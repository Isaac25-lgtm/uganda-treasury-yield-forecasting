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
