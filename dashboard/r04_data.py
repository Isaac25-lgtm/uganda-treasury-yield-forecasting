"""Data layer for the R04 dashboard: reads ONLY committed aggregate tables under results/.

Never downloads sources, parses BoU documents or trains models. Every derived frame is computed from
published auction statistics (printed cut-off yields, offered amounts) and this project's own forecasts.
No individual bids, bidder identities or participant data exist anywhere in these tables.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("R04_RESULTS_DIR", ROOT / "results"))
TABLES = RESULTS / "tables"

MODEL_ORDER = ["last_yield", "ar1", "ridge_prebid", "ridge_lag_only", "hgb_prebid"]
MODEL_LABELS = {
    "last_yield": "Last observed yield (benchmark)",
    "ar1": "AR(1) per tenor",
    "ridge_prebid": "Ridge: lags + pre-bid ITT offers",
    "ridge_lag_only": "Ridge: lags only (ablation)",
    "hgb_prebid": "Gradient boosting: lags + pre-bid offers",
}
SENSITIVITY_LABELS = {
    "as_printed": "As printed (unparseable values left missing)",
    "repaired_typo": "Primary: 13..001 typo repaired via price identity",
    "drop_1176": "Exclude auction 1176 (day-count ambiguity)",
    "drop_identity_flags": "Exclude all identity-failing rows",
}
TENORS = (91, 182, 364)

# Allowlist of aggregate tables that may be offered for download (no raw PDFs/DOCX, no row-level bids).
DOWNLOADABLE_TABLES = {
    "forward_metrics_all_sensitivities.csv": "MAE/RMSE and block-bootstrap CIs, all models x 4 sensitivities",
    "mae_by_tenor_primary.csv": "MAE by tenor, primary analysis",
    "forecasts_primary.csv": "Observed cut-off yields and the five one-step forecasts, 45 test auctions",
    "inclusion_flow.csv": "Rows and auctions retained at each step",
    "event_registry_tenor_rows.csv": "Printed cut-off price/yield per auction and tenor with identity audit",
    "source_anomalies.csv": "Preserved source anomalies",
    "prebid_itt_timing_audit.csv": "Invitation-to-Tender notice timing audit",
    "results_document_status.csv": "Parse status of each official results release",
    "model_registry_primary.csv": "Per-refit training sizes and ridge alphas",
}
FORBIDDEN_DOWNLOAD_COLUMNS = ("path", "secret", "token", "bidder", "participant")


class MissingResultsError(FileNotFoundError):
    """A committed aggregate table needed by the dashboard is missing or empty."""


def load_table(name: str, tables: Path = TABLES) -> pd.DataFrame:
    p = Path(tables) / name
    if not p.exists():
        raise MissingResultsError(f"required aggregate table missing: results/tables/{name}; "
                                  "run scripts/run_pipeline.py offline (the dashboard never recomputes it)")
    df = pd.read_csv(p)
    if df.empty:
        raise MissingResultsError(f"aggregate table is empty: results/tables/{name}")
    return df


def run_summary(results: Path = RESULTS) -> dict:
    p = Path(results) / "run_summary.json"
    if not p.exists():
        raise MissingResultsError("results/run_summary.json missing")
    return json.loads(p.read_text())


def reproduction_record(results: Path = RESULTS) -> dict | None:
    p = Path(results) / "reproduction" / "reproduction_record.json"
    return json.loads(p.read_text()) if p.exists() else None


def forecasts_long(fc: pd.DataFrame) -> pd.DataFrame:
    """Wide committed forecasts -> long (auction_date, tenor, model, observed, predicted, error)."""
    long = fc.melt(id_vars=["auction_date", "tenor", "y"], value_vars=[m for m in MODEL_ORDER if m in fc.columns],
                   var_name="model", value_name="predicted")
    long = long.rename(columns={"y": "observed"})
    long["auction_date"] = pd.to_datetime(long["auction_date"])
    long["error"] = long["predicted"] - long["observed"]
    long["abs_error"] = long["error"].abs()
    long["sq_error"] = long["error"] ** 2
    long["model_label"] = long["model"].map(MODEL_LABELS)
    return long


def add_gap_segments(df: pd.DataFrame, date_col: str = "auction_date", by: tuple = ("tenor",),
                     max_gap_days: int = 21) -> pd.DataFrame:
    """Segment id that increments whenever consecutive dated rows are > max_gap_days apart.

    Auctions are fortnightly; a longer gap means unparsed/missing auctions in between, so plotted lines
    must break there instead of implying interpolated observations.
    """
    out = df.sort_values(list(by) + [date_col]).copy()
    gaps = out.groupby(list(by))[date_col].diff().dt.days.gt(max_gap_days)
    out["segment"] = gaps.astype(int).groupby([out[c] for c in by]).cumsum()
    return out


def recompute_metrics(fc: pd.DataFrame) -> pd.DataFrame:
    """MAE/RMSE per model recomputed from the committed forecast table (consistency check)."""
    lg = forecasts_long(fc)
    g = lg.groupby("model")
    out = pd.DataFrame({"MAE_pp": g["abs_error"].mean(), "RMSE_pp": np.sqrt(g["sq_error"].mean()),
                        "n_test_rows": g.size(), "n_test_auctions": g["auction_date"].nunique()})
    return out.reindex([m for m in MODEL_ORDER if m in out.index])


def per_auction_loss_differences(fc: pd.DataFrame) -> pd.DataFrame:
    """Per auction: mean over tenors of |e_model| - |e_last_yield| (pp). Negative = better than last yield."""
    lg = forecasts_long(fc)
    per = lg.groupby(["auction_date", "model"])["abs_error"].mean().unstack("model")
    diff = per.sub(per["last_yield"], axis=0).drop(columns="last_yield")
    out = diff.reset_index().melt(id_vars="auction_date", var_name="model", value_name="loss_diff_pp")
    n_ten = lg[lg["model"] == "last_yield"].groupby("auction_date").size().rename("n_tenors")
    out = out.merge(n_ten.reset_index(), on="auction_date")
    out["model_label"] = out["model"].map(MODEL_LABELS)
    return out.sort_values(["model", "auction_date"]).reset_index(drop=True)


def observed_series(registry: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    """Observed cut-off yields (primary values) with explicit gaps.

    Missing auctions get a row with yield NaN so lines BREAK there; nothing is interpolated or zero-filled.
    ``segment`` increments after every missing/unparsed auction so each drawn line only joins consecutive
    observed auctions.
    """
    r = registry.copy()
    r["auction_date"] = pd.to_datetime(r["auction_date"])
    r["observed_yield"] = r["mmy_repaired"]
    r["flag"] = np.select(
        [r["parse_flag"].eq("not_awarded"), r["parse_flag"].eq("unparseable"), ~r["identity_ok"].fillna(True).astype(bool)],
        ["not awarded (printed N/A)", "printed typo repaired (13..001 -> 13.001)",
         "price/yield identity anomaly (auction 1176 day-count)"], default="")
    keep = ~coverage["results_status"].str.startswith(("scheduled after", "rescheduled"))
    cal = coverage.loc[keep,
                       ["auction_date", "results_status"]].copy()
    cal["auction_date"] = pd.to_datetime(cal["auction_date"])
    rows = []
    for t in TENORS:
        sub = r[r["tenor"] == t].set_index("auction_date")
        for _, c in cal.sort_values("auction_date").iterrows():
            d = c["auction_date"]
            if d in sub.index:
                s = sub.loc[d]
                rows.append({"auction_date": d, "tenor": t, "observed_yield": s["observed_yield"],
                             "printed_yield_raw": s["mmy_raw"], "cutoff_price_raw": s["cutoff_price_raw"],
                             "flag": s["flag"], "results_status": "parsed"})
            else:
                rows.append({"auction_date": d, "tenor": t, "observed_yield": np.nan, "printed_yield_raw": None,
                             "cutoff_price_raw": None, "flag": "", "results_status": c["results_status"]})
    o = pd.DataFrame(rows)
    o["segment"] = 0
    for t in TENORS:
        m = o["tenor"] == t
        o.loc[m, "segment"] = o.loc[m, "observed_yield"].isna().cumsum().to_numpy()
    o["tenor_label"] = o["tenor"].astype(str) + "-day"
    return o


def auction_coverage(registry: pd.DataFrame, itt: pd.DataFrame, docs: pd.DataFrame,
                     forecasts: pd.DataFrame) -> pd.DataFrame:
    """Scheduled-auction calendar (union of ITT and results dates) with parse and test-set status."""
    reg = registry.copy()
    reg["auction_date"] = pd.to_datetime(reg["auction_date"])
    dates = set(reg["auction_date"].dropna())
    it = itt.dropna(subset=["auction_date"]).copy()
    it["auction_date"] = pd.to_datetime(it["auction_date"])
    dates |= set(it["auction_date"])
    dd = docs.dropna(subset=["auction_date"]).copy()
    dd["auction_date"] = pd.to_datetime(dd["auction_date"])
    dates |= set(dd["auction_date"])
    cal = pd.DataFrame({"auction_date": sorted(dates)})
    n_y = reg.dropna(subset=["mmy_repaired"]).groupby("auction_date").size().rename("tenors_with_yield")
    cal = cal.merge(n_y.reset_index(), on="auction_date", how="left")
    cal["tenors_with_yield"] = cal["tenors_with_yield"].fillna(0).astype(int)
    st = dd.drop_duplicates("auction_date").set_index("auction_date")["status"]
    cutoff = reg.dropna(subset=["mmy_repaired"])["auction_date"].max()
    cal["results_status"] = np.where(cal["tenors_with_yield"] > 0, "parsed",
                                     cal["auction_date"].map(st).fillna("no T-bill results table in catalogue"))
    parsed = cal.loc[cal["tenors_with_yield"] > 0, "auction_date"]
    for i, r in cal[cal["tenors_with_yield"] == 0].iterrows():
        near = parsed[(parsed - r["auction_date"]).abs() <= pd.Timedelta(days=3)]
        if len(near):  # ITT-scheduled date whose results are printed on a nearby date (e.g. 1176: 10 -> 11 Apr 2024)
            cal.loc[i, "results_status"] = f"rescheduled: results dated {near.iloc[0].date()}"
    cal.loc[cal["auction_date"] > cutoff, "results_status"] = "scheduled after data cutoff"
    its = it.sort_values("timing_status", key=lambda s: s != "pre_bid_verified").drop_duplicates("auction_date")
    cal["itt_timing_status"] = cal["auction_date"].map(its.set_index("auction_date")["timing_status"]).fillna(
        "no ITT parsed")
    test_dates = set(pd.to_datetime(forecasts["auction_date"]))
    cal["in_primary_test_set"] = cal["auction_date"].isin(test_dates)
    return cal


def safe_download_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Guard: refuse to offer frames whose columns look like paths, secrets or participant data."""
    bad = [c for c in df.columns if any(s in str(c).lower() for s in FORBIDDEN_DOWNLOAD_COLUMNS)]
    if bad:
        raise ValueError(f"column(s) not allowed in public downloads: {bad}")
    for c in [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]:
        if df[c].astype(str).str.contains(r"(?:^|\s)(?:/home/|/tmp/|[A-Za-z]:\\)", regex=True).any():
            raise ValueError(f"local path found in column {c}")
    return df
