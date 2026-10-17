# Limitations

- **Coverage gap.** 10 official results releases (2025-12-17 and 2026-02-11 → 2026-09-02) draw the results table as
  vector glyphs or images with no text layer; OCR was unavailable and values were not guessed. Two further 2026
  files are a garbled bond/bill overlay and an unrelated document. Only 3 auctions of 2026 are parsed. Forecasts for
  the auction following a gap use the last *parsed* yield, which a real forecaster would have had more recently.
- **No macro arm.** CBR decisions, CPI and FX with provable release dates were not obtained; the rescue tested only the
  Invitation-to-Tender offered amounts, which are almost piecewise constant (≈13 distinct offer vectors 2022–2026) and
  therefore carry little auction-to-auction information.
- **Small sample.** 45 forward test auctions; block-bootstrap CIs are wide and the 4-auction block length is a choice.
- **Post-metric parser fix.** One ITT date-format fix was made after the first metrics were seen (run 1 `eb66c2d`, 42
  test auctions → run 2, 45). No model, feature or decision rule changed; both runs give `NEGATIVE_MODEL`.
- **Ridge selection.** The inner CV chose the largest alpha (100) at every refit, i.e. shrinkage toward "no change";
  the grid was frozen and was not widened.
- **Exploratory sub-result, not a claim.** Gradient boosting had lower 91-day MAE than last yield (0.509 vs 0.562 pp,
  42 rows) but was worse overall; this was not a prespecified subgroup and is not interpreted.
- **Source anomalies** are preserved: `13..001` printed yield (2024-02-14), auction 1176 yields consistent with actual
  rather than nominal days (90/181/363), a 364-day maturity printed as 2024-02-29 (182 days) for 2023-08-30, an
  issue number printed as 1171 for the 1172 auction, ITT notice dates after the auction (1132, 1174) or on it (1184).
- **Prior results not reproduced on identical inputs** (prior row-level files unavailable in the cloud).
- No investment, trading or return claims are made or implied.
