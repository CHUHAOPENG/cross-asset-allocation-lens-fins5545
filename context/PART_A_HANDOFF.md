# Part A to Part B handoff

## Purpose and boundary

This handoff records the approved parts of CHUHAO PENG's own Project A foundation that Project B may reuse. Project A remains read-only. Project B will not copy the Part A folder, raw data, reports, readiness artifacts, or generated exhibits. Existing supplied files in this Project B `context/` folder remain unchanged.

## Exact Part A sources inspected

- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/context/student_decisions.md`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/src/etl.py`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/src/features.py`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/scripts/run_part_a.py`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/tests/test_station1_etl.py`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/tests/test_station2_features.py`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/tests/test_station2_timestamp_diagnostic.py`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/results/tables/feature_dictionary.csv`
- `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA/results/tables/calendar_alignment_summary.csv`

No other Part A file was used for this handoff.

## Reuse, adaptation, and exclusion

| Part A item | Project B treatment | Reason |
|---|---|---|
| `clean_price_data`, `clean_news_headlines`, and the `load_clean_*` interfaces in `src/etl.py` | Adapt into Project B rather than importing across project boundaries | Preserve approved keys, 2020-2023 boundary, exact news de-duplication, missingness, and deterministic ordering while keeping Project B standalone. |
| `daily_returns` and `observed_equity_calendar` in `src/features.py` | Reuse the method and tests | Returns are ticker-isolated `adjClose.pct_change(fill_method=None)` on native dates; no price fill is permitted. |
| `map_news_rule_a` in `src/features.py` | Reuse the mapping rule and audit fields | It implements the approved calendar-date decision without pretending the supplied time component is publication time. |
| `assemble_headline_panel` in `src/features.py` | Adapt for sentiment inputs | Preserve the complete equity ticker-date grid and the distinction between zero supplied headlines and a neutral score. Project B must retain actual headline text for scoring rather than only Part A count samples. |
| `align_crypto_returns_to_equity_calendar` and `calendar_alignment_summary` | Adapt for Combined funds and audit | Calculate native seven-day crypto returns first, then select already-computed returns onto equity dates. |
| Part A tests for ticker isolation, missing-price handling, Rule A statuses, and crypto Monday/weekend behaviour | Port or rewrite as Project B regression tests | These tests directly protect the inherited calendar and no-fill decisions. |
| Project B's supplied `src/data_access.py` | Keep as the Project B loader; do not copy Part A's loader | The starter already provides the official standalone access path. |
| Part A readiness matrix, descriptive tokenisation/watchlist, figures, report prose, output samples, and packaging material | Exclude | They are Part A descriptive or submission artifacts, not Project B portfolio/sentiment inputs. |

## Approved Rule A news mapping

Rule A is **Conservative Calendar-Date Mapping**:

1. Preserve `original_utc_timestamp` and derive its UTC `headline_calendar_date`.
2. Do not trust either midnight or non-midnight clock time as verified publication time.
3. If the UTC calendar date is an observed cleaned-equity trading date, map to the same date.
4. Otherwise map to the next observed cleaned-equity trading date.
5. Preserve `headline_calendar_date`, `mapped_equity_trading_date`, `mapping_delay_calendar_days`, `mapping_status`, `timestamp_time_of_day_status`, and `mapping_rule`.
6. Keep a final-boundary row in mapping audit data when no following observed equity date exists, but exclude it from calculations needing a valid mapped date.

For trading, the mapped daily sentiment signal is then lagged by one additional equity trading day. Rule A alignment by itself is not permission to trade on the mapped day.

## Crypto calendar treatment

- Sort within ticker and calculate simple adjusted-close returns on the native seven-day crypto calendar.
- Never forward-fill a price and never merge price levels onto the equity calendar before differencing.
- Equity and Combined fund rows use crypto returns selected from the already-computed native return series on observed equity trading dates. Weekend-only and other non-equity-date return rows do not enter the Combined comparison.
- Crypto-only funds retain the native calendar and use 365-period annualisation. Equity and Combined funds use their equity-date calendar and 252-period annualisation.
- Part A's supplied alignment summary records 14,600 valid native crypto ticker-day returns, 10,060 selected to 1,006 observed equity dates, and 4,540 excluded by the comparison-calendar selection. These are inherited audit facts, not new Project B results.

## Limitations that remain mandatory disclosures

- News contains headlines, not article bodies; headline sentiment is a noisy proxy.
- Supplied timestamps are not verified publication times. The data have different timestamp regimes, including a mechanically patterned 2023 non-midnight block, so after-close logic is not supported.
- Rule A uses observed cleaned-equity dates, not a complete exchange calendar; early closes are not modelled.
- Six cleaned Part A final-boundary headlines had no following observed equity date.
- Publisher is missing or blank for about 93.6% of cleaned Part A headlines and is not an economic signal.
- News coverage is uneven across tickers, sectors, and dates. No supplied headline means missing coverage, not neutral sentiment and not proof that no news existed.
- Exact duplicate cleaning on ticker, normalised date, and title may collapse source-level or syndication variation.
- The sample ends at 2023-12-31. No result is current, predictive, causal, or an investment recommendation merely because the inherited mapping and returns are reproducible.
- Native-to-equity crypto selection deliberately omits weekend-only observations from Combined funds and must be disclosed when interpreting cross-asset results.

## Relevant course-week code inspected

The following read-only course paths informed the Project B design; none is copied wholesale:

- Week 5 OOS scheduling, solvers, drifted holding returns, metrics, turnover, and audits:
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week5/code/stage3_oos_portfolios.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week5/tests/test_stage3_oos_portfolios.py`
- Week 8 VADER preservation and finance-extension workflow:
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/vader_tools.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/06_score_movie_reviews.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/09_build_finance_lexicon.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/10_extend_and_test_vader.py`
- Week 9 plain-versus-finance VADER scoring, aggregation, and descriptive/causal standardisation distinction:
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week9/fear_greed_index/fear_greed_tools.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week9/fear_greed_index/01_recap_vader_meet_finvader.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week9/fear_greed_index/02_score_headlines.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week9/fear_greed_index/03_transform_to_01.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week9/fear_greed_index/04_build_fear_greed_index.py`

Week 5 is a useful architecture, not a drop-in implementation: it is crypto-specific, uses a 365-day constant, does not implement this project's dynamic maximum-weight cap, and raises on several solver failures rather than applying the Project B fallback. Week 9 full-sample z-scores are descriptive only; Project B trading must use causal expanding standardisation.
