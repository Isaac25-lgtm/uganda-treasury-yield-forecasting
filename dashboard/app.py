"""R04 research dashboard (Streamlit): pre-bid forecasting of Uganda T-bill auction cut-off yields.

    streamlit run dashboard/app.py

Reads only committed aggregate tables in results/ (see dashboard/r04_data.py). It never downloads sources,
parses BoU documents or trains a model. Research presentation only: no trading, return or investment advice.
"""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import r04_data as d

ROOT = Path(__file__).resolve().parents[1]

# Validated categorical slots (dataviz reference palette, light surface #fcfcfb). Models: slots 1-5 in fixed
# order. Tenors: slots 6-8, always paired with distinct point shapes (CVD secondary encoding).
MODEL_COLORS = {"last_yield": "#2a78d6", "ar1": "#eb6834", "ridge_prebid": "#1baf7a",
                "ridge_lag_only": "#eda100", "hgb_prebid": "#e87ba4"}
TENOR_COLORS = {"91-day": "#008300", "182-day": "#6250d6", "364-day": "#e34948"}
TENOR_SHAPES = {"91-day": "circle", "182-day": "square", "364-day": "triangle-up"}
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e7e6e2"
UNIT = "percentage points (pp)"


def model_scale(models):
    return alt.Scale(domain=[d.MODEL_LABELS[m] for m in models], range=[MODEL_COLORS[m] for m in models])


def tenor_color(tenors):
    return alt.Scale(domain=list(tenors), range=[TENOR_COLORS[t] for t in tenors])


def tenor_shape(tenors):
    return alt.Scale(domain=list(tenors), range=[TENOR_SHAPES[t] for t in tenors])


def style(chart: alt.Chart) -> alt.Chart:
    return (chart.configure_axis(gridColor=GRID, domainColor=INK_2, tickColor=INK_2, labelColor=INK_2,
                                 titleColor=INK, labelFontSize=12, titleFontSize=12, labelLimit=320)
            .configure_legend(labelColor=INK, titleColor=INK, labelFontSize=12, orient="bottom", columns=2,
                              labelLimit=360)
            .configure_header(labelColor=INK, labelFontSize=12, labelLimit=360)
            .configure_view(strokeWidth=0))


def show(chart, key: str) -> None:
    st.altair_chart(style(chart), width="stretch", key=key)


def table_and_download(df: pd.DataFrame, label: str, file_name: str, key: str) -> None:
    """Table view (accessibility relief) + allowlisted aggregate CSV download."""
    safe = d.safe_download_frame(df)
    with st.expander(f"Table view and CSV — {label}"):
        st.dataframe(safe, hide_index=True)
        st.download_button(f"Download {file_name}", safe.to_csv(index=False).encode(), file_name=file_name,
                           mime="text/csv", key=f"dl_{key}")


@st.cache_data
def load_all():
    t = {n: d.load_table(n) for n in d.DOWNLOADABLE_TABLES}
    cov = d.auction_coverage(t["event_registry_tenor_rows.csv"], t["prebid_itt_timing_audit.csv"],
                             t["results_document_status.csv"], t["forecasts_primary.csv"])
    obs = d.observed_series(t["event_registry_tenor_rows.csv"], cov)
    fl = d.forecasts_long(t["forecasts_primary.csv"])
    loss = d.per_auction_loss_differences(t["forecasts_primary.csv"])
    rec = d.recompute_metrics(t["forecasts_primary.csv"])
    return t, cov, obs, fl, loss, rec


def ribbon(info: dict, repro: dict | None, cutoff: str) -> None:
    rep = (f"reproduced exactly at <code>{repro['code_commit'][:7]}</code> (239/239 checksum-valid documents)"
           if repro else "not independently reproduced")
    st.markdown(
        f"""<div role="note" style="border:1px solid {GRID};border-left:6px solid {INK};padding:10px 14px;
border-radius:6px;background:#f6f5f2;color:{INK};font-size:0.92rem;line-height:1.5">
<b>Decision: NEGATIVE_MODEL</b> (no pre-bid model beats the last observed yield) · macro predictors <b>HOLD_DATA</b>
· <b>Run</b> {info.get('experiment_id')} at code <code>{info.get('code_commit_at_run', '')[:7]}</code>, {rep}
· <b>Data cutoff</b>: last parsed auction {cutoff}
· <b>Observed</b> official Bank of Uganda published auction statistics — <b>not simulated</b>
· Published aggregates only: no confidential bids, bidder identities or participant records
· Research presentation, <b>not investment advice</b>; no trading or return claims.</div>""",
        unsafe_allow_html=True)


# ----------------------------------------------------------------------------------------------- sections
def page_overview(t, rec):
    st.title("Do pre-bid signals beat the last observed Uganda T-bill auction yield?")
    st.markdown(
        "**Target:** the Bank of Uganda (BoU) Treasury-bill **cut-off money-market yield** for 91-, 182- and 364-day "
        "tenors, as printed in official results releases, % per year on a 365/nominal-day basis. "
        "**Forecast origin:** before the 10:00 bid deadline of each auction. "
        "**Unit:** the auction; all tenors of one auction are evaluated and resampled together.")
    m = t["forward_metrics_all_sensitivities.csv"]
    prim = m[m["sensitivity"] == "repaired_typo"].set_index("model").reindex(d.MODEL_ORDER)
    c = st.columns(4)
    c[0].metric("Benchmark MAE (last yield)", f"{prim.loc['last_yield', 'MAE_pp']:.3f} pp")
    c[1].metric("Best challenger MAE (AR(1))", f"{prim.loc['ar1', 'MAE_pp']:.3f} pp",
                delta=f"{prim.loc['ar1', 'MAE_change_vs_last_pct']:+.1f}% vs benchmark", delta_color="inverse")
    c[2].metric("Forward test auctions", int(prim.loc["last_yield", "n_test_auctions"]))
    c[3].metric("Test tenor-rows", int(prim.loc["last_yield", "n_test_rows"]))
    df = prim.reset_index()[["model", "MAE_pp", "RMSE_pp", "MAE_change_vs_last_pct", "ci95_lo", "ci95_hi"]]
    df["model_label"] = df["model"].map(d.MODEL_LABELS)
    st.subheader("Mean absolute error, primary analysis (45 auctions, 132 tenor-rows)")
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=4, height=18).encode(
        x=alt.X("MAE_pp:Q", title=f"MAE ({UNIT}); lower is better", scale=alt.Scale(zero=True)),
        y=alt.Y("model_label:N", sort=[d.MODEL_LABELS[x] for x in d.MODEL_ORDER], title=None),
        color=alt.Color("model_label:N", scale=model_scale(d.MODEL_ORDER), legend=None),
        tooltip=[alt.Tooltip("model_label:N", title="Model"), alt.Tooltip("MAE_pp:Q", title="MAE (pp)", format=".4f"),
                 alt.Tooltip("RMSE_pp:Q", title="RMSE (pp)", format=".4f"),
                 alt.Tooltip("MAE_change_vs_last_pct:Q", title="vs last yield (%)", format="+.1f")])
    labels = bars.mark_text(align="left", dx=4, color=INK).encode(text=alt.Text("MAE_pp:Q", format=".3f"),
                                                                  color=alt.value(INK))
    base_rule = alt.Chart(df[df["model"] == "last_yield"]).mark_rule(strokeDash=[4, 3], color=INK).encode(x="MAE_pp:Q")
    show((bars + labels + base_rule).properties(height=210), "overview_mae")
    table_and_download(df.drop(columns="model_label"), "MAE comparison", "r04_mae_primary.csv", "ov")
    st.warning("All four challengers have higher MAE than the last observed yield. For the two ridge models the "
               "95% block-bootstrap CI of the per-auction loss difference lies entirely above zero (reliably worse); "
               "for AR(1) and gradient boosting it spans zero. No prespecified GO criterion was met, so the branch "
               "stopped (no further algorithm search).")
    with st.expander("What these numbers are — and are not"):
        st.markdown(
            "- Values are **published auction statistics** (printed cut-off prices/yields and offered amounts) and "
            "this project's own forecasts. The BoU does not publish individual bids, and none are used here.\n"
            "- The tested *pre-bid* information is limited to the auction's Invitation-to-Tender offered amounts plus "
            "earlier auction results. CBR, CPI and FX were **not** tested: dated release histories were not obtained.\n"
            "- Earlier handoff figures (0.34374 vs 0.47691) were **not reproduced on identical inputs**; this rebuild "
            "agrees qualitatively.\n- Recomputed from the committed forecast table: "
            + ", ".join(f"{m} MAE {rec.loc[m, 'MAE_pp']:.5f}" for m in rec.index))


def page_provenance(t):
    st.header("Data provenance")
    st.markdown(
        "**Source:** Bank of Uganda website, *Auction information* (official T-bill **results press releases** and "
        "**Invitations to Tender**), listed through the site's public CMS endpoint and fetched 17 October 2026. "
        "239/239 documents (119 results, 120 ITTs; 33,812,254 bytes) are identified by SHA-256 in "
        "`data/manifests/bou_tbill_documents.csv`. Raw PDF/DOCX files are **not** redistributed here.\n\n"
        "*Attribution:* auction statistics © Bank of Uganda, reproduced from its public releases for research "
        "commentary. BoU does not endorse this analysis; derived forecasts and metrics are the project's own.")
    docs = t["results_document_status.csv"]
    counts = docs["status"].value_counts().rename_axis("status").reset_index(name="documents")
    ch = alt.Chart(counts).mark_bar(cornerRadiusEnd=4, height=18, color="#2a78d6").encode(
        x=alt.X("documents:Q", title="Results documents (count)"), y=alt.Y("status:N", sort="-x", title=None),
        tooltip=["status:N", "documents:Q"])
    show((ch + ch.mark_text(align="left", dx=4, color=INK).encode(text="documents:Q")).properties(height=120),
         "prov_status")
    st.caption("`no_text_layer`: the results table is drawn as an image/vector glyphs (Dec 2025–Sep 2026); values "
               "were not OCR'd or guessed. `not_tbill_results`: bond releases, an unrelated notice or a garbled overlay.")
    table_and_download(docs, "results document status", "results_document_status.csv", "prov_docs")
    st.subheader("Preserved source anomalies (never silently fixed)")
    st.dataframe(t["source_anomalies.csv"], hide_index=True)
    st.download_button("Download source_anomalies.csv", t["source_anomalies.csv"].to_csv(index=False).encode(),
                       "source_anomalies.csv", "text/csv", key="dl_anom")


def date_window(dates: pd.Series, key: str):
    lo, hi = dates.min().date(), dates.max().date()
    return st.slider("Time window", min_value=lo, max_value=hi, value=(lo, hi), format="YYYY-MM-DD", key=key)


def page_observed(obs, cov):
    st.header("Observed official cut-off yields, 2022–2026")
    tenors = st.multiselect("Tenors", list(TENOR_COLORS), default=list(TENOR_COLORS), key="obs_tenors")
    w = date_window(obs["auction_date"], "obs_window")
    o = obs[obs["tenor_label"].isin(tenors) & obs["auction_date"].dt.date.between(*w)]
    if o.empty:
        st.info("No tenor selected.")
        return
    tip = [alt.Tooltip("auction_date:T", title="Auction", format="%Y-%m-%d"),
           alt.Tooltip("tenor_label:N", title="Tenor"),
           alt.Tooltip("observed_yield:Q", title="Cut-off money-market yield (%)", format=".3f"),
           alt.Tooltip("printed_yield_raw:N", title="As printed"), alt.Tooltip("cutoff_price_raw:N", title="Cut-off price"),
           alt.Tooltip("flag:N", title="Source flag")]
    base = alt.Chart(o).encode(x=alt.X("auction_date:T", title="Auction date"))
    lines = base.mark_line(strokeWidth=2).encode(
        y=alt.Y("observed_yield:Q", title="Cut-off money-market yield (% p.a.)", scale=alt.Scale(zero=False)),
        color=alt.Color("tenor_label:N", scale=tenor_color(tenors), title="Tenor"),
        detail="segment:N")
    pts = base.mark_point(filled=True, size=40).encode(
        y="observed_yield:Q", color=alt.Color("tenor_label:N", scale=tenor_color(tenors), title="Tenor"),
        shape=alt.Shape("tenor_label:N", scale=tenor_shape(tenors), title="Tenor"), tooltip=tip)
    flagged = base.transform_filter("datum.flag != ''").mark_point(size=260, strokeWidth=2, color=INK,
                                                                   shape="diamond").encode(y="observed_yield:Q",
                                                                                           tooltip=tip)
    miss = cov[~cov["results_status"].isin(["parsed", "scheduled after data cutoff"])
               & ~cov["results_status"].str.startswith("rescheduled")
               & cov["auction_date"].dt.date.between(*w)]
    rules = alt.Chart(miss).mark_rule(strokeDash=[3, 3], color="#9a9893").encode(
        x="auction_date:T", tooltip=[alt.Tooltip("auction_date:T", title="Scheduled auction", format="%Y-%m-%d"),
                                     alt.Tooltip("results_status:N", title="Why missing")])
    show((rules + lines + pts + flagged).properties(height=380), "obs_chart")
    st.caption(f"Gaps are **missing** auctions (dashed grey rules: {len(miss)} in window) — lines break there; "
               "nothing is interpolated or set to zero. Black diamonds mark preserved source anomalies "
               "(hover for details). Values shown are the primary analysis series (`13..001` repaired).")
    table_and_download(o.drop(columns=["segment"]), "observed series in window", "r04_observed_yields.csv", "obs")


def page_cohort(t, cov):
    st.header("Study cohort, pre-bid timing and exclusions")
    st.subheader("Inclusion flow (tenor-rows)")
    flow = t["inclusion_flow.csv"]
    st.dataframe(flow, hide_index=True)
    st.markdown("Of **117 scheduled auctions** before the cutoff (Invitation-to-Tender or results dates), 100 have "
                "parsed results; 10 are image-only releases; 7 have no T-bill results table in the BoU catalogue; "
                "the 10-Apr-2024 ITT date is the rescheduled auction 1176 (results dated 11-Apr). The primary forward "
                "test uses **45 auctions / 132 tenor-rows** (2024-01-03 → 2026-09-30); rows lacking any lag or "
                "verified pre-bid feature are excluded for **all** models alike.")
    status_order = ["parsed", "no_text_layer", "no T-bill results table in catalogue", "scheduled after data cutoff"]
    cc = cov.copy()
    cc["status_group"] = cc["results_status"].where(cc["results_status"].isin(status_order), "rescheduled")
    cc["test_set"] = cc["in_primary_test_set"].map({True: "in primary test set", False: "not in test set"})
    strip = alt.Chart(cc).mark_tick(thickness=3, size=26).encode(
        x=alt.X("auction_date:T", title="Scheduled auction date"),
        y=alt.Y("status_group:N", title=None, sort=status_order + ["rescheduled"]),
        color=alt.Color("test_set:N", scale=alt.Scale(domain=["in primary test set", "not in test set"],
                                                      range=["#2a78d6", "#9a9893"]), title=None),
        tooltip=[alt.Tooltip("auction_date:T", format="%Y-%m-%d", title="Auction"),
                 alt.Tooltip("results_status:N", title="Results"), alt.Tooltip("itt_timing_status:N", title="ITT timing"),
                 alt.Tooltip("tenors_with_yield:Q", title="Tenors with yield")])
    show(strip.properties(height=200), "cohort_strip")
    table_and_download(cc.drop(columns=["status_group", "test_set"]), "auction calendar coverage",
                       "r04_auction_coverage.csv", "cov")
    st.subheader("Invitation-to-Tender notice timing (is the offered amount really pre-bid?)")
    itt = t["prebid_itt_timing_audit.csv"].copy()
    lead = itt.dropna(subset=["notice_lead_days"])
    lead_c = lead[lead["notice_lead_days"].between(-30, 40)]
    show(alt.Chart(lead_c).mark_bar(cornerRadiusEnd=2, color="#2a78d6").encode(
        x=alt.X("notice_lead_days:Q", bin=alt.Bin(step=1), title="Notice date → auction date (days); window −30…40"),
        y=alt.Y("count():Q", title="Notices"),
        tooltip=[alt.Tooltip("count():Q", title="Notices")]).properties(height=200), "itt_hist")
    st.write(itt["timing_status"].value_counts().rename("notices"))
    st.caption("Offers are used only from notices dated 1–14 days before the auction (median 6). Notices dated on/after "
               "the auction (TIMING_VIOLATION) or with year typos (e.g. 371 days) are treated as unverified. Results "
               "PDFs' creation timestamps are ≥12.5 h after auction-day midnight (Kampala) — consistent with release "
               "after the 10:00 deadline, but this is retrospective metadata evidence, not a publication log.")
    table_and_download(itt, "ITT timing audit", "prebid_itt_timing_audit.csv", "itt")
    st.subheader("Model refit registry (primary)")
    table_and_download(t["model_registry_primary.csv"], "refit registry", "model_registry_primary.csv", "reg")


def page_forecasts(fl):
    st.header("Forward forecasts vs observed cut-off yields (test period)")
    c = st.columns([1, 2])
    tenor = c[0].selectbox("Tenor", [91, 182, 364], format_func=lambda x: f"{x}-day", key="fc_tenor")
    models = c[1].multiselect("Model families", d.MODEL_ORDER, default=d.MODEL_ORDER,
                              format_func=lambda m: d.MODEL_LABELS[m], key="fc_models")
    w = date_window(fl["auction_date"], "fc_window")
    f = fl[(fl["tenor"] == tenor) & fl["model"].isin(models) & fl["auction_date"].dt.date.between(*w)]
    if f.empty:
        st.info("Select at least one model.")
        return
    f = d.add_gap_segments(f, by=("tenor", "model"))
    obs = d.add_gap_segments(f.drop_duplicates("auction_date")[["auction_date", "tenor", "observed"]])
    tip = [alt.Tooltip("auction_date:T", title="Auction", format="%Y-%m-%d"),
           alt.Tooltip("model_label:N", title="Model"), alt.Tooltip("predicted:Q", title="Forecast (%)", format=".3f"),
           alt.Tooltip("observed:Q", title="Observed (%)", format=".3f"),
           alt.Tooltip("error:Q", title="Error (pp)", format="+.3f")]
    ol = alt.Chart(obs).mark_line(color=INK, strokeWidth=2.5).encode(
        x=alt.X("auction_date:T", title="Auction date"),
        y=alt.Y("observed:Q", title=f"{tenor}-day cut-off yield (% p.a.)", scale=alt.Scale(zero=False)),
        detail="segment:N")
    op = alt.Chart(obs).mark_point(color=INK, filled=True, size=45).encode(
        x="auction_date:T", y="observed:Q",
        tooltip=[alt.Tooltip("auction_date:T", format="%Y-%m-%d", title="Auction"),
                 alt.Tooltip("observed:Q", format=".3f", title="Observed (%)")])
    ml = alt.Chart(f).mark_line(strokeWidth=1.6, point=alt.OverlayMarkDef(size=28, filled=True)).encode(
        x="auction_date:T", y="predicted:Q",
        color=alt.Color("model_label:N", scale=model_scale(models), title="Forecast"),
        detail="segment:N", tooltip=tip)
    show((ol + op + ml).properties(height=360), "fc_timeline")
    st.caption("Black: observed official cut-off yield. Lines break wherever consecutive test auctions are more than "
               "21 days apart (unparsed auctions in between, e.g. Dec 2025–Sep 2026); nothing is interpolated. After "
               "such a gap the 'last observed yield' is the last *parsed* one, older than a real forecaster's.")
    st.subheader("Observed vs predicted (all tenors), one panel per model")
    sc = fl[fl["model"].isin(models) & fl["auction_date"].dt.date.between(*w)].copy()
    sc["tenor_label"] = sc["tenor"].astype(str) + "-day"
    lo, hi = float(min(sc["observed"].min(), sc["predicted"].min())) - 0.3, float(
        max(sc["observed"].max(), sc["predicted"].max())) + 0.3
    diag = alt.Chart(pd.DataFrame({"v": [lo, hi]})).mark_line(strokeDash=[4, 3], color=INK_2).encode(
        x=alt.X("v:Q", scale=alt.Scale(domain=[lo, hi])), y=alt.Y("v:Q", scale=alt.Scale(domain=[lo, hi])))
    pts = alt.Chart().mark_point(filled=True, size=40, opacity=0.85).encode(
        x=alt.X("observed:Q", title="Observed (% p.a.)", scale=alt.Scale(domain=[lo, hi])),
        y=alt.Y("predicted:Q", title="Predicted (% p.a.)", scale=alt.Scale(domain=[lo, hi])),
        color=alt.Color("tenor_label:N", scale=tenor_color(list(TENOR_COLORS)), title="Tenor"),
        shape=alt.Shape("tenor_label:N", scale=tenor_shape(list(TENOR_COLORS)), title="Tenor"),
        tooltip=tip + [alt.Tooltip("tenor_label:N", title="Tenor")])
    facet = alt.layer(diag, pts, data=sc).properties(width=210, height=210).facet(
        facet=alt.Facet("model_label:N", title=None, sort=[d.MODEL_LABELS[m] for m in d.MODEL_ORDER]), columns=3)
    show(facet, "fc_scatter")
    st.caption("Dashed line: perfect forecast (predicted = observed). Tenors of one auction are dependent "
               "observations, not 132 independent points.")
    table_and_download(f.drop(columns=["sq_error", "segment"]), f"{tenor}-day forecasts in window", f"r04_forecasts_{tenor}d.csv",
                       "fc")


def page_errors(t, fl, loss):
    st.header("Errors and per-auction loss differences")
    m = t["forward_metrics_all_sensitivities.csv"]
    prim = m[m["sensitivity"] == "repaired_typo"].copy()
    prim["model_label"] = prim["model"].map(d.MODEL_LABELS)
    st.subheader("MAE and RMSE (primary)")
    mm = prim.melt(id_vars=["model", "model_label"], value_vars=["MAE_pp", "RMSE_pp"], var_name="metric",
                   value_name="pp")
    mm["metric"] = mm["metric"].map({"MAE_pp": "MAE (pp)", "RMSE_pp": "RMSE (pp)"})
    g = alt.Chart(mm).mark_bar(cornerRadiusEnd=4, height=12).encode(
        y=alt.Y("model_label:N", sort=[d.MODEL_LABELS[x] for x in d.MODEL_ORDER], title=None),
        x=alt.X("pp:Q", title=UNIT), color=alt.Color("model_label:N", scale=model_scale(d.MODEL_ORDER), legend=None),
        tooltip=["model_label:N", "metric:N", alt.Tooltip("pp:Q", format=".4f")])
    show((g + g.mark_text(align="left", dx=3, color=INK).encode(text=alt.Text("pp:Q", format=".3f"),
                                                                color=alt.value(INK)))
         .properties(height=170, width=300).facet(column=alt.Column("metric:N", title=None)), "err_maermse")
    st.subheader("MAE by tenor (primary)")
    bt = t["mae_by_tenor_primary.csv"].copy()
    bt["model_label"] = bt["model"].map(d.MODEL_LABELS)
    bt["tenor_label"] = bt["tenor"].astype(str) + "-day (n=" + bt["n_test_rows"].astype(str) + ")"
    tb = alt.Chart(bt).mark_bar(cornerRadiusEnd=4, height=10).encode(
        y=alt.Y("model_label:N", sort=[d.MODEL_LABELS[x] for x in d.MODEL_ORDER], title=None),
        x=alt.X("MAE_pp:Q", title=f"MAE ({UNIT})"),
        color=alt.Color("model_label:N", scale=model_scale(d.MODEL_ORDER), legend=None),
        tooltip=["model_label:N", "tenor_label:N", alt.Tooltip("MAE_pp:Q", format=".4f"), "n_test_rows:Q"])
    show(tb.properties(height=150, width=260).facet(column=alt.Column("tenor_label:N", title=None,
                                                                  sort=sorted(bt["tenor_label"].unique(),
                                                                              key=lambda x: int(x.split("-")[0])))),
         "err_tenor")
    st.caption("The 91-day boosting MAE (0.509 vs 0.562) is a non-prespecified subgroup view, not a claim.")
    table_and_download(bt.drop(columns=["model_label", "tenor_label"]), "MAE by tenor", "mae_by_tenor_primary.csv",
                       "bt")

    st.subheader("Error distributions (descriptive)")
    e = fl.copy()
    e["tenor_label"] = e["tenor"].astype(str) + "-day"
    box = alt.Chart(e).mark_boxplot(size=14, median={"color": INK}, ticks=True).encode(
        x=alt.X("error:Q", title="Forecast − observed (pp)"),
        y=alt.Y("model_label:N", sort=[d.MODEL_LABELS[x] for x in d.MODEL_ORDER], title=None),
        color=alt.Color("model_label:N", scale=model_scale(d.MODEL_ORDER), legend=None))
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=INK, strokeDash=[4, 3]).encode(x="x:Q")
    show((zero + box).properties(height=230), "err_box")
    st.caption("Boxes pool 132 tenor-rows from 45 auctions; tenors within an auction are clustered, so the spread "
               "is descriptive, not an independent-sample test.")

    st.subheader("Per-auction loss difference vs last yield, with block-bootstrap CI")
    model = st.selectbox("Challenger", [x for x in d.MODEL_ORDER if x != "last_yield"],
                         format_func=lambda x: d.MODEL_LABELS[x], key="loss_model")
    lm = loss[loss["model"] == model].copy()
    lm["auction_date"] = pd.to_datetime(lm["auction_date"])
    row = prim.set_index("model").loc[model]
    band = alt.Chart(pd.DataFrame({"lo": [row["ci95_lo"]], "hi": [row["ci95_hi"]],
                                   "mean": [row["mean_auction_loss_diff_pp"]]}))
    bars = alt.Chart(lm).mark_bar(width=5, color=MODEL_COLORS[model]).encode(
        x=alt.X("auction_date:T", title="Test auction"),
        y=alt.Y("loss_diff_pp:Q", title="|error| − |last-yield error| (pp, mean over tenors)"),
        tooltip=[alt.Tooltip("auction_date:T", format="%Y-%m-%d", title="Auction"),
                 alt.Tooltip("loss_diff_pp:Q", format="+.3f", title="Loss difference (pp)"),
                 alt.Tooltip("n_tenors:Q", title="Tenors in auction")])
    ci = band.mark_rect(opacity=0.18, color=INK).encode(y="lo:Q", y2="hi:Q")
    mean = band.mark_rule(color=INK, strokeWidth=2).encode(y="mean:Q")
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=INK_2, strokeDash=[4, 3]).encode(y="y:Q")
    show((ci + zero + bars + mean).properties(height=320), "loss_chart")
    st.markdown(f"Mean **{row['mean_auction_loss_diff_pp']:+.4f} pp**, 95% moving-block bootstrap CI "
                f"[{row['ci95_lo']:+.4f}, {row['ci95_hi']:+.4f}] (block 4 auctions, 2000 replicates, seed 20261017; "
                f"n = {int(row['n_test_auctions'])} auctions). Positive = worse than the last observed yield. "
                "Shaded band: CI of the mean; bars: individual auctions.")
    table_and_download(lm[["auction_date", "model", "loss_diff_pp", "n_tenors"]], "per-auction loss differences",
                       f"r04_loss_diff_{model}.csv", "loss")


def page_sensitivity(t):
    st.header("Prespecified source-repair sensitivities")
    m = t["forward_metrics_all_sensitivities.csv"].copy()
    m = m[m["model"] != "last_yield"]
    m["model_label"] = m["model"].map(d.MODEL_LABELS)
    m["sensitivity_label"] = m["sensitivity"].map(d.SENSITIVITY_LABELS)
    sens = st.multiselect("Sensitivities", list(d.SENSITIVITY_LABELS), default=list(d.SENSITIVITY_LABELS),
                          format_func=lambda s: d.SENSITIVITY_LABELS[s], key="sens_sel")
    m = m[m["sensitivity"].isin(sens)]
    if m.empty:
        st.info("Select at least one sensitivity.")
        return
    tip = [alt.Tooltip("sensitivity_label:N", title="Sensitivity"), alt.Tooltip("model_label:N", title="Model"),
           alt.Tooltip("mean_auction_loss_diff_pp:Q", format="+.4f", title="Mean loss diff (pp)"),
           alt.Tooltip("ci95_lo:Q", format="+.4f", title="CI low"), alt.Tooltip("ci95_hi:Q", format="+.4f", title="CI high"),
           alt.Tooltip("MAE_pp:Q", format=".4f", title="MAE (pp)"), alt.Tooltip("n_test_auctions:Q", title="Test auctions")]
    order = [d.SENSITIVITY_LABELS[k] for k in d.SENSITIVITY_LABELS]
    base = alt.Chart().encode(y=alt.Y("sensitivity_label:N", sort=order, title=None),
                              color=alt.Color("model_label:N", scale=model_scale(d.MODEL_ORDER[1:]), legend=None))
    err = base.mark_rule(strokeWidth=2).encode(
        x=alt.X("ci95_lo:Q", title="Loss diff vs last yield (pp), 95% CI"), x2="ci95_hi:Q", tooltip=tip)
    dot = base.mark_point(filled=True, size=90, opacity=1).encode(x="mean_auction_loss_diff_pp:Q", tooltip=tip)
    zero = alt.Chart().mark_rule(color=INK, strokeDash=[4, 3]).encode(x=alt.datum(0))
    show(alt.layer(zero, err, dot, data=m).properties(height=150, width=260)
         .facet(facet=alt.Facet("model_label:N", title=None, sort=[d.MODEL_LABELS[x] for x in d.MODEL_ORDER[1:]]),
                columns=2), "sens_chart")
    st.caption("Right of the dashed line = worse than the last observed yield. Verdict is NEGATIVE_MODEL in every "
               "sensitivity; test auctions per sensitivity: 44 / 45 / 43 / 43.")
    table_and_download(t["forward_metrics_all_sensitivities.csv"], "all metrics", "forward_metrics_all_sensitivities.csv",
                       "sens")


def page_limitations():
    st.header("Limitations and timing uncertainty")
    st.markdown((ROOT / "docs" / "LIMITATIONS.md").read_text())


def page_repro(repro):
    st.header("Reproducibility and deployment status")
    if repro:
        st.success(f"Independent re-run on {repro['date_utc']} at code `{repro['code_commit'][:7]}` from "
                   f"{repro['raw_inputs']['documents_present']}/{repro['raw_inputs']['documents_expected']} "
                   "checksum-valid cached BoU documents (no re-download): **all 9 committed tables reproduced "
                   f"exactly** in {repro['wall_seconds']} s.")
        mx = pd.read_csv(ROOT / "results" / "reproduction" / "reproduction_matrix.csv")
        st.dataframe(mx, hide_index=True)
        st.json({k: v for k, v in repro.items() if k in ("command", "compare_command", "environment", "not_changed")})
    st.markdown((ROOT / "docs" / "REPRODUCIBILITY.md").read_text())
    dep = ROOT / "docs" / "DEPLOYMENT.md"
    if dep.exists():
        st.markdown(dep.read_text())


SECTIONS = {
    "Overview": "overview", "Data provenance": "provenance", "Observed yields": "observed",
    "Cohort and pre-bid timing": "cohort", "Forecasts vs observed": "forecasts", "Errors and loss differences": "errors",
    "Sensitivities": "sensitivity", "Limitations": "limitations", "Reproducibility and deployment": "repro",
}


def main() -> None:
    st.set_page_config(page_title="R04 · Uganda T-bill pre-bid forecasts", layout="wide")
    try:
        info, repro = d.run_summary(), d.reproduction_record()
        t, cov, obs, fl, loss, rec = load_all()
    except d.MissingResultsError as exc:
        st.error(f"Cannot start: {exc}")
        st.stop()
    cutoff = str(obs.dropna(subset=["observed_yield"])["auction_date"].max().date())
    ribbon(info, repro, cutoff)
    page = st.sidebar.radio("Section", list(SECTIONS))
    st.sidebar.caption("Bank of Uganda auction statistics; analysis by R04 (research). Not investment advice.")
    key = SECTIONS[page]
    if key == "overview":
        page_overview(t, rec)
    elif key == "provenance":
        page_provenance(t)
    elif key == "observed":
        page_observed(obs, cov)
    elif key == "cohort":
        page_cohort(t, cov)
    elif key == "forecasts":
        page_forecasts(fl)
    elif key == "errors":
        page_errors(t, fl, loss)
    elif key == "sensitivity":
        page_sensitivity(t)
    elif key == "limitations":
        page_limitations()
    else:
        page_repro(repro)


main()
