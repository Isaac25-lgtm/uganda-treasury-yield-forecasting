# Scientific protocol — R04 phase 1 (bounded pre-bid rescue)

Machine-readable, frozen version: [`configs/experiment.yaml`](../configs/experiment.yaml), committed at `3bf3cb3`
before any results table was parsed or any metric computed.

**Question.** Does information that is genuinely public before the 10:00 bid deadline improve one-step forecasts of
Bank of Uganda Treasury-bill cut-off yields beyond the last observed same-tenor auction yield?

**Estimand / target.** Printed *money-market yield* at the cut-off price, % p.a., per tenor (91, 182, 364 days), per
scheduled auction. Verified convention: `y = (100/P − 1) · 365 / nominal_days · 100`. Weighted-average yields,
discount rates, effective yields, bonds and secondary-market rates are excluded.

**Unit and dependence.** Auction event (date + printed issue number). Tenors of one auction are evaluated together and
resampled together.

**Information set at the forecast origin.** (i) results of strictly earlier auctions; (ii) the target auction's own
Invitation to Tender (per-tenor offered amounts), only when its printed notice date is 1–14 days before the auction;
(iii)–(iv) CBR and macro releases only with a documented pre-auction release date — *none obtained in this phase*.
Forbidden: same-auction bids, tendered/accepted amounts, cover ratios, cut-off/weighted prices or yields, later revisions.
Enforced in code (`features.assert_no_same_auction_leakage`) and tests.

**Design.** Expanding window, refit before every test auction; first test auction on/after 2024-01-01; ≥20 training
auctions. Models (no others permitted): last yield; per-tenor AR(1) (OLS); ridge on Δy (alpha by inner forward CV over
{0.1, 1, 10, 100}); one nonlinear model (HistGradientBoosting, fixed depth 2, lr 0.05, 200 iterations, min leaf 10);
lag-only ridge as an ablation.

**Metrics.** Primary MAE (pp) on identical test rows; secondary RMSE and directional accuracy. Uncertainty: per-auction
loss differential vs last yield, 95% moving-block bootstrap (block 4 auctions, 2000 replicates, seed 20261017).

**Decision rule.** GO (CONDITIONAL) only if a pre-bid model reduces MAE ≥5% *and* the CI upper bound is < 0 *and* every
feature has documented timing. Otherwise NEGATIVE_MODEL (timing valid, no gain) or HOLD_DATA (timing unverified); stop.

**Declared sensitivities.** `as_printed` (unparseable printed values left missing), `repaired_typo` (primary; `13..001`
→ 13.001, verified by the price identity), `drop_1176`, `drop_identity_flags`.
