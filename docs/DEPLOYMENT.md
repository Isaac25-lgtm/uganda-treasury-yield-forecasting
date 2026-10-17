# Deployment gate — **HOLD_DEPLOYMENT** (coordinator review required)

**Decision (2026-10-17): HOLD_DEPLOYMENT.** The dashboard is technically ready and public-safe by construction,
but the Bank of Uganda terms do not clearly grant public republication. A coordinator (and, if needed, BoU)
must decide before any public Streamlit deployment. No deployment was attempted.

## Evidence (1 targeted request of the 3 allowed)
- Official terms read in full through the same CMS route the BoU terms page uses:
  `https://bou.or.ug/api/terms-and-condition?populate=heroSection.image&populate=terms`. HTTP 200, 5,229 bytes,
  SHA-256 `3fc4fc633f01ad266f6d3460b2bf18c1fc5c9582c6abf926fc9cf7d258cc2289`, CMS `updatedAt` 2026-06-16.
  The raw file is kept git-ignored.
- **Clause 1:** BoU allows Users to "download and copy the information, documents and materials … from the Site
  **for User use** subject to the terms and conditions … and also subject to more specific restrictions that may
  apply to specific material".
  - This permits download and copying for the user's own use.
  - It does **not** expressly permit public redistribution or republication.
  - No open licence (e.g. Creative Commons) is stated, and none is invented here.
- **Clauses 3, 5–6:** no warranty, no liability, and the user indemnifies BoU.
- **Clause 7:** nothing on the Site constitutes an investment recommendation.
- **Clause 8:** third-party copyrighted material needs permission from its source.
- **Document-specific terms:** a local scan of all 239 downloaded documents found no copyright, licence or reuse
  notice. Results documents are titled "PRESS RELEASE" and ITTs say "This advertisement is also available on Bank
  of Uganda's web site", which points to intended public dissemination. That is context, not a licence.

## Allowlist (what the app would publish if cleared)
- **Tier A — the project's own derived results.** Forecasts, errors, MAE/RMSE, bootstrap CIs, inclusion counts,
  timing classifications, reproduction matrix. Lowest risk.
- **Tier B — reproduces printed BoU statistics.** Cut-off prices and yields, offered amounts, printed dates,
  document file names, URLs and hashes. These are factual public auction aggregates, but republication is the
  open question above.
- **Never published:**
  - raw PDF/DOCX files;
  - individual bids or bidder/participant data (none exists in this project);
  - local paths, secrets or tracebacks (`showErrorDetails = "none"`);
  - any model binary.

Downloads are restricted in code to `r04_data.DOWNLOADABLE_TABLES` plus derived `r04_*.csv` chart data. A column
and path guard is enforced (`safe_download_frame`), and tests exercise it.

## If cleared
- Entry point: `dashboard/app.py`.
- Requirements: `dashboard/requirements.txt`.
- Config: `.streamlit/config.toml` (light theme, no error details, no uploads).
- Attribution on every page: "Bank of Uganda auction statistics; analysis by R04 (research). Not investment
  advice", plus a no-endorsement note.
- The app never downloads sources or trains models at runtime.

A conservative alternative is a Tier-A-only deployment; it would need a small code flag that is not built yet.
