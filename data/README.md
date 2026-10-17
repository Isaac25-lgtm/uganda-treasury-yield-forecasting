# Data — acquisition and permission matrix

| Data | Source | Status | In Git? |
|---|---|---|---|
| BoU T-bill results releases 2022–2026 | `https://bou.or.ug/uploads/…` via the BoU auction-information CMS listing | fetched, hashed | **No** (`data/raw/`, git-ignored) |
| BoU T-bill Invitations to Tender 2022–2026 | same | fetched, hashed | **No** |
| Download manifest (URL, bytes, SHA-256, HTTP status, attempts) | generated | — | yes: `manifests/bou_tbill_documents.csv` |
| CBR decisions, UBOS CPI, BoU FX history | — | HOLD_DATA (see `docs/DATA_ACCESS.md`) | — |

Re-create raw data with `PYTHONPATH=src python3 -m ugtbill.acquire --first-year 2022`. In the manifest, `attempts=0`
means the file was verified from the local cache during a rerun. Processed row-level intermediates go to
`data/processed/` (git-ignored). No synthetic data is mixed with observed data; test fixtures live in `tests/` and are
labelled synthetic. No credentials or restricted data are used.
