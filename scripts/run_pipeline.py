"""End-to-end R04 phase-1 pipeline on already-downloaded official documents.

    PYTHONPATH=src python3 -I scripts/run_pipeline.py

Reads raw files from data/raw/bou/docs (git-ignored; fetch with ``python -m ugtbill.acquire``),
writes row-level intermediates to data/processed/ (git-ignored) and small public-safe
aggregate tables to results/tables/.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from ugtbill.evaluate import decision, forward_evaluate, summarise  # noqa: E402
from ugtbill.features import build_features  # noqa: E402
from ugtbill.preprocess import (assemble_panel, audit_identity, build_itt, build_results,  # noqa: E402
                                dedupe_events, load_manifest, verify_raw_inputs, write_csv)

FIRST_TEST = "2024-01-01"
SENSITIVITIES = ["as_printed", "repaired_typo", "drop_1176", "drop_identity_flags"]
PRIMARY = "repaired_typo"  # declared primary analysis set; as_printed reported alongside


def main(argv: list[str] | None = None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results",
                    help="where tables/ and run_summary.json are written (default: committed results/)")
    ap.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/bou/docs")
    a = ap.parse_args(argv)
    t0 = datetime.now(timezone.utc)
    raw = a.raw_dir
    proc = ROOT / "data/processed"
    tables = a.out_dir / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(ROOT / "data/manifests/bou_tbill_documents.csv")
    verify_raw_inputs(manifest, raw)  # fails clearly if any raw document is missing or altered

    docs, rows = build_results(manifest, raw)
    audited = audit_identity(rows)
    panel, conflicts = dedupe_events(audited)
    itt = build_itt(manifest, raw)
    write_csv(docs, proc / "results_registry.csv")
    write_csv(panel, proc / "tenor_panel_audited.csv")
    write_csv(itt, proc / "itt_registry.csv")

    # ---- public-safe audit tables (published official aggregates; no restricted data) ----
    reg_cols = ["auction_date", "printed_auction_no", "tenor", "maturity_date", "cutoff_price_raw", "mmy_raw",
                "mmy", "mmy_repaired", "mmy_implied_nominal", "identity_gap_pp", "identity_gap_actual_pp",
                "identity_ok", "days_actual", "tenor_consistent", "parse_flag", "source_file", "sha256"]
    ev = panel[reg_cols].sort_values(["auction_date", "tenor"])
    write_csv(ev, tables / "event_registry_tenor_rows.csv")
    flags = ev[(~ev["identity_ok"].fillna(False).astype(bool)) | (ev["parse_flag"] != "ok")
               | (~ev["tenor_consistent"].fillna(True).astype(bool) & ev["days_actual"].notna())]
    write_csv(flags, tables / "source_anomalies.csv")
    write_csv(docs.drop(columns=["sha256"]), tables / "results_document_status.csv")
    write_csv(itt[["auction_date", "issue_no", "notice_date", "notice_lead_days", "timing_status", "offer_91",
                   "offer_182", "offer_364", "offer_total", "bid_deadline", "local_file"]].sort_values("auction_date"),
              tables / "prebid_itt_timing_audit.csv")

    # ---- frozen forward evaluation for each declared sensitivity ----
    all_summ, flow = [], []
    for sens in SENSITIVITIES:
        pan = assemble_panel(panel, itt, sens)
        feat = build_features(pan)
        pr, reg = forward_evaluate(feat, FIRST_TEST)
        summ = summarise(pr)
        summ.insert(0, "sensitivity", sens)
        summ["decision_if_timing_verified"] = decision(summ, timing_verified=True)
        all_summ.append(summ)
        write_csv(pr, proc / f"predictions_{sens}.csv")
        if sens == PRIMARY:
            write_csv(reg, tables / "model_registry_primary.csv")
            per = pr.groupby(["model", "tenor"])["abs_err"].agg(["mean", "count"]).reset_index()
            per.columns = ["model", "tenor", "MAE_pp", "n_test_rows"]
            write_csv(per, tables / "mae_by_tenor_primary.csv")
            ts = pr.pivot_table(index=["auction_date", "tenor", "y"], columns="model", values="yhat").reset_index()
            write_csv(ts, tables / "forecasts_primary.csv")
        flow.append({"sensitivity": sens, "tenor_rows_parsed": len(panel), "events_parsed": panel["auction_date"].nunique(),
                     "rows_with_target": int(pan["y"].notna().sum()),
                     "rows_with_prebid_offer": int(pan["offer_tenor"].notna().sum()),
                     "rows_complete_features": int(feat.dropna(subset=["y", "y_lag1", "dy_lag2", "offer_change_vs_prev"]).shape[0]),
                     "test_events": int(pr["auction_date"].nunique()) if len(pr) else 0,
                     "test_rows_per_model": int(len(pr) / pr["model"].nunique()) if len(pr) else 0})
    summary = pd.concat(all_summ, ignore_index=True)
    write_csv(summary.round(5), tables / "forward_metrics_all_sensitivities.csv")
    write_csv(pd.DataFrame(flow), tables / "inclusion_flow.csv")

    # Timing verdict: CBR / CPI / FX release chronology was NOT obtained (see docs/DATA_ACCESS.md);
    # the only pre-bid features used are ITT offers with verified notice dates.
    prim = summary[summary["sensitivity"] == PRIMARY]
    final = decision(prim, timing_verified=True)
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    run = {"experiment_id": "r04_prebid_rescue_v1", "run_started_utc": t0.isoformat(timespec="seconds"),
           "code_commit_at_run": git, "first_test": FIRST_TEST, "primary_sensitivity": PRIMARY,
           "decision": final, "macro_features": "HOLD_DATA (CBR/CPI/FX release chronology not obtained)",
           "documents_parsed_ok": int((docs["status"] == "ok").sum()),
           "documents_no_text_layer": int((docs["status"] == "no_text_layer").sum()),
           "identity_conflicting_duplicates": int(len(conflicts))}
    run["run_finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (a.out_dir / "run_summary.json").write_text(json.dumps(run, indent=2) + "\n")
    print(pd.DataFrame(flow).to_string(index=False))
    print(summary.round(4).to_string(index=False))
    print(json.dumps(run, indent=2))


if __name__ == "__main__":
    main()
