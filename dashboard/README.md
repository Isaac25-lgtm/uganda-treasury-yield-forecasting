# R04 research dashboard

`streamlit run dashboard/app.py` — reads only `results/tables/*.csv` and `results/run_summary.json`; no training, no
raw documents. Sections: Overview → Data provenance → Study cohort → Baselines and models → Validation →
Sensitivity/limitations → Reproducibility. Smoke-tested by `tests/test_dashboard.py` (Streamlit AppTest).

**Not deployed.** A public deployment needs the investigator's explicit approval and their own Streamlit Community Cloud
login; no live URL exists.
