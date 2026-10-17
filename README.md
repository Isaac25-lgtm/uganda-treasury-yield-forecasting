# Uganda Treasury-bill pre-bid yield forecasts (R04)

Investigator: Isaac Omoding · Research programme R04 · Stage: **phase-1 bounded rescue, completed — branch stopped**

**Decision: `NO_GO` for the pre-bid ML rescue — modelling result `NEGATIVE_MODEL`; macro-predictor arm `HOLD_DATA`.**

Bank of Uganda (BoU) Treasury-bill auctions set short-term government borrowing costs every two weeks. An earlier
exploratory analysis found that lag-only machine learning did not beat the last observed auction yield. This phase asked
whether information that is *genuinely public before the 10:00 bid deadline* rescues the forecast. Under a protocol
frozen before any yield was parsed, it did not.

## Research question
Do pre-bid signals improve one-step forecasts of BoU T-bill **cut-off money-market yields** (91/182/364 days) beyond the
last observed same-tenor auction yield?

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
re-downloaded. All 9 committed result tables reproduced **exactly** (`results/reproduction/`). MAE/RMSE recomputed
from the committed forecasts confirm last-yield **0.33686 pp** as the best of the five model families.

**Dashboard.** `dashboard/app.py` is a full research dashboard.

**Deployment status: HOLD_DEPLOYMENT.** BoU's website terms allow downloading and copying "for User use" but
do not clearly allow public republication (`docs/DEPLOYMENT.md`). Prior art remains `UNVERIFIED` and needs a
direct competitor audit (`docs/PRIOR_ART.md`). No novelty is claimed.

## Reproduce
```bash
pip install -e ".[test,dashboard]"          # needs poppler-utils
PYTHONPATH=src python3 -m ugtbill.acquire --first-year 2022
OMP_NUM_THREADS=2 PYTHONPATH=src python3 -I scripts/run_pipeline.py
python3 -m pytest -q
PYTHONPATH=src python3 -I scripts/compare_reproduction.py <out-dir>   # compare a re-run with committed tables
pip install -r dashboard/requirements.txt && streamlit run dashboard/app.py   # local only; HOLD_DEPLOYMENT
```

## Repository map
`configs/experiment.yaml` (frozen protocol) · `src/ugtbill/` (acquire, parse, audit, features, evaluate) ·
`results/tables/` (public aggregate outputs) · `docs/` ([status](docs/STATUS.md), [protocol](docs/SCIENTIFIC_PROTOCOL.md),
[limitations](docs/LIMITATIONS.md), [decision log](docs/DECISION_LOG.md), [reproducibility](docs/REPRODUCIBILITY.md)) ·
`dashboard/` · [`AGENTS.md`](AGENTS.md) (execution contract).

## Next step
None for modelling. Re-open only if dated official CBR/CPI/FX release histories become available, and then under a new
frozen protocol. A competitor audit is required before any write-up of the negative result.

*AI assistance:* code, analysis and documentation were produced with an AI coding assistant (Claude Code) under the
investigator's instructions; every number above comes from the committed pipeline outputs.
