# R04 evidence status

Updated 17 October 2026 from cloud session execution (branch `research/r04-cloud-phase-1`).

| Dimension | Status | Evidence |
|---|---|---|
| Data access (auction documents) | **VALIDATED** | 239/239 official BoU T-bill documents fetched (119 results, 120 Invitations to Tender; 33,812,254 bytes), SHA-256 in `data/manifests/bou_tbill_documents.csv` |
| Data access (macro: CBR, CPI, FX) | **HOLD_DATA** | No dated CBR decision history obtained (BoU page is a Power BI embed); UBOS host failed TLS verification twice; FX file is a current snapshot only |
| Target validity | **VALIDATED with flags** | 300 tenor-rows / 100 auctions (2022-01-05 → 2026-09-30). Printed money-market yield matches cut-off price under `(100/P−1)·365/nominal days` in 296/299 priced rows (after the declared `13..001` repair); the 3 failures are all in auction 1176; 1 `13..001` printed typo (2024-02-14); 1 not-awarded tenor (1203, 91-day) |
| Pre-bid timing | **PARTIAL** | ITT notices: 109 dated a plausible 1–14 days pre-auction (median 6), 3 timing violations, 5 implausible leads (year typos), 3 image-only. Results-PDF creation timestamps are ≥12.5 h after auction-day midnight (Kampala), i.e. after the 10:00 bid deadline |
| Method validity | **VALID for the tested scope** | Frozen protocol (`configs/experiment.yaml`, commit `3bf3cb3`) before any yield was parsed; forward expanding window, all tenors of an auction grouped |
| AI incremental value | **NEGATIVE** | See below |
| Scientific novelty | **Not established** | Competitor audit not performed in this phase (`docs/PRIOR_ART.md`) |
| Readiness | **NOT manuscript-ready** | |

## Publication decision: `NO_GO` for the pre-bid ML rescue (modelling result `NEGATIVE_MODEL`; macro arm `HOLD_DATA`)

Primary analysis (`repaired_typo`, 45 forward test auctions, 132 tenor-rows, 2024-01-03 → 2026-09-30):

| Model | MAE (pp) | Δ vs last yield | mean per-auction loss diff (pp) [95% block-bootstrap CI] |
|---|---|---|---|
| last observed tenor yield | **0.3369** | — | — |
| AR(1) per tenor | 0.3512 | +4.2% | +0.0146 [−0.0069, +0.0366] |
| ridge, lag + pre-bid ITT offers | 0.4251 | +26.2% | +0.0875 [+0.0086, +0.2285] |
| ridge, lag only (ablation) | 0.4234 | +25.7% | +0.0858 [+0.0085, +0.2250] |
| gradient boosting, lag + pre-bid offers | 0.3768 | +11.9% | +0.0410 [−0.0032, +0.0833] |

No pre-bid model met the frozen GO rule (≥5% MAE reduction and CI upper bound < 0). The verdict is identical in all four
declared source sensitivities (`results/tables/forward_metrics_all_sensitivities.csv`). Per the investigator's stop rule
this research branch stops here: no further algorithm search.

## Prior exploratory result (handoff) — status

Prior: 68 events, 44 test auctions / 132 tenor-rows, last-yield MAE 0.34374, AR(1) 0.37936, ridge 0.40193, boosting 0.47691.
**Not reproduced on identical inputs** (the prior row-level data are unavailable). This independent rebuild gives the
same qualitative ranking (last yield best; lag-only ML worse) at a similar scale (45 / 132), last-yield MAE 0.3369.
The prior `13..001` typo and the three auction-1176 identity anomalies **are reproduced** from the official PDFs.

## Runs

| Run | Code | Note |
|---|---|---|
| 1 | `eb66c2d` | first evaluation; 42 test auctions (ITT dates `January,03 2024` not parsed) |
| 2 (reported) | `ffa9c47` + docs | parser fix only (no model/rule change); 45 test auctions; same decision |
