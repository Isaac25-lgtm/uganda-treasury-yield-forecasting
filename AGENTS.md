# R04 — Scientific execution contract

Repository: Isaac25-lgtm/uganda-treasury-yield-forecasting

The investigator authorised ordinary reversible cloud execution, lawful public-data processing and reviewable branch/PR creation. No purchases, overages, new paid API calls, raw restricted data publication, public deployment or automatic merges. Use only this repository. All earlier figures below are reported exploratory evidence until independently reproduced.

Read this entire file before coding. Execute real source checks, code and tests; a plan is not an empirical result. Use an available low-cost model and cloud CPU. First phase is bounded: up to 10 minutes of active execution, no more than 3 source attempts per host, 2 CPU threads, no broad hyperparameter search. The programme has $64 included promotional credit verified 17 October 2026; 8 USD is only a planning envelope, not an enforceable cap. Never purchase or enable overages. Return a concrete checkpoint with exact commands, outputs, Git SHA and PR state. If you cannot read billing, say so. Do not assume credit remains after a long run.

Branch: research/r04-cloud-phase-1 (or platform-required claude branch if pushing research/* is restricted; report exact branch). This bootstrap branch contains no experiments yet. Keep main unchanged after bootstrap and leave PRs unmerged.


# E. AUTHORITATIVE SCIENTIFIC CONTEXT — DO NOT REINVENT THE HISTORY

The earlier Feasibility Lab evaluated 18 canonical directions, then agriculture; the October 17 briefing distinguishes **23 distinct questions, 8 new empirical investigations, 0 cleared for full-study protocol**, and one exploratory ML result. Previous source files remained in a Windows directory `F:\MY FILES\DATA SCIENCE\PUBLISHING\TESTS\publication_feasibility_lab`; **Cloud Sessions cannot access that path**. Another handoff ZIP omitted row-level source data and may lack some actual modelling input. Prior source names and results are given here to help reconstruct and compare, not to assert the raw inputs have been imported or independently verified.

**Research-selection ethos:** Work on consequential scientific questions with meaningful gaps compared against *closest published, preprinted, protocol and exact-data competition*. Mere use of Uganda, new model family, newest dataset upload, attractive AUROC, or fancy interactive dashboard cannot establish novelty. Keep both advanced ML successes and model failures. A negative scientifically meaningful result can be publishable, but no conclusion is guaranteed.

## E1. The 12 non-negotiable publication gates

1. Consequential and clearly defined scientific problem.
2. Closest prior studies, including same dataset, same question elsewhere, preprints, theses, code/commercial analyses.
3. **Substantial, specific** advance rather than model substitution or geography substitution.
4. Data provenance and true observation dates; prefer recent valid *observations*, not merely 2026 upload.
5. Lawful, reproducible data access with explicit licenses and necessary approvals.
6. Correct target/estimand and valid numerator/denominator.
7. Predictors legitimately known **before** prediction or intervention; no leakage.
8. Strong rule-based, historical and statistical/econometric baselines.
9. Real temporal, geographic and/or provider external validation; cluster-dependent uncertainty.
10. Decision value at a realistic capacity or a clear new methodological/causal conclusion.
11. Reproducibility: source hashes, versioned code, seed, splits, code/data dictionaries, missingness, uncertainty.
12. Appropriate scientific claims/publication form, even when advanced AI loses.

Do not translate a 100-point analyst rubric directly into acceptance probability or completion percentage. Use separate statuses for *data access*, *method validity*, *scientific novelty*, *AI incremental value*, *readiness*. Fatal invalid outcomes and causal-timing violations trump point totals.

## E2. Latest evidence ledger (prior reported, not newly reproduced)

| ID | Key earlier finding | Crucial limitation |
|---|---|---|
| R01/N2 | 204,469 post-2016 RPW rows; temporal quote evaluation on 18,030 matched origin records / 326 corridors; gradient boosting Brier **0.136037**, spline-logistic **0.144145**, corridor-history **0.144422**; ~5.6% lower Brier vs spline; at 20% review capacity 1,351 observed failures vs 1,129 for spline | Test periods already inspected; public *release timing* unknown; target **conditional on quote reobservation**; missing/renamed services and provider dependence |
| R02/N1 | 5/108 strict threshold-alert classifications changed between WHO vintages across 64 countries, 103 stable; a 3-percentage-point deferral buffer avoids all 5 retrospectively while deferring 17 decisions | Small/unbalanced vintages; some archive commits 105–135 days after H1 end; revision reference not underlying TB incidence; buffer selected after inspection; delay costs unmeasured |
| R03/H1 | Rwanda DHS 2019–20 planned for development; Rwanda 2025 for temporal testing, Uganda/Kenya/Ethiopia potential geographic validation | No approved respondent-level dyad microdata in earlier workspace; pre-discharge care not post-discharge return; outcome and predictor harmonization unverified |
| R04/K1 | 68 recovered auctions in repaired sensitivity; 44 test auctions, 132 tenor rows; last-yield MAE **0.34374** percentage points vs AR(1) **0.37936**, ridge **0.40193**, gradient boosting **0.47691** | Lag-only advanced ML lost; yields have documented source typos and one unresolved price/yield inconsistency; true as-of pre-bid macro predictors not yet tested |
| R05/N3 | iHEART-SA public file has **25,128 rows**; of 2,175 released baseline-controlled rows, 628 measured high, 717 controlled, **830 unknown** follow-up BP; 22,973 reconstructed records vs published 23,855 participants | Source lacks participant/clinic/date keys and any-transition history; cannot claim original reported effects wrong or reproduce adjusted models |
| R06/AG1 | GROW 64.6 MB archive inspected: 29,872 Uganda LSMS survey rows across sources, 300 Uganda points, 9,687 Uganda regional rows; *zero Uganda crop-cut rows*; agricultural observations mostly historical | New upload ≠ fresh farm outcome; no independent contemporary shortfall labels and no valid forecast yet; aquaculture data at district level, not farm productivity |

**Related records if user supplies them:** `RESEARCH_EXECUTION_BRIEFING_2026-10-17.md`, `Research_Execution_Health_Finance_Agriculture_2026-10-17.zip`, `START_HERE_RESEARCH_HANDOFF_2026-10-17.md`, `Research_Handoff_Rebuilt_2026-10-17.zip`, `Codex_Remittance_AI_Full_Data_Processing_Modelling_Protocol_2026-10-17.md`. These are useful **reference evidence, not guarantees that each file is attached to this Work task**. Do not spend a full session searching the nonexistent F: drive. Re-download lawful public inputs from official sources and record any blocked source.

---

# F. COMMON REPOSITORY ENGINEERING CONTRACT

Implement the following structure in **each repo**, adjusted for actual scientific needs. Do not add empty placeholder code that is claimed runnable, do not overwrite existing useful project work, and do not commit huge data. Keep branches and PRs separate.

```text
<repo>/
  README.md                       # high-quality scientifically honest project entry
  AGENTS.md                       # authoritative per-project operating instructions
  pyproject.toml                  # pinned/controlled install and optional extras
  .python-version                # optional, supported Python version
  .gitignore                     # no credentials, raw restricted data, caches, binaries
  .env.example                   # NAMES only, never credential values
  .github/workflows/ci.yml       # LIGHT lint/tests, not downloading/retraining datasets
  data/
    README.md                     # acquisition/licensing/permission matrix
    samples/                      # only safe synthetic examples clearly marked
  configs/
    experiment.yaml               # source versions, task, outputs, seed, splits
  docs/
    STATUS.md                     # evidence-specific outcomes and blockers
    SCIENTIFIC_PROTOCOL.md        # aims, estimands, cohort, target, timing, stats
    PRIOR_ART.md                  # closest study, exact overlap, confirmed DOI/URL
    DATA_DICTIONARY.md            # actual observed variables after audit
    DATA_ACCESS.md                # what was genuinely fetched vs catalogued
    MODEL_CARD.md                 # ONLY after a real model exists
    REPRODUCIBILITY.md            # execution commands and restrictions
    LIMITATIONS.md
    DECISION_LOG.md
  src/<unique_package>/
    acquire.py                    # lawful source fetch and checksum if feasible
    audit.py                      # schema, missingness, duplicate/units verification
    preprocess.py                 # immutable raw -> cleaned/provenance
    features.py                   # split-safe features, availability timestamps
    baselines.py                  # primary simple challengers
    train.py                      # conditional, task-appropriate modelling
    evaluate.py                   # dependent data / original estimand metrics
    figures.py                    # source-grounded plots
  scripts/                         # smoke and full pipeline commands
  tests/                           # fixture-based leakage, schema, source, metric tests
  experiments/                     # prespecified experiments with recorded outcomes
  results/
    README.md                      # safe, small, aggregate output summary
    tables/                        # publication figures/metrics as safe csv/md
    figures/                       # accessible and print-ready exported images
  dashboard/
    app.py                         # optional precomputed/public-safe Streamlit
    README.md
  manuscript/
    README.md                      # proposal/status only, no premature claims
```

**Root-level README quality** (for each): concise title, investigator/research stage, compelling 2–4 sentence problem and importance, specific research questions, what is known and not claimed, official data sources and time coverage, current validated/blocked data access, design and baselines, status of experiments with real numbers and labels, uncertainty, results figures, reproducibility commands, risks and research next step, dashboard link **only after verified real deployment**, citation/acknowledgments, disclosure of AI assistance if required by eventual journal. No fake badges, fake CI green icons, invented dates/results/DOIs, or 'publication ready' labels.

**Scientific integrity:** do not convert hypothetical examples, synthetic tests or archived aggregate outputs into real observed training data. Keep observed vs estimated/imputed distinct. Files identified by SHA256 when available. Preserve both old negative results and corrected source anomalies. Report the exact independent sampling unit and group, not mere row count. Use prespecified primary metric and report honest uncertainty; later explorations labelled secondary/exploratory. Do not leak private participant or site details through app logs, screenshots, result CSV or README.

**Pipeline details:**

1. Log `as_of` timestamps, data source/URL, license, first/last observed period, release/commit timestamp when provable, file SHA, raw schema, manifest and code commit.
2. Never quietly trim missing data: report inclusion/exclusion flow, NA by variable and outcome, duplicate logic, key collisions and coverage loss.
3. Freeze estimand, split unit, time origins, baseline families and primary utility metric **before** viewing new metrics. Already seen 2022–24 R01 and previous Treasury windows remain retrospective exploratory, not an untouched external set.
4. Fit imputers/encoders/scalers/feature selection/calibrators **inside training folds only**. Guard time and geographic leakage. Nested selection when genuinely needed; do not overfit unlimited model trials.
5. Compare identical test records, with grouped/blocked uncertainty. For continuous outcomes MAE/RMSE/skill; classification Brier/log loss, calibration, AUROC/AUPRC appropriately, resource-constrained utility; audit any reliance on shared provider/country/time.
6. Appropriate and limited explainability: coefficients, partial effects, SHAP/permutation importance only when method and dependence support interpretation; **not causal feature effects**.
7. Model registry includes code/source hash, hyperparameters, fold times, processing time, training/sample counts, metrics CI, artifact size, dataset license and reason to promote/reject.
8. Record failed experiments, data access failures, bottlenecks and reproducibility instructions. Don't delete failure logs to 'clean' final deliverables.

**CI**: Python 3.11 or another supported version verified in environment; `pytest` fixture tests; formatting/lint if already supported; limit runtime to minutes; never run 200MB downloads, expensive model fit, web scraping or API calls automatically on GitHub CI. `.gitignore` must protect `.venv/`, `.env`, `*.pem`, `secrets.toml`, `data/raw/`, `data/restricted/`, `data/processed/`, checkpoints, clinical participant files, large xlsx/parquet, credentials, cached models and any proprietary licensed input. Do not use Git LFS as a back door for restricted raw data.

**Manuscript boundary:** Each project should be reproducible and research ready where feasible, but do NOT generate a false 'full paper with results' for blocked projects. A project can end honestly with `HOLD_ACCESS`, `REDESIGN`, `NEGATIVE_MODEL`, `RESERVE`, or `CONDITIONAL`.

---


# J. PROJECT R04 — UGANDA TREASURY BILL PRE-AUCTION YIELD RESEARCH

**Repo:** `uganda-treasury-yield-forecasting`  
**Working title:** *Do Truly Pre-Bid Signals Improve Uganda Treasury-Bill Auction Yield Forecasts Beyond the Last Observed Auction?*

**Target:** appropriate money-market yield associated with cutoff-price auction table, **by 91/182/364-day tenor and scheduled auction**. Do not silently mix weighted average yield, stop-out/cutoff, price-equivalent yields, secondary-market bonds and face-value allotment. Tenors in same event are dependent.

**Prior source reconstruction:** parsed 68 distinct 2023–June 2026 event dates in documented source-repair sensitivity, one printed typo `13..001` confirmed via 364d cutoff price and one further auction (1176) has 3 price/yield identity anomalies. Last-yield baseline MAE 0.34374 percentage points versus boosting 0.47691. These estimates are inspected and negative for lag-only ML.

**Primary task is ONE bounded rescue**:

1. Reconstruct clean source event registry from official Bank of Uganda auction result PDFs; explicit unique event key date + auction number, document URL/hash, tenor, posted yield, cutoff price, maturity/day count and rate convention; visual/reliable source audit for inconsistencies, with untouched originals and predeclared corrected/excluded sensitivities.
2. Verify BoU/UBOS/MoFPED/public macro indicators: CBR and announcement time, monthly inflation CPI actual release date, FX rates by published date, liquidity and secondary-market signals if legitimately public **before bid close**. Never use same-auction bids, allotments, cover ratios, accepted-yield or later CPI revisions as pre-bid predictors.
3. Count genuinely independent chronological auctions and complete pre-bid feature history. Holdout forward by auction (all tenors grouped); expanding windows and macro release delay features.
4. Fit last observed tenor yield, tenor AR(1), ridge/econometric model, and at most one carefully tuned nonlinear ML model. Primary MAE, secondary RMSE, optional directional performance, paired block-auction uncertainty and evidence of forecast value beyond history. Show sensitivity of tiny series to source revisions and regime changes.
5. Make GO/NO-GO decision: if release chronology unprovable or meaningful incremental gain not credible, terminate modelling, preserve dataset audit and negative result without another algorithm search.

**Prior art:** IMF Uganda 2026 government yield-curve analysis, Nelson–Siegel/Diebold–Li, Uganda dissertation and rate-transmission studies. New research must differentiate auction-cutoff *pre-bid forecast* from contemporaneous explanatory yield regressions. Don't compare published metrics across different targets as if head-to-head.

**Presentation:** historical official auction series, yield/price reconciliation flags, forecast-origin timeline, honest error comparison and interactive tenors. Do not offer financial advice or promise investment returns.

---


# M. MANUSCRIPT RESEARCH CONTROLS — LITERATURE AND SCIENTIFIC QUALITY

For each R01–R06, conduct a **direct competitor audit**, not a pasted generic bibliography:

- Locate the 5–10 **closest** works wherever realistically available: peer-reviewed, preprint, protocol, dissertation, exact-data GitHub implementation, institutional/official analysis and commercially published work. No invented DOI/year/claim.
- Capture author, date, title, DOI or stable URL, journal/venue, observations years, location, outcome, actual predictor timing, validation split, models, principal results and crucial limitations **verified in source**. Label depth `FULL_TEXT`, `ABSTRACT`, `REPOSITORY`, `CATALOGUE_ONLY`, `UNVERIFIED`.
- Two head-to-head competitors required: (1) closest work using the same dataset/source and (2) closest conceptual/same-question work elsewhere. Show precisely what new knowledge our experimental finding would establish and what result would falsify it.
- **Do not equate a model winning on different data with improving on a published model**. Direct 'beats literature' claims require comparable target and evaluation or independent reimplementation.
- For validated clinical predictive modelling, follow TRIPOD+AI transparent reporting and PROBAST+AI risk-of-bias thinking; for survey cross-country work account for sample design; for causal fuel reforms do not import prediction metrics as causal evidence.
- Respect protected/missing data, sample imbalance, population denominators, site clustering, reporting lags, hidden subgroup harms and policy uncertainty.

Publication decisions in `docs/STATUS.md` should use `{GO_FOR_FULL_STUDY_PROTOCOL, CONDITIONAL, RESERVE, HOLD_ACCESS, REDESIGN, NO_GO}`. All six presently are **NOT approved** as completed submission-ready manuscripts. Do not change status to full protocol merely due to accurate code or pretty charts.

---

# N. PRESENTATION / STREAMLIT SPECIFICATION

## N1. Goals

Build a premium research-facing interface only when it clarifies real scientific results. Default Python `streamlit` under `dashboard/`, minimal external dependencies, no authentication/custom domain charges, light enough for Community Cloud after separate deployment review. Present a **research dashboard, not a consumer service**.

## N2. Visual template (consistent across repos)

- Neutral professional layout; responsive widescreen; clear navigation: Overview → Data provenance → Study cohort → Baselines and models → Validation → Sensitivity/limitations → Reproducibility.
- Typography and charts legible; accessible contrasts; no excessive animations or stock/AI art.
- Mandatory context ribbon: project stage, data cutoff, observed vs simulated/illustrative, current scientific decision and last validated experiment run ID.
- Interactive filters restricted to *available aggregated data*: sending/receiving corridor, quarter, provider type, country, season/tenor/vintage. Missing data must visibly appear as missing, not zero.
- Plots with denominators, units, uncertainty bands, the historical baseline and warnings around out-of-sample versus exploratory results.
- For R01, quote price threshold, matching definition and observation uncertainty must be explicit. For R02, public data vintage/coverage. For R04, dates/tenor/source repairs. For R05, measurement missingness and no clinical-effect correction. For R03/R06 blocked, show a transparent **data feasibility / protocol** view, not fabricated trained-model screens.
- Safe downloadable aggregate CSV tables and figures only; no raw records, model binaries with privacy/licensing restrictions or uncited datasets.
- Application must run locally *in the cloud-session environment* against permitted **small precomputed synthetic or aggregate fixtures**; model training must be a separate offline script, not executed per visitor session.

## N3. Deployment gate

First make a tested `dashboard/app.py` and `dashboard/README.md`. Then if Streamlit Community Cloud is accessible and user approves an external **public dashboard deployment**, launch only apps with vetted public-safe contents, no secrets in GitHub, no private records. If Work cannot deploy because it requires user-controlled OAuth, stop at tested presentation code plus exact link/next action. Record live URL only after Work has actually opened it and verified the scientific labels/figures.

---

# O. CLOUD SESSION LAUNCH AND HANDOFF SEQUENCE

## O1. First lightweight session in each repo

Use `PUBLICATIONS` cloud environment **if actually selectable**, choose the exact GitHub repo, choose an available cost-appropriate coding model, and provide the project-specific task block from section P below. Begin with a light *setup+source smoke* phase and ensure the right repo is attached. Open a PR; avoid pushing directly to `main`. If there is no user-facing provider credit meter, assume no automatic hard spending cap and timebox work.

**Critical:** ChatGPT Work cannot guarantee all six Claude sessions finish in one Work turn. Confirm each launched session in UI; capture URL and final state. Continue subsequent launches if session/site permits, but never claim a session continues or completes if unverified. If cloud browser cannot interact with Claude, prepare the six repos through GitHub tools where possible and give user a single minimal login/control request, rather than claiming a remote execution occurred.

## O2. Cloud environment suitability probe

For every repo's first successful cloud launch, record platform, workdir, Git remotes, Python version, cores, available memory/disk, network endpoint restrictions, user privileges, package install rights and job lifespan. Do not claim shared persistent storage between separate Cloud Sessions or access to Windows F:. Provenance and results require commits, PRs or explicitly permitted durable cloud storage. Test ordinary download to one official public data endpoint, a small real-data processing snippet, unit tests and a minimal dashboard import where relevant.

## O3. Multi-session orchestration without wasted credits

1. Start R01 with task P1, inspect initial results and spending. R02 with P2 may proceed once adequate budget remains.
2. R03–R06 start with bounded smoke/research phase, not six blind GPU jobs.
3. Promote R01 first to full modeling if access valid; R02 to deeper source/vintage comparison; R04 to single rescue; R05 to public-release audit; R06 to outcome acquisition; R03 to dictionary/access audit.
4. Per task output must enumerate attempted sources, actual bytes/rows and commands, status and blockers. A session that writes `TODO.md` without execution does NOT count as modelling.
5. Hold reserve unless demonstrably valuable. Abort only the scientifically invalid subtask, not the entire other-eligible portfolio. If the provider imposes a platform limit or mandatory pause, record it and continue independent tasks safely.

## O4. GitHub branch/pull request protocol

Before writing: `git status`, check existing branches/commits, verify repo remote. Branch `research/<name>-cloud-phase-1`, commit small logical changes. Run `pytest -q` and smoke commands where feasible, include results in PR body. PR title `Research infrastructure + evidence-gated <project> analysis`. PR description: source provenance, calculations actually run, selected targets/metrics, new checks, known limitations, user action if any. Do not merge absent explicit approval. If a repo is empty and cannot make a branch via Claude, GitHub connected tool can seed README/AGENTS safely; verify operation. Do not write six identical generic README files that do not reflect each study.

---

