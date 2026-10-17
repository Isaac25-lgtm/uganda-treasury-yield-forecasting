"""Immutable raw documents -> event registry, tenor panel, identity audit, pre-bid ITT table.

Outputs (written under ``data/processed/``, git-ignored; small aggregate copies are
written to ``results/tables/`` by scripts/run_pipeline.py):

- ``results_registry.csv``: one row per parsed results document (status, printed keys)
- ``tenor_panel.csv``: one row per (auction_date, tenor) with printed and repaired values
- ``itt_registry.csv``: one row per Invitation to Tender with pre-bid fields and timing
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from .parse_itt import parse_itt
from .parse_results import mmy_from_price, parse_results_file, repair_double_dot
from .pdftext import extract_text

IDENTITY_TOL_PP = 0.02
KNOWN_AMBIGUOUS_EVENTS = {"1176"}
MAX_PLAUSIBLE_LEAD_DAYS = 14  # notices are normally dated 6 days ahead; longer leads are date typos  # investigator-documented price/yield ambiguity (AGENTS.md J)


def load_manifest(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def build_results(manifest: pd.DataFrame, raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    docs, rows = [], []
    for _, m in manifest[manifest["category"] == "Auction results"].iterrows():
        if not m["local_file"]:
            docs.append({"local_file": "", "source_url": m["source_url"], "status": "download_failed"})
            continue
        r = parse_results_file(raw_dir / m["local_file"])
        docs.append({
            "local_file": m["local_file"], "source_url": m["source_url"], "sha256": m["sha256"],
            "status": r["status"], "printed_auction_no": r.get("auction_no"),
            "auction_date": r.get("auction_date"), "settlement_date": r.get("settlement_date"),
            "printed_release_date": r.get("printed_release_date"),
            "pdf_creation_date": r.get("pdf_creation_date"),
            "n_tenors": len(r.get("tenors", {})),
        })
        for t, rec in r.get("tenors", {}).items():
            rows.append({"auction_date": r["auction_date"], "settlement_date": r["settlement_date"],
                         "printed_auction_no": r["auction_no"], "tenor": t, "source_file": m["local_file"],
                         "sha256": m["sha256"], **rec})
    return pd.DataFrame(docs), pd.DataFrame(rows)


def audit_identity(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel.copy()
    sd = pd.to_datetime(p["settlement_date"])
    md = pd.to_datetime(p["maturity_date"])
    p["days_actual"] = (md - sd).dt.days
    p["mmy_implied_nominal"] = [mmy_from_price(pr, t) if pr == pr else np.nan
                                for pr, t in zip(p["cutoff_price"], p["tenor"])]
    p["mmy_implied_actual"] = [mmy_from_price(pr, d) if pr == pr and d == d and d > 0 else np.nan
                               for pr, d in zip(p["cutoff_price"], p["days_actual"])]
    p["mmy_repaired"] = [repair_double_dot(s) if f == "unparseable" else v
                         for s, v, f in zip(p["mmy_raw"], p["mmy"], p["parse_flag"])]
    # Primary convention (matches the printed yield in the large majority of rows):
    # money-market yield = (100/P - 1) * 365 / nominal tenor days.
    p["identity_gap_pp"] = (p["mmy_repaired"] - p["mmy_implied_nominal"]).abs()
    p["identity_gap_actual_pp"] = (p["mmy_repaired"] - p["mmy_implied_actual"]).abs()
    p["identity_ok"] = p["identity_gap_pp"] <= IDENTITY_TOL_PP
    p["identity_ok_actual_days"] = p["identity_gap_actual_pp"] <= IDENTITY_TOL_PP
    p["tenor_consistent"] = (p["days_actual"] - p["tenor"]).abs() <= 3
    return p


def dedupe_events(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One row per (auction_date, tenor). Duplicate listings must agree exactly; conflicts are reported."""
    keys = ["auction_date", "tenor"]
    conflicts = []
    keep = []
    for k, g in panel.groupby(keys, dropna=False):
        if len(g) > 1:
            vals = g[["cutoff_price_raw", "mmy_raw"]].astype(str).drop_duplicates()
            if len(vals) > 1:
                conflicts.append({"auction_date": k[0], "tenor": k[1], "n_docs": len(g),
                                  "files": ";".join(g["source_file"])})
        keep.append(g.iloc[0])
    return pd.DataFrame(keep).reset_index(drop=True), pd.DataFrame(conflicts)


def build_itt(manifest: pd.DataFrame, raw_dir: Path) -> pd.DataFrame:
    rows = []
    for _, m in manifest[manifest["category"] == "Invitation to tender"].iterrows():
        if not m["local_file"]:
            continue
        r = parse_itt(extract_text(raw_dir / m["local_file"]))
        rows.append({"local_file": m["local_file"], "source_url": m["source_url"], "sha256": m["sha256"], **r})
    return classify_notice_timing(pd.DataFrame(rows))


def classify_notice_timing(itt: pd.DataFrame) -> pd.DataFrame:
    """Pre-bid status of each ITT from its printed notice date vs its auction date."""
    itt = itt.copy()
    ad, nd = pd.to_datetime(itt["auction_date"]), pd.to_datetime(itt["notice_date"])
    itt["notice_lead_days"] = (ad - nd).dt.days
    itt["timing_status"] = np.select(
        [itt["auction_date"].isna() & itt["issue_no"].isna(), itt["auction_date"].isna(), itt["notice_date"].isna(),
         itt["notice_lead_days"] <= 0, itt["notice_lead_days"] > MAX_PLAUSIBLE_LEAD_DAYS],
        ["no_text_layer", "auction_date_unparsed", "notice_date_not_printed", "TIMING_VIOLATION",
         "implausible_lead_unverified"],
        default="pre_bid_verified")
    return itt


def assemble_panel(audited: pd.DataFrame, itt: pd.DataFrame, sensitivity: str = "as_printed",
                   require_verified_notice: bool = False) -> pd.DataFrame:
    """Target panel for one declared sensitivity; offers joined from the ITT of the same auction date."""
    p = audited.copy()
    p["issue_key"] = p["printed_auction_no"].astype("Int64").astype(str)
    if sensitivity == "as_printed":
        p["y"] = p["mmy"]
    elif sensitivity == "repaired_typo":
        p["y"] = p["mmy_repaired"]
    elif sensitivity == "drop_1176":
        p["y"] = p["mmy_repaired"]
        p.loc[p["issue_key"].isin(KNOWN_AMBIGUOUS_EVENTS), "y"] = np.nan
    elif sensitivity == "drop_identity_flags":
        p["y"] = p["mmy_repaired"].where(p["identity_ok"])
    else:
        raise ValueError(sensitivity)
    p = p[p["parse_flag"] != "not_awarded"] if sensitivity != "as_printed" else p
    it = itt.dropna(subset=["auction_date"]).sort_values("timing_status", key=lambda s: s != "pre_bid_verified")
    it = it.drop_duplicates("auction_date").copy()
    # Only offers from notices with a verified pre-auction date are usable as pre-bid predictors
    # (notices without a printed date are accepted only if require_verified_notice=False).
    usable = it["timing_status"].eq("pre_bid_verified") | (
        (not require_verified_notice) & it["timing_status"].eq("notice_date_not_printed"))
    for c in ("offer_91", "offer_182", "offer_364", "offer_total"):
        it.loc[~usable, c] = np.nan
    long = it.melt(id_vars=["auction_date", "issue_no", "offer_total", "notice_date", "timing_status"],
                   value_vars=["offer_91", "offer_182", "offer_364"], var_name="tv", value_name="offer_tenor")
    long["tenor"] = long["tv"].str.replace("offer_", "").astype(int)
    long["auction_date"] = pd.to_datetime(long["auction_date"])
    p["auction_date"] = pd.to_datetime(p["auction_date"])
    out = p.merge(long.drop(columns="tv").rename(columns={"issue_no": "itt_issue_no"}),
                  on=["auction_date", "tenor"], how="left")
    # derive missing totals from per-tenor offers (all three printed)
    tot = out.groupby("auction_date")["offer_tenor"].transform(lambda s: s.sum(min_count=3))
    out["offer_total"] = out["offer_total"].fillna(tot)
    return out


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)
