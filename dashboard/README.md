# R04 research dashboard

`pip install -r dashboard/requirements.txt && streamlit run dashboard/app.py`

The app reads only the committed aggregate tables in `results/` (`dashboard/r04_data.py`). It never downloads
sources, parses documents or trains models.

**Sections:**
- Overview
- Data provenance
- Observed yields: 91/182/364-day series, with missing auctions shown as breaks and source anomalies marked
- Cohort and pre-bid timing
- Forecasts vs observed: all five model families, a timeline and faceted scatter plots
- Errors and loss differences: MAE/RMSE, MAE by tenor, error distributions, per-auction loss differences with
  the block-bootstrap CI
- Sensitivities: all four
- Limitations
- Reproducibility and deployment

Every page carries the context ribbon (run, code, cutoff, observed data not simulated, NEGATIVE_MODEL, not advice).
Every chart has hover tooltips, units, a table view and an allowlisted CSV download.

**Colours:** model and tenor colours use a validated categorical palette on a pinned light theme. Tenors also get
distinct point shapes as a colour-blind-safe secondary cue.

**Tests:** `tests/test_dashboard.py` (AppTest) covers every section, every widget, the download names, and a clear
failure when results are missing.

**Deployment: HOLD_DEPLOYMENT** (see `docs/DEPLOYMENT.md`). Nothing is deployed.
