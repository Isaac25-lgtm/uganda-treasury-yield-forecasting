"""Source-result consistency: committed tables must agree with each other and with the frozen experiment.

These tests read only committed aggregate outputs (results/), so they run in CI without raw documents.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ugtbill.evaluate import decision
from ugtbill.preprocess import RawInputError, verify_raw_inputs

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "results" / "tables"
sys.path.insert(0, str(ROOT / "dashboard"))
sys.path.insert(0, str(ROOT / "scripts"))
import r04_data  # noqa: E402

MODELS = ["last_yield", "ar1", "ridge_prebid", "ridge_lag_only", "hgb_prebid"]


@pytest.fixture(scope="module")
def fc():
    return pd.read_csv(T / "forecasts_primary.csv")


@pytest.fixture(scope="module")
def metrics():
    return pd.read_csv(T / "forward_metrics_all_sensitivities.csv")


def test_exact_primary_experiment_coverage(fc):
    assert fc["auction_date"].nunique() == 45
    assert len(fc) == 132
    assert fc["auction_date"].min() == "2024-01-03" and fc["auction_date"].max() == "2026-09-30"
    assert fc.groupby("tenor").size().to_dict() == {91: 42, 182: 45, 364: 45}
    assert set(MODELS) <= set(fc.columns)
    assert not fc[MODELS + ["y"]].isna().any().any(), "every model must be scored on identical rows"


def test_mae_rmse_recomputed_from_committed_forecasts(fc, metrics):
    rec = r04_data.recompute_metrics(fc)
    prim = metrics[metrics["sensitivity"] == "repaired_typo"].set_index("model")
    for m in MODELS:
        assert rec.loc[m, "MAE_pp"] == pytest.approx(prim.loc[m, "MAE_pp"], abs=1e-5)   # table rounded to 5 dp
        assert rec.loc[m, "RMSE_pp"] == pytest.approx(prim.loc[m, "RMSE_pp"], abs=1e-5)
        assert rec.loc[m, "n_test_rows"] == prim.loc[m, "n_test_rows"] == 132
    assert rec.loc["last_yield", "MAE_pp"] == pytest.approx(0.33686, abs=1e-5)
    assert rec["MAE_pp"].idxmin() == "last_yield"


def test_mae_by_tenor_recomputed(fc):
    bt = pd.read_csv(T / "mae_by_tenor_primary.csv").set_index(["model", "tenor"])
    lg = r04_data.forecasts_long(fc)
    re = lg.groupby(["model", "tenor"])["abs_error"].agg(["mean", "size"])
    for idx, row in bt.iterrows():
        assert re.loc[idx, "mean"] == pytest.approx(row["MAE_pp"], abs=1e-9)
        assert re.loc[idx, "size"] == row["n_test_rows"]


def test_per_auction_loss_difference_mean_matches_committed(fc, metrics):
    loss = r04_data.per_auction_loss_differences(fc)
    prim = metrics[metrics["sensitivity"] == "repaired_typo"].set_index("model")
    for m in MODELS[1:]:
        lm = loss[loss["model"] == m]
        assert len(lm) == 45
        assert lm["loss_diff_pp"].mean() == pytest.approx(prim.loc[m, "mean_auction_loss_diff_pp"], abs=1e-5)
        assert prim.loc[m, "ci95_lo"] <= prim.loc[m, "mean_auction_loss_diff_pp"] <= prim.loc[m, "ci95_hi"]


def test_all_four_sensitivities_and_go_rule(metrics):
    assert set(metrics["sensitivity"]) == {"as_printed", "repaired_typo", "drop_1176", "drop_identity_flags"}
    assert metrics.groupby("sensitivity")["model"].apply(set).map(lambda s: s == set(MODELS)).all()
    for s, g in metrics.groupby("sensitivity"):
        assert decision(g, timing_verified=True) == "NEGATIVE_MODEL", s
        assert (g.set_index("model").drop("last_yield")["MAE_change_vs_last_pct"] > 0).all(), s
    assert metrics.groupby("sensitivity")["n_test_auctions"].first().to_dict() == {
        "as_printed": 44, "repaired_typo": 45, "drop_1176": 43, "drop_identity_flags": 43}


def test_inclusion_flow_matches_metrics(metrics):
    flow = pd.read_csv(T / "inclusion_flow.csv").set_index("sensitivity")
    first = metrics.groupby("sensitivity")[["n_test_auctions", "n_test_rows"]].first()
    for s in flow.index:
        assert flow.loc[s, "test_events"] == first.loc[s, "n_test_auctions"]
        assert flow.loc[s, "test_rows_per_model"] == first.loc[s, "n_test_rows"]
        assert flow.loc[s, "events_parsed"] == 100 and flow.loc[s, "tenor_rows_parsed"] == 300


def test_source_anomalies_preserved():
    an = pd.read_csv(T / "source_anomalies.csv")
    assert (an["mmy_raw"] == "13..001").sum() == 1
    assert (an.loc[an["printed_auction_no"] == 1176, "identity_ok"] == False).sum() == 3  # noqa: E712
    reg = pd.read_csv(T / "event_registry_tenor_rows.csv")
    assert len(reg) == 300 and reg["auction_date"].nunique() == 100
    assert int(reg["identity_ok"].sum()) == 296 and int(reg["mmy_repaired"].notna().sum()) == 299


def test_run_summary_and_reproduction_record():
    run = json.loads((ROOT / "results/run_summary.json").read_text())
    assert run["decision"] == "NEGATIVE_MODEL" and run["primary_sensitivity"] == "repaired_typo"
    assert run["macro_features"].startswith("HOLD_DATA")
    rec = json.loads((ROOT / "results/reproduction/reproduction_record.json").read_text())
    assert rec["raw_inputs"]["documents_present"] == 239
    assert rec["raw_inputs"]["documents_missing"] == 0 and rec["raw_inputs"]["sha256_mismatches"] == 0
    assert rec["redownloaded_documents"] == 0
    mx = pd.read_csv(ROOT / "results/reproduction/reproduction_matrix.csv")
    assert set(mx["table"]) == {p.name for p in T.glob("*.csv")}
    assert (mx["status"] == "EXACT").all()


# ---- missing / empty inputs must fail clearly ------------------------------------------------------------
def _manifest(tmp_path, content=b"x"):
    import hashlib
    f = tmp_path / "doc.pdf"
    f.write_bytes(content)
    return pd.DataFrame({"local_file": ["doc.pdf"], "sha256": [hashlib.sha256(content).hexdigest()]})


def test_verify_raw_inputs_ok_and_failures(tmp_path):
    man = _manifest(tmp_path)
    verify_raw_inputs(man, tmp_path)
    with pytest.raises(RawInputError, match="empty"):
        verify_raw_inputs(man.iloc[0:0], tmp_path)
    with pytest.raises(RawInputError, match="missing"):
        verify_raw_inputs(man, tmp_path / "nowhere")
    (tmp_path / "doc.pdf").write_bytes(b"tampered")
    with pytest.raises(RawInputError, match="1 altered"):
        verify_raw_inputs(man, tmp_path)


def test_pipeline_refuses_to_run_without_raw_documents(tmp_path):
    import run_pipeline
    with pytest.raises(RawInputError, match="NOT a reproduction"):
        run_pipeline.main(["--out-dir", str(tmp_path / "out"), "--raw-dir", str(tmp_path / "empty")])


def test_dashboard_loader_fails_clearly(tmp_path):
    with pytest.raises(r04_data.MissingResultsError, match="missing"):
        r04_data.load_table("forecasts_primary.csv", tables=tmp_path)
    (tmp_path / "forecasts_primary.csv").write_text("auction_date,tenor,y\n")
    with pytest.raises(r04_data.MissingResultsError, match="empty"):
        r04_data.load_table("forecasts_primary.csv", tables=tmp_path)


def test_compare_reproduction_detects_differences():
    import compare_reproduction as cr
    a = pd.DataFrame({"k": ["x", "y"], "v": [1.0, np.nan], "fit_seconds": [1.0, 2.0]})
    assert cr.compare_tables(a, a.assign(fit_seconds=[9.0, 9.0]))["status"] == "EXACT"
    assert cr.compare_tables(a, a.assign(v=[1.00005, np.nan]))["status"] == "WITHIN_ROUNDING_TOLERANCE"
    assert cr.compare_tables(a, a.assign(v=[1.1, np.nan]))["status"] == "VALUES_DIFFER"
    assert cr.compare_tables(a, a.assign(k=["x", "z"]))["status"] == "VALUES_DIFFER"
    assert cr.compare_tables(a, a.iloc[:1])["status"] == "STRUCTURE_DIFFERS"
