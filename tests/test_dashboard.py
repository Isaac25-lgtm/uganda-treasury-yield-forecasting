"""Dashboard smoke test against the committed aggregate tables (skipped if streamlit is absent)."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("section", ["Overview", "Data provenance", "Study cohort", "Baselines and models",
                                     "Validation", "Sensitivity / limitations", "Reproducibility"])
def test_dashboard_sections_render(section):
    testing = pytest.importorskip("streamlit.testing.v1")
    if not (ROOT / "results/tables/forward_metrics_all_sensitivities.csv").exists():
        pytest.skip("aggregate tables not generated")
    at = testing.AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=60)
    at.run()
    at.sidebar.radio[0].set_value(section).run()
    assert not at.exception, at.exception
