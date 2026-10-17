"""R04 research dashboard (Streamlit) — reads only precomputed public aggregate tables.

    streamlit run dashboard/app.py

No model is trained here and no raw document is read. Not financial advice.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / name)


def run_info() -> dict:
    p = ROOT / "results" / "run_summary.json"
    return json.loads(p.read_text()) if p.exists() else {}


def main() -> None:
    st.set_page_config(page_title="R04 Uganda T-bill pre-bid forecasts", layout="wide")
    info = run_info()
    st.info(
        f"**Stage:** research phase 1 (bounded rescue) · **Data cutoff:** last parsed auction 2026-09-30 · "
        f"**Data:** observed official BoU documents (no simulated values) · "
        f"**Decision:** {info.get('decision', 'n/a')} · **Run:** {info.get('experiment_id', 'n/a')} "
        f"@ `{info.get('code_commit_at_run', 'n/a')[:10]}` · Not investment advice; no returns are implied."
    )
    page = st.sidebar.radio("Section", ["Overview", "Data provenance", "Study cohort", "Baselines and models",
                                        "Validation", "Sensitivity / limitations", "Reproducibility"])
    metrics = load("forward_metrics_all_sensitivities.csv")
    prim = metrics[metrics["sensitivity"] == info.get("primary_sensitivity", "repaired_typo")]

    if page == "Overview":
        st.title("Do pre-bid signals beat the last observed auction yield?")
        st.write("Target: Bank of Uganda T-bill **cut-off money-market yield** (% p.a., 365/nominal-day basis) "
                 "for 91/182/364-day tenors, forecast before the 10:00 bid deadline. Unit: auction event "
                 "(tenors grouped).")
        base = prim.set_index("model").loc["last_yield"]
        c = st.columns(3)
        c[0].metric("Last-yield MAE (pp)", f"{base['MAE_pp']:.3f}")
        c[1].metric("Test auctions", int(base["n_test_auctions"]))
        c[2].metric("Test tenor-rows", int(base["n_test_rows"]))
        st.dataframe(prim[["model", "MAE_pp", "RMSE_pp", "MAE_change_vs_last_pct", "ci95_lo", "ci95_hi"]]
                     .round(4), hide_index=True)
        st.warning("No pre-bid model beat the last observed yield; the branch stops with NEGATIVE_MODEL. "
                   "Macro predictors (CBR, CPI, FX) remain HOLD_DATA: dated release chronology was not obtained.")
    elif page == "Data provenance":
        st.header("Official source documents")
        docs = load("results_document_status.csv")
        st.write(docs["status"].value_counts().rename("documents"))
        st.dataframe(docs, hide_index=True)
        st.subheader("Source anomalies (preserved, not silently fixed)")
        st.dataframe(load("source_anomalies.csv"), hide_index=True)
    elif page == "Study cohort":
        st.header("Inclusion flow by sensitivity")
        st.dataframe(load("inclusion_flow.csv"), hide_index=True)
        st.header("Pre-bid Invitation-to-Tender timing audit")
        itt = load("prebid_itt_timing_audit.csv")
        st.write(itt["timing_status"].value_counts().rename("notices"))
        st.dataframe(itt, hide_index=True)
    elif page == "Baselines and models":
        st.header("Historical cut-off yields and one-step forecasts (test period)")
        fc = load("forecasts_primary.csv")
        tenor = st.selectbox("Tenor (days)", sorted(fc["tenor"].unique()))
        models = st.multiselect("Models", [c for c in fc.columns if c not in ("auction_date", "tenor", "y")],
                                default=["last_yield", "hgb_prebid"])
        sub = fc[fc["tenor"] == tenor].set_index(pd.to_datetime(fc.loc[fc["tenor"] == tenor, "auction_date"]))
        st.line_chart(sub[["y"] + models].rename(columns={"y": "observed cut-off yield"}))
        st.caption("Gaps (e.g. Dec-2025 to Sep-2026) are auctions whose official results table has no text layer; "
                   "they are missing, not zero.")
        st.dataframe(load("mae_by_tenor_primary.csv").round(4), hide_index=True)
    elif page == "Validation":
        st.header("Forward auction-grouped validation")
        st.write("Expanding window, refit before each test auction (first test on/after 2024-01-01). "
                 "Loss differential = per-auction mean(|e_model| - |e_last|); 95% moving-block bootstrap CI "
                 "(block 4 auctions, 2000 replicates). Negative = better than last yield.")
        d = prim[prim["model"] != "last_yield"][["model", "mean_auction_loss_diff_pp", "ci95_lo", "ci95_hi"]]
        st.dataframe(d.round(4), hide_index=True)
        st.bar_chart(d.set_index("model")["mean_auction_loss_diff_pp"])
        st.dataframe(load("model_registry_primary.csv"), hide_index=True)
    elif page == "Sensitivity / limitations":
        st.header("Source-repair sensitivities")
        st.dataframe(metrics[["sensitivity", "model", "n_test_auctions", "MAE_pp", "MAE_change_vs_last_pct",
                              "ci95_lo", "ci95_hi"]].round(4), hide_index=True)
        st.markdown((ROOT / "docs" / "LIMITATIONS.md").read_text())
    else:
        st.header("Reproducibility")
        st.markdown((ROOT / "docs" / "REPRODUCIBILITY.md").read_text())


if __name__ == "__main__":
    main()
