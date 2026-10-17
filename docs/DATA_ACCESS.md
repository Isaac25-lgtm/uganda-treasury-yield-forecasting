# Data access — what was actually fetched (17 October 2026, cloud session)

| Source | URL / endpoint | Attempts | Outcome | Bytes / rows |
|---|---|---|---|---|
| BoU website shell | `https://www.bou.or.ug/bouwebsite/FinancialMarkets/GovernmentSecurities/TreasuryBills.html` | 1 | 200; JavaScript SPA, no data | 7,578 B |
| BoU JS bundle (endpoint discovery) | `https://www.bou.or.ug/assets/index-B2Dn-qUe.js` | 1 | 200 | 2,136,389 B (not kept) |
| BoU auction catalogue (Strapi CMS) | `https://bou.or.ug/api/financial-market-auction-information?populate=…` | 1 (+1 rerun reading the cached copy) | 200 | 952,664 B, SHA-256 `0f7cf2a1705dd880e1178f584247ae62daf53ae2f6e1a9e9063508d864829302`; 1,156 document entries |
| BoU T-bill documents 2022+ | `https://bou.or.ug/uploads/<file>` | 1 each; 1 file re-fetched after a truncated transfer was detected | 239/239 valid | 33,812,254 B; 119 results + 120 ITTs; per-file SHA-256 in `data/manifests/bou_tbill_documents.csv` |
| BoU monetary-policy listing | `https://bou.or.ug/api/monetary-policy?populate=statementsAndReports…` | 1 | 200; only 4 mislabelled items | 4,641 B — no CBR decision history |
| BoU interest-rate page | `https://bou.or.ug/api/interest-rate?populate=…` | 1 | 200; CBR chart is a Power BI embed; only file is a current FX snapshot | 4,286 B |
| UBOS (CPI releases) | `https://www.ubos.org/` | 2 | **TLS failure** (`unable to get local issuer certificate`); verification was not disabled | 0 B |

Interpretation of the "≤3 attempts per host" rule: at most 3 attempts per resource, no retries for 403/404, ≥0.4 s
between downloads. Downloading each listed T-bill document once was necessary for the task.

**Release timing.** CMS `createdAt` values are *not* release timestamps: 2022–2025 documents show bulk-migration dates
(2025-12-31, 2026-04-25). Evidence actually used: ITT printed notice dates (pre-bid), and results-PDF `CreationDate`
metadata (all ≥12.5 h after auction-day midnight, Kampala time, i.e. after the 10:00 deadline).

**Licence.** Public BoU website documents, used for non-commercial research; raw files are not redistributed
(kept in git-ignored `data/raw/`). Committed tables contain only printed public auction aggregates and file hashes.

**Not obtained (HOLD_DATA):** dated CBR decisions, UBOS CPI with release dates, BoU daily FX history, interbank/secondary
market rates. No paid data was used.
