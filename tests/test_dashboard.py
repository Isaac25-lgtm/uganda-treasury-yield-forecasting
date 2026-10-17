"""Dashboard tests (Streamlit AppTest) against the committed aggregate tables.

In CI the dashboard requirements are installed and ``R04_REQUIRE_DASHBOARD=1`` turns a missing streamlit
into a failure instead of a skip.
"""

import os
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "dashboard" / "app.py")
sys.path.insert(0, str(ROOT / "dashboard"))

if os.environ.get("R04_REQUIRE_DASHBOARD") == "1":
    import streamlit.testing.v1 as testing  # noqa: F401  (must be importable in CI)
else:
    testing = pytest.importorskip("streamlit.testing.v1")

import r04_data  # noqa: E402

SECTIONS = {  # section -> minimum number of Altair charts it must render
    "Overview": 1, "Data provenance": 1, "Observed yields": 1, "Cohort and pre-bid timing": 2,
    "Forecasts vs observed": 2, "Errors and loss differences": 4, "Sensitivities": 1, "Limitations": 0,
    "Reproducibility and deployment": 0,
}
DOWNLOAD_NAME = re.compile(r"^Download ([a-z0-9_]+\.csv)$")


def _count(node, kind):
    n = int(getattr(node, "type", None) == kind)
    ch = getattr(node, "children", None)
    if isinstance(ch, dict):
        n += sum(_count(c, kind) for c in ch.values())
    return n


def _open(section):
    at = testing.AppTest.from_file(APP, default_timeout=90)
    at.run()
    at.sidebar.radio[0].set_value(section).run()
    assert not at.exception, at.exception
    return at


def _downloads_ok(at):
    allowed = set(r04_data.DOWNLOADABLE_TABLES)
    for b in at.get("download_button"):
        m = DOWNLOAD_NAME.match(b.proto.label)
        assert m, b.proto.label
        name = m.group(1)
        assert name in allowed or name.startswith("r04_"), name  # allowlisted table or derived chart data


@pytest.mark.parametrize("section", list(SECTIONS))
def test_every_section_renders_with_charts_and_safe_downloads(section):
    at = _open(section)
    assert _count(at._tree, "vega_lite_chart") >= SECTIONS[section]
    _downloads_ok(at)
    text = " ".join(m.value for m in at.markdown)
    assert "NEGATIVE_MODEL" in text and "not simulated" in text and "not investment advice" in text


def test_sidebar_lists_every_section():
    at = testing.AppTest.from_file(APP, default_timeout=90)
    at.run()
    assert list(at.sidebar.radio[0].options) == list(SECTIONS)


def test_observed_widgets_filter_tenor_and_window():
    at = _open("Observed yields")
    at.multiselect(key="obs_tenors").set_value(["364-day"]).run()
    lo, hi = at.slider(key="obs_window").value
    at.slider(key="obs_window").set_value((pd.Timestamp("2024-01-01").date(), hi)).run()
    assert not at.exception
    at.multiselect(key="obs_tenors").set_value([]).run()
    assert not at.exception and any("No tenor selected" in i.value for i in at.info)


def test_forecast_widgets_all_five_models_and_tenors():
    at = _open("Forecasts vs observed")
    assert set(at.multiselect(key="fc_models").value) == set(r04_data.MODEL_ORDER)
    for tenor in (91, 182, 364):
        at.selectbox(key="fc_tenor").set_value(tenor).run()
        assert not at.exception
        assert _count(at._tree, "vega_lite_chart") == 2
    at.multiselect(key="fc_models").set_value(["last_yield", "hgb_prebid"]).run()
    assert not at.exception
    at.multiselect(key="fc_models").set_value([]).run()
    assert any("Select at least one model" in i.value for i in at.info)


def test_loss_difference_selector_every_challenger():
    at = _open("Errors and loss differences")
    for m in r04_data.MODEL_ORDER[1:]:
        at.selectbox(key="loss_model").set_value(m).run()
        assert not at.exception
        assert any("95% moving-block bootstrap CI" in md.value for md in at.markdown)


def test_sensitivity_selector():
    at = _open("Sensitivities")
    at.multiselect(key="sens_sel").set_value(["drop_1176"]).run()
    assert not at.exception
    at.multiselect(key="sens_sel").set_value([]).run()
    assert any("Select at least one sensitivity" in i.value for i in at.info)


def test_app_reports_missing_results_without_traceback(tmp_path, monkeypatch):
    monkeypatch.setenv("R04_RESULTS_DIR", str(tmp_path))
    sys.modules.pop("r04_data", None)
    at = testing.AppTest.from_file(APP, default_timeout=90)
    at.run()
    sys.modules.pop("r04_data", None)
    assert not at.exception
    assert any("Cannot start" in e.value for e in at.error)


def test_download_frames_are_safe():
    t = {n: r04_data.load_table(n) for n in r04_data.DOWNLOADABLE_TABLES}
    for name, df in t.items():
        r04_data.safe_download_frame(df)
        assert not any(c.lower().endswith(("path", "secret")) for c in df.columns), name
    with pytest.raises(ValueError):
        r04_data.safe_download_frame(pd.DataFrame({"bidder_name": ["x"]}))
    with pytest.raises(ValueError):
        r04_data.safe_download_frame(pd.DataFrame({"f": ["/home/user/secret.pdf"]}))


def test_observed_series_never_fills_missing_auctions():
    t = {n: r04_data.load_table(n) for n in r04_data.DOWNLOADABLE_TABLES}
    cov = r04_data.auction_coverage(t["event_registry_tenor_rows.csv"], t["prebid_itt_timing_audit.csv"],
                                    t["results_document_status.csv"], t["forecasts_primary.csv"])
    assert cov["results_status"].value_counts().to_dict() == {
        "parsed": 100, "no_text_layer": 10, "no T-bill results table in catalogue": 7,
        "rescheduled: results dated 2024-04-11": 1, "scheduled after data cutoff": 1}
    obs = r04_data.observed_series(t["event_registry_tenor_rows.csv"], cov)
    missing = obs[obs["results_status"] != "parsed"]
    assert len(missing) == 17 * 3 and missing["observed_yield"].isna().all()
    assert not (obs["observed_yield"] == 0).any()
    # a line segment never spans a missing auction
    for (_, _), g in obs.dropna(subset=["observed_yield"]).groupby(["tenor", "segment"]):
        dates = obs[(obs["tenor"] == g["tenor"].iloc[0])].set_index("auction_date")["observed_yield"]
        span = dates.loc[g["auction_date"].min():g["auction_date"].max()]
        assert span.notna().all()
