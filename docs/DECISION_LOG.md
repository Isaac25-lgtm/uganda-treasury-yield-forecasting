# Decision log

| When (UTC, 2026-10-17) | Decision | Reason |
|---|---|---|
| ~19:04 | Use BoU Strapi CMS catalogue instead of scraping the SPA | single official listing with document URLs |
| ~19:10 | **Freeze protocol** (`configs/experiment.yaml`, commit `3bf3cb3`) | before any results table was parsed |
| ~19:11 | UBOS stopped after 2 TLS failures | never disable TLS verification; CPI → HOLD_DATA |
| ~19:12 | CBR/FX → HOLD_DATA | no dated, downloadable CBR history; FX file is a snapshot |
| ~19:13 | Target = printed money-market yield; identity convention 365/nominal days | matches printed yields in 296/299 priced rows |
| ~19:14 | Auction 1176 kept in primary set, excluded in `drop_1176` | its yields match actual (not nominal) days; ambiguity, not an error proof |
| ~19:14 | ITT offers usable only if notice is dated 1–14 days pre-auction | 3 violations and 5 year-typo leads observed; decided before metrics |
| 19:15 | Run 1 → NEGATIVE_MODEL (42 test auctions) | commit `eb66c2d` |
| ~19:17 | Parser fix for `Month,DD YYYY` ITT dates; run 2 → NEGATIVE_MODEL (45) | post-metric data-quality fix; reported transparently |
| ~19:18 | **Stop the research branch** — no further algorithms | frozen stop rule |
