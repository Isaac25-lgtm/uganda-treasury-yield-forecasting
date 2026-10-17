# Model card — evaluated and rejected (no model is promoted)

- **Task:** one-step forecast of BoU T-bill cut-off money-market yield (91/182/364 d) before the 10:00 bid deadline.
- **Data:** official BoU results and Invitation-to-Tender documents, auctions 2022-01-05 → 2026-09-30 (100 parsed).
- **Models evaluated:** last yield (benchmark), per-tenor AR(1), ridge (lag + ITT offers), ridge (lag only, ablation),
  HistGradientBoosting (lag + ITT offers; fixed hyperparameters). Refit 45 times (one per test auction); total fit time
  ≈ 10 s on 2 threads; training windows 35–79 auctions.
- **Outcome:** all challengers have higher MAE than the last observed yield (see `docs/STATUS.md`). **Rejected.**
- **Intended use:** methodological evidence only. **Not** for trading, pricing, investment or policy decisions.
- **Artifacts:** no model binaries are saved or distributed.
