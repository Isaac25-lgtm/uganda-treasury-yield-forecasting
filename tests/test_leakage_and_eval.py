"""Leakage, timing and evaluation tests on SYNTHETIC panels (not observed data)."""

import numpy as np
import pandas as pd
import pytest

from ugtbill.acquire import flatten_catalog, select_tbill_documents
from ugtbill.evaluate import block_bootstrap_ci, decision, forward_evaluate, summarise
from ugtbill.features import (LAG_FEATURES, PREBID_FEATURES, assert_no_same_auction_leakage,
                              build_features)
from ugtbill.preprocess import classify_notice_timing


def synthetic_panel(n_events=40, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-05", periods=n_events, freq="14D")
    rows = []
    level = {91: 9.0, 182: 11.0, 364: 12.5}
    for i, d in enumerate(dates):
        for t in (91, 182, 364):
            level[t] += rng.normal(0, 0.2)
            rows.append({"auction_date": d, "tenor": t, "y": level[t], "issue_no": 1000 + i,
                         "offer_tenor": {91: 15e9, 182: 40e9, 364: 180e9}[t] * (1 + (i % 5 == 0)),
                         "offer_total": 235e9 * (1 + (i % 5 == 0))})
    return pd.DataFrame(rows)


def test_forbidden_same_auction_fields_rejected():
    assert_no_same_auction_leakage(LAG_FEATURES + PREBID_FEATURES)
    for bad in ("bid_cover", "accepted_amount", "tendered", "cutoff_price", "wavg_yield"):
        with pytest.raises(ValueError):
            assert_no_same_auction_leakage(LAG_FEATURES + [bad])


def test_features_do_not_use_target_auction_outcome():
    p = synthetic_panel()
    f1 = build_features(p)
    p2 = p.copy()
    target_day = p2["auction_date"].unique()[20]
    p2.loc[p2["auction_date"] == target_day, "y"] += 5.0  # perturb the target auction's outcome
    f2 = build_features(p2)
    m = f1["auction_date"] == target_day
    cols = [c for c in LAG_FEATURES + PREBID_FEATURES]
    pd.testing.assert_frame_equal(f1.loc[m, cols].reset_index(drop=True), f2.loc[m, cols].reset_index(drop=True))
    # ... while the next auction's lag features do see it
    nxt = f1["auction_date"] == p["auction_date"].unique()[21]
    assert not np.allclose(f1.loc[nxt, "y_lag1"], f2.loc[nxt, "y_lag1"])


def test_lag1_is_previous_event_same_tenor():
    f = build_features(synthetic_panel())
    g = f[f["tenor"] == 182].sort_values("auction_date")
    assert np.allclose(g["y_lag1"].iloc[1:].to_numpy(), g["y"].iloc[:-1].to_numpy())


def test_forward_evaluation_is_strictly_forward_and_grouped():
    f = build_features(synthetic_panel(50))
    pr, reg = forward_evaluate(f, first_test="2023-01-01", min_train_events=20)
    assert len(reg) > 0
    first_test = pd.Timestamp("2023-01-01")
    assert (pd.to_datetime(pr["auction_date"]) >= first_test).all()
    # every test auction predicted for all tenors by every model on identical rows
    counts = pr.groupby(["auction_date", "model"]).size()
    assert counts.nunique() == 1
    lastp = pr[pr["model"] == "last_yield"]
    assert np.allclose(lastp["yhat"], lastp["y_lag1"])
    # training window grows by exactly one event per test auction
    assert (np.diff(reg["n_train_events"]) == 1).all()


def test_bootstrap_and_decision_rule():
    lo, hi = block_bootstrap_ci(np.full(30, -0.1))
    assert lo == pytest.approx(-0.1) and hi == pytest.approx(-0.1)
    s = pd.DataFrame({"model": ["last_yield", "ridge_prebid", "hgb_prebid"],
                      "MAE_change_vs_last_pct": [0, -8.0, 3.0], "ci95_hi": [0, -0.01, 0.05]})
    assert decision(s, timing_verified=True) == "CONDITIONAL"
    assert decision(s, timing_verified=False) == "HOLD_DATA"
    s.loc[1, "ci95_hi"] = 0.01
    assert decision(s, timing_verified=True) == "NEGATIVE_MODEL"


def test_summarise_baseline_has_zero_differential():
    f = build_features(synthetic_panel(45))
    pr, _ = forward_evaluate(f, first_test="2023-01-01")
    s = summarise(pr).set_index("model")
    assert s.loc["last_yield", "mean_auction_loss_diff_pp"] == 0
    assert set(s.index) == {"last_yield", "ar1", "ridge_prebid", "ridge_lag_only", "hgb_prebid"}


def test_notice_timing_classification():
    itt = pd.DataFrame({
        "issue_no": [1, 2, 3, 4, None, 6],
        "auction_date": ["2024-03-13", "2024-03-13", "2024-03-13", "2023-01-18", None, None],
        "notice_date": ["2024-03-07", "2024-03-14", "2024-03-13", "2022-01-12", None, "2024-01-01"],
    })
    st = classify_notice_timing(itt)["timing_status"].tolist()
    assert st == ["pre_bid_verified", "TIMING_VIOLATION", "TIMING_VIOLATION",
                  "implausible_lead_unverified", "no_text_layer", "auction_date_unparsed"]


def test_catalogue_selection_excludes_bonds():
    cat = {"data": {"auctionInformation": {"items": [
        {"category": "Auction results", "file": [{"year": 2024, "fileWithMonth": [{"month": "May", "file": [
            {"title": "Press-Release-TBill-08-May-2024", "file": {"url": "/uploads/a.pdf", "name": "a.pdf"}},
            {"title": "Press-Release-Report-for-the-3-YR-20-YR-T-Bonds", "file": {"url": "/uploads/b.pdf", "name": "b.pdf"}},
        ]}]}]},
        {"category": "Invitation to tender", "file": [{"year": 2024, "fileWithMonth": [{"month": "May", "file": [
            {"title": "Invitation to Tender for Treasury Bills Issue No 1179", "file": {"url": "/uploads/c.pdf", "name": "c.pdf"}},
            {"title": "Invitation to Tender for the 2-Year 5-year bonds", "file": {"url": "/uploads/d.pdf", "name": "d.pdf"}},
        ]}]}]},
    ]}}}
    docs = select_tbill_documents(flatten_catalog(cat), first_year=2023)
    assert sorted(d["url_path"] for d in docs) == ["/uploads/a.pdf", "/uploads/c.pdf"]
