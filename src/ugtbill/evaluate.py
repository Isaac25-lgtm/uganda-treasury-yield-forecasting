"""Frozen forward, auction-grouped evaluation (configs/experiment.yaml).

Expanding window, one-step-ahead: before each test auction every model is refitted
on all tenor-rows of strictly earlier auctions; all tenors of the test auction are
predicted together. Loss differentials are formed per auction and resampled with a
moving-block bootstrap over test auctions.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import LAG_FEATURES, PREBID_FEATURES, assert_no_same_auction_leakage

RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)


def _ridge_inner_cv(train: pd.DataFrame, cols: list[str]) -> float:
    """Choose alpha by inner forward CV on the training window only (last 30% of its auctions)."""
    dates = np.sort(train["auction_date"].unique())
    cut = dates[int(len(dates) * 0.7)]
    tr, va = train[train["auction_date"] < cut], train[train["auction_date"] >= cut]
    if len(tr) < 15 or len(va) < 3:
        return 10.0
    best, best_a = np.inf, 10.0
    for a in RIDGE_ALPHAS:
        m = make_pipeline(StandardScaler(), Ridge(alpha=a)).fit(tr[cols], tr["dy"])
        err = np.mean(np.abs(m.predict(va[cols]) - va["dy"]))
        if err < best:
            best, best_a = err, a
    return best_a


def _ar1_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    out = np.empty(len(test))
    for i, (_, r) in enumerate(test.iterrows()):
        g = train[train["tenor"] == r["tenor"]]
        X = np.column_stack([np.ones(len(g)), g["y_lag1"].to_numpy()])
        beta, *_ = np.linalg.lstsq(X, g["y"].to_numpy(), rcond=None)
        out[i] = beta[0] + beta[1] * r["y_lag1"]
    return out


def forward_evaluate(feat: pd.DataFrame, first_test: str, min_train_events: int = 20,
                     seed: int = 20261017, use_prebid: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    prebid = PREBID_FEATURES if use_prebid else []
    cols_pre = LAG_FEATURES + prebid
    cols_lag = list(LAG_FEATURES)
    assert_no_same_auction_leakage(cols_pre)
    need = ["y", "y_lag1"] + cols_pre
    data = feat.dropna(subset=need).copy()
    events = np.sort(data["auction_date"].unique())
    test_events = [d for d in events if d >= np.datetime64(first_test)]
    preds, registry = [], []
    for d in test_events:
        train = data[data["auction_date"] < d]
        test = data[data["auction_date"] == d]
        if train["auction_date"].nunique() < min_train_events:
            continue
        t0 = time.perf_counter()
        p = {"last_yield": test["y_lag1"].to_numpy(), "ar1": _ar1_predict(train, test)}
        a_pre = _ridge_inner_cv(train, cols_pre)
        m = make_pipeline(StandardScaler(), Ridge(alpha=a_pre)).fit(train[cols_pre], train["dy"])
        p["ridge_prebid"] = test["y_lag1"].to_numpy() + m.predict(test[cols_pre])
        a_lag = _ridge_inner_cv(train, cols_lag)
        m = make_pipeline(StandardScaler(), Ridge(alpha=a_lag)).fit(train[cols_lag], train["dy"])
        p["ridge_lag_only"] = test["y_lag1"].to_numpy() + m.predict(test[cols_lag])
        g = HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=200,
                                          min_samples_leaf=10, random_state=seed)
        g.fit(train[cols_pre], train["dy"])
        p["hgb_prebid"] = test["y_lag1"].to_numpy() + g.predict(test[cols_pre])
        for name, yhat in p.items():
            for (_, r), yh in zip(test.iterrows(), yhat):
                preds.append({"auction_date": d, "issue_no": r.get("issue_no"), "tenor": r["tenor"],
                              "model": name, "y": r["y"], "y_lag1": r["y_lag1"], "yhat": yh})
        registry.append({"auction_date": d, "n_train_rows": len(train),
                         "n_train_events": train["auction_date"].nunique(), "ridge_alpha_prebid": a_pre,
                         "ridge_alpha_lag": a_lag, "fit_seconds": round(time.perf_counter() - t0, 3)})
    pr = pd.DataFrame(preds)
    pr["abs_err"] = (pr["yhat"] - pr["y"]).abs()
    return pr, pd.DataFrame(registry)


def block_bootstrap_ci(x: np.ndarray, block: int = 4, reps: int = 2000, seed: int = 20261017,
                       level: float = 0.95) -> tuple[float, float]:
    """Moving-block bootstrap percentile CI for the mean of a time-ordered series."""
    x = np.asarray(x, float)
    n = len(x)
    if n == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts_max = max(n - block, 0)
    means = np.empty(reps)
    for b in range(reps):
        starts = rng.integers(0, starts_max + 1, size=nb)
        idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts])[:n]
        means[b] = x[idx].mean()
    lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def summarise(pr: pd.DataFrame, baseline: str = "last_yield", seed: int = 20261017) -> pd.DataFrame:
    rows = []
    base = pr[pr["model"] == baseline].set_index(["auction_date", "tenor"])
    for name, g in pr.groupby("model", sort=False):
        g = g.set_index(["auction_date", "tenor"])
        diff = (g["abs_err"] - base.loc[g.index, "abs_err"]).groupby(level=0).mean().sort_index()
        lo, hi = block_bootstrap_ci(diff.to_numpy(), seed=seed)
        dy_true = g["y"] - g["y_lag1"]
        dy_hat = g["yhat"] - g["y_lag1"]
        nz = dy_true.abs() > 1e-9
        moved = dy_hat.abs() > 1e-9
        da = float((np.sign(dy_hat[nz & moved]) == np.sign(dy_true[nz & moved])).mean()) if (nz & moved).any() else np.nan
        mae = g["abs_err"].mean()
        mae_b = base["abs_err"].mean()
        rows.append({"model": name, "n_test_auctions": g.index.get_level_values(0).nunique(),
                     "n_test_rows": len(g), "MAE_pp": mae, "RMSE_pp": float(np.sqrt((g["abs_err"] ** 2).mean())),
                     "MAE_change_vs_last_pct": 100 * (mae - mae_b) / mae_b,
                     "mean_auction_loss_diff_pp": diff.mean(), "ci95_lo": lo, "ci95_hi": hi,
                     "directional_acc_nonzero": da})
    return pd.DataFrame(rows)


def decision(summary: pd.DataFrame, timing_verified: bool, prebid_models=("ridge_prebid", "hgb_prebid")) -> str:
    s = summary.set_index("model")
    credible = any(
        (m in s.index) and s.loc[m, "MAE_change_vs_last_pct"] <= -5.0 and s.loc[m, "ci95_hi"] < 0
        for m in prebid_models
    )
    if credible and timing_verified:
        return "CONDITIONAL"
    if credible and not timing_verified:
        return "HOLD_DATA"
    return "NEGATIVE_MODEL"
