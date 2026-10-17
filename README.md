# Uganda Treasury-bill pre-bid yield forecasts (R04)

[![ci](https://github.com/Isaac25-lgtm/uganda-treasury-yield-forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/Isaac25-lgtm/uganda-treasury-yield-forecasting/actions/workflows/ci.yml)

Investigator: Isaac Omoding · Research programme R04 · Stage: **phase-1 bounded rescue, completed — branch stopped**

**Decision: `NO_GO` for the pre-bid ML rescue — modelling result `NEGATIVE_MODEL`; macro-predictor arm `HOLD_DATA`.**

Bank of Uganda (BoU) Treasury-bill auctions set short-term government borrowing costs every two weeks. An earlier
exploratory analysis found that lag-only machine learning did not beat the last observed auction yield. This phase asked
whether information that is *genuinely public before the 10:00 bid deadline* rescues the forecast. Under a protocol
frozen before any yield was parsed, it did not.

## Research question
Do pre-bid signals improve one-step forecasts of BoU T-bill **cut-off money-market yields** (91/182/364 days) beyond the
last observed same-tenor auction yield?

## Research gap and scope
The bounded question is whether dated, pre-bid offered amounts add useful information beyond yield history on an identical forward test cohort. It does not establish novelty: the competitor audit remains unverified. The protocol was frozen at `3bf3cb3` before parsing yields; no additional algorithm search followed the negative result.

## What was done (all from official public BoU documents)
- Located BoU's CMS catalogue and downloaded **239/239** T-bill documents 2022→Oct 2026 (119 results releases, 120
  Invitations to Tender; 33.8 MB), each SHA-256-hashed; raw files kept out of Git.
- Parsed **100 auctions / 300 tenor-rows** (2022-01-05 → 2026-09-30). Verified the printed yield convention
  `(100/P − 1)·365/nominal days` (296/299 priced rows).
- Reproduced the two documented source anomalies from the PDFs: printed `13..001` (2024-02-14, 364-day) and auction
  **1176**, whose three yields match *actual* days to maturity (90/181/363) instead of nominal tenor days. Both are kept
  as declared sensitivities, never silently fixed.
- Audited pre-bid timing: ITT notices are dated a median 6 days before the auction (109 verified; 3 dated on/after
  the auction and 5 with year typos were excluded as unverified).
- Forward, auction-grouped evaluation (expanding window, refit before each of 45 test auctions, 2024-01-03 → 2026-09-30).

## Dataset, inclusion and preprocessing
Source: official [Bank of Uganda](https://www.bou.or.ug/) auction results and Invitations to Tender, acquired 17 October 2026. The [document manifest](data/manifests/bou_tbill_documents.csv) records URLs, bytes and SHA-256; [document status](results/tables/results_document_status.csv) preserves unsuccessful parses.

- Include Treasury-bill cut-off money-market yields for 91/182/364-day tenors. Exclude bonds, weighted-average yields, discount/effective rates and secondary-market rates.
- Parse immutable PDF/DOCX inputs; retain printed fields alongside the primary repaired values. Audit the price identity within 0.02 pp and deduplicate auction-date/tenor records, recording conflicting duplicates.
- Use target-auction offered amounts only from notices dated 1–14 days before the auction. Same-auction bids, cover ratios, accepted amounts and outcome prices/yields are forbidden predictors.
- Construct lagged yields/changes, lagged tenor spreads, elapsed days and tenor indicators from earlier auctions; pre-bid features are log offered amount, its change and tenor share. Rows missing any required feature or target are excluded for **every** model alike.
- At least 20 earlier training auctions are required. Test dates start on/after 1 January 2024; the final primary sample is 45 auctions and 132 tenor-rows (91-day: 42; 182-day: 45; 364-day: 45).
- The calendar reconstruction has 117 auctions through the cutoff: 100 parsed, 10 image-only and 7 with no T-bill results table located. The 10 April 2024 notice corresponds to results dated 11 April, rather than an extra missing auction. Gaps remain missing; no zero filling or interpolation is used.

## Experimental design and uncertainty
Before each test auction, refit using strictly earlier auctions in an expanding window. Compare last observed same-tenor yield, per-tenor AR(1), standardized ridge predicting yield changes with and without pre-bid offers, and fixed HistGradientBoosting (depth 2, learning rate 0.05, 200 iterations, minimum leaf 10). Ridge alpha is selected from {0.1, 1, 10, 100} using an inner forward split restricted to the training window.

Primary error is MAE in percentage points; RMSE is secondary. Confidence intervals concern the **per-auction mean absolute-loss difference**, with all tenors grouped together: moving-block percentile bootstrap, block length 4 auctions, 2,000 replicates, seed 20261017. They are not prediction intervals. The prespecified GO rule required at least 5% MAE improvement, an upper CI below zero and verified predictor timing; no challenger passed. [Protocol](docs/SCIENTIFIC_PROTOCOL.md) · [frozen configuration](configs/experiment.yaml).

## Results (primary analysis, 45 test auctions / 132 tenor-rows)

| Model | MAE (pp) | vs last yield | per-auction loss diff [95% block-bootstrap CI] |
|---|---|---|---|
| **Last observed tenor yield** | **0.337** | — | — |
| AR(1) per tenor | 0.351 | +4.2% | +0.015 [−0.007, +0.037] |
| Ridge, lag + pre-bid offers | 0.425 | +26.2% | +0.088 [+0.009, +0.229] |
| Ridge, lag only (ablation) | 0.423 | +25.7% | +0.086 [+0.009, +0.225] |
| Gradient boosting, lag + pre-bid offers | 0.377 | +11.9% | +0.041 [−0.003, +0.083] |

Positive differences mean *worse* than the last yield. Same verdict under all four source sensitivities
(`results/tables/forward_metrics_all_sensitivities.csv`). The prior handoff figures (last-yield 0.34374 vs boosting
0.47691 on 44 test auctions) were **not reproduced on identical inputs**; this independent rebuild agrees qualitatively.

## What is not claimed
No pre-bid gain; no macro (CBR/CPI/FX) test — their release chronology was not obtained; no novelty claim (competitor
audit pending); no investment, trading or return implications.

## Data access status
Validated: BoU auction documents. Blocked/HOLD: dated CBR decisions (Power BI only), UBOS CPI (TLS failure, not
bypassed), FX history. 10 results releases from Dec-2025 to Sep-2026 have no text layer and are reported missing.
Details: [`docs/DATA_ACCESS.md`](docs/DATA_ACCESS.md).

## Reproduction and presentation (17 Oct 2026)

**Reproduction.** An independent re-run used 239/239 checksum-valid cached BoU documents, with nothing
re-downloaded. All 9 committed result tables reproduced **exactly, excluding wall-clock fitting time** (`results/reproduction/`). MAE/RMSE recomputed
from the committed forecasts confirm last-yield **0.33686 pp** as the best of the five model families.

**Dashboard.** The existing `dashboard/app.py` now presents observed auction series, forecasts from all five families, observed-versus-predicted panels, error distributions, per-auction loss differences and confidence intervals, all four source sensitivities, coverage, pre-bid timing, limitations and aggregate CSV downloads. Charts preserve gaps and source anomalies. It reads committed results only: no acquisition or training at startup.

**Verification.** **45 tests passed** on both Python 3.13 and a clean Python 3.11 environment. Tests recompute MAE/RMSE from committed forecasts, check cohort/decision consistency, require clear missing-input failures, and exercise every dashboard section and download. [Verified CI run](https://github.com/Isaac25-lgtm/uganda-treasury-yield-forecasting/actions/runs/39068529540). Raw-data reproduction is a separate cloud execution, not a claim made by these CI checks.

**Deployment status: HOLD_DEPLOYMENT.** BoU's website terms allow downloading and copying "for User use" but
do not clearly allow public republication (`docs/DEPLOYMENT.md`). Prior art remains `UNVERIFIED` and needs a
direct competitor audit (`docs/PRIOR_ART.md`). No novelty is claimed.

## Reproduce
```bash
pip install -e ".[test,dashboard]"          # needs poppler-utils
PYTHONPATH=src python3 -m ugtbill.acquire --first-year 2022
OMP_NUM_THREADS=2 PYTHONPATH=src python3 -I scripts/run_pipeline.py --out-dir /tmp/r04-reproduction
PYTHONPATH=src python3 -I scripts/compare_reproduction.py /tmp/r04-reproduction
python3 -m pytest -q
pip install -r dashboard/requirements.txt && streamlit run dashboard/app.py   # local only; HOLD_DEPLOYMENT
```

## Repository map
`configs/experiment.yaml` (frozen protocol) · `src/ugtbill/` (acquire, parse, audit, features, evaluate) ·
`results/tables/` (public aggregate outputs) · `docs/` ([status](docs/STATUS.md), [protocol](docs/SCIENTIFIC_PROTOCOL.md),
[limitations](docs/LIMITATIONS.md), [decision log](docs/DECISION_LOG.md), [reproducibility](docs/REPRODUCIBILITY.md)) ·
`dashboard/` · [`AGENTS.md`](AGENTS.md) (execution contract).

## Scientific limitations
The study is retrospective. Printed notice dates and PDF metadata are timing evidence, not server-side publication logs. Missing releases can make the last parsed yield older than the yield available to an actual forecaster. There are only 45 test auctions; within-auction tenors are dependent and bootstrap conclusions depend on the declared block design. Macro release histories were not obtained, the prior pilot was not exactly replicated, and no prospective performance or financial-return claim is justified.

The primary typo repair and exclusion of auction 1176/identity-flagged rows are all reported as declared sensitivities, with the negative conclusion retained. Missing 2025–26 releases and the competitor audit remain research gaps; dashboard completeness does not resolve them.

## Next step
None for modelling. Re-open only if dated official CBR/CPI/FX release histories become available, and then under a new
frozen protocol. A competitor audit is required before any write-up of the negative result.

*AI assistance:* code, analysis and documentation were produced with an AI coding assistant (Claude Code) under the
investigator's instructions; every number above comes from the committed pipeline outputs.
