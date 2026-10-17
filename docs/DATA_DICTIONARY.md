# Data dictionary (observed fields after audit)

`results/tables/event_registry_tenor_rows.csv` — one row per (auction_date, tenor), 300 rows.

| Field | Meaning |
|---|---|
| auction_date | auction date printed in the results release |
| printed_auction_no | issue number as printed (note: the 2024-02-14 release prints `1171`; its file name and ITT say 1172) |
| tenor | 91 / 182 / 364 days |
| maturity_date | printed maturity date |
| cutoff_price_raw, mmy_raw | printed strings, untouched |
| mmy | printed money-market yield parsed as a plain decimal (NaN if unparseable / N/A) |
| mmy_repaired | `mmy`, except declared `..` → `.` repair |
| mmy_implied_nominal | `(100/P − 1)·365/tenor·100` |
| identity_gap_pp / identity_gap_actual_pp | |printed − implied| with nominal / actual (maturity − settlement) days |
| identity_ok | gap ≤ 0.02 pp under the nominal convention |
| days_actual, tenor_consistent | maturity − settlement days; within 3 days of tenor |
| parse_flag | `ok`, `unparseable`, `not_awarded` |
| source_file, sha256 | official document and its hash |

`results/tables/prebid_itt_timing_audit.csv` — one row per Invitation to Tender: printed issue_no, auction_date,
notice_date, notice_lead_days, timing_status (`pre_bid_verified`, `TIMING_VIOLATION`, `implausible_lead_unverified`,
`auction_date_unparsed`, `no_text_layer`), offer_91/182/364/total (UGX), bid_deadline.

Model features (`src/ugtbill/features.py`): lag — `dy_lag1`, `dy_lag2`, `y_lag1`, `spread_364_91_lag1`,
`spread_182_91_lag1`, `days_since_prev`, tenor dummies; pre-bid — `log_offer_tenor`, `offer_change_vs_prev`,
`offer_share_tenor`. Missing values are never zero-filled; rows lacking any feature are excluded for *all* models.
