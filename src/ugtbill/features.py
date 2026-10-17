"""Split-safe features with explicit availability rules.

Input ``panel``: one row per (auction event, tenor) with columns
``event_key, issue_no, auction_date, tenor, y`` (cut-off yield, %) and the target
auction's own Invitation-to-Tender fields ``offer_tenor, offer_total, itt_notice_date``.

Every lag feature is computed from *earlier auction events only* (shift within tenor,
ordered by auction date). The ITT fields are pre-bid by construction (published
before the bid deadline). No field derived from the target auction's bids, cover,
allotment or accepted price/yield may be added here; ``FORBIDDEN_SUBSTRINGS`` is
enforced by :func:`assert_no_same_auction_leakage` and the tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TENORS = (91, 182, 364)
LAG_FEATURES = ["dy_lag1", "dy_lag2", "y_lag1", "spread_364_91_lag1", "spread_182_91_lag1",
                "days_since_prev", "t182", "t364"]
PREBID_FEATURES = ["log_offer_tenor", "offer_change_vs_prev", "offer_share_tenor"]
FORBIDDEN_SUBSTRINGS = ("bid", "cover", "accepted", "allot", "wavg", "weighted", "price", "tendered")


def assert_no_same_auction_leakage(columns) -> None:
    bad = [c for c in columns if any(s in c.lower() for s in FORBIDDEN_SUBSTRINGS)]
    if bad:
        raise ValueError(f"same-auction / post-auction fields used as predictors: {bad}")


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel.sort_values(["auction_date", "tenor"]).copy()
    p["auction_date"] = pd.to_datetime(p["auction_date"])
    wide = p.pivot(index="auction_date", columns="tenor", values="y")  # keeps all-missing events
    wide = wide.reindex(columns=list(TENORS))
    prev = wide.shift(1)  # previous auction event, all tenors (known before this auction's bids)
    ev_dates = pd.Series(wide.index, index=wide.index)
    days_since = (ev_dates - ev_dates.shift(1)).dt.days

    rows = []
    for _, r in p.iterrows():
        d, t = r["auction_date"], int(r["tenor"])
        i = wide.index.get_loc(d)
        own = wide[t]
        y_lag1 = own.iloc[i - 1] if i >= 1 else np.nan
        y_lag2 = own.iloc[i - 2] if i >= 2 else np.nan
        y_lag3 = own.iloc[i - 3] if i >= 3 else np.nan
        rows.append({
            "y_lag1": y_lag1,
            "dy_lag1": y_lag1 - y_lag2,
            "dy_lag2": y_lag2 - y_lag3,
            "spread_364_91_lag1": prev.loc[d, 364] - prev.loc[d, 91],
            "spread_182_91_lag1": prev.loc[d, 182] - prev.loc[d, 91],
            "days_since_prev": days_since.loc[d],
        })
    f = pd.concat([p.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    f["t182"] = (f["tenor"] == 182).astype(float)
    f["t364"] = (f["tenor"] == 364).astype(float)
    f["dy"] = f["y"] - f["y_lag1"]
    # pre-bid ITT features of the target auction itself
    f["log_offer_tenor"] = np.log(f["offer_tenor"].astype(float))
    f["offer_share_tenor"] = f["offer_tenor"] / f["offer_total"]
    f = f.sort_values(["tenor", "auction_date"])
    f["offer_change_vs_prev"] = f.groupby("tenor")["log_offer_tenor"].diff()
    return f.sort_values(["auction_date", "tenor"]).reset_index(drop=True)
