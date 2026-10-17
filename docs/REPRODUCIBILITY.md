# Reproducibility

Environment used: Linux cloud container, Python 3.13.16, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1, pytest 9.1.1,
streamlit 1.66.0, poppler `pdftotext` 24.02.0; 4 cores available, runs limited to 2 threads.

```bash
pip install -e ".[test]"                     # + ".[dashboard]" for the app; requires poppler-utils (pdftotext, pdfinfo)
PYTHONPATH=src python3 -m ugtbill.acquire --first-year 2022   # ~8 min; writes data/raw/ (git-ignored) + manifest
OMP_NUM_THREADS=2 PYTHONPATH=src python3 -I scripts/run_pipeline.py   # ~50 s; writes results/tables + results/run_summary.json
OMP_NUM_THREADS=2 python3 -m pytest -q
streamlit run dashboard/app.py
```

Verify raw inputs against `data/manifests/bou_tbill_documents.csv` (`sha256sum data/raw/bou/docs/*`). The BoU CMS
catalogue may change; the catalogue used has SHA-256
`0f7cf2a1705dd880e1178f584247ae62daf53ae2f6e1a9e9063508d864829302` (pass `--fetch-catalog` to refresh it).

Seed 20261017 (bootstrap and gradient boosting). Splits and models: `configs/experiment.yaml`. Per-refit registry:
`results/tables/model_registry_primary.csv`. CI runs only fixture tests (no downloads, no retraining).

## Verified reproduction (2026-10-17)

Run against the cached raw documents; the pipeline refuses to run if any are missing or altered:

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONPATH=src python3 -I scripts/run_pipeline.py --out-dir <scratch>   # 60 s
PYTHONPATH=src python3 -I scripts/compare_reproduction.py <scratch> --write results/reproduction                # 9/9 EXACT
```

Python 3.11 check: a clean venv with Python 3.11.17, numpy 2.4.6, pandas 3.0.6, scikit-learn 1.9.1,
streamlit 1.66.0 and altair 6.3.0, installed as CI does (`pip install -e ".[test]" -r dashboard/requirements.txt`):
`R04_REQUIRE_DASHBOARD=1 pytest -q` → 45 passed. The same suite also passes on Python 3.13.16.
Dashboard: `streamlit run dashboard/app.py` (reads `results/` only; `R04_RESULTS_DIR` overrides).
