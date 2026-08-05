# Interaction 003 — Rule A news foundation and sector sentiment

Date: 2026-08-05
Project: /Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectB

## Prompt

The complete original prompt is preserved verbatim from /Users/chris/.codex/attachments/789bdfd3-d6c2-4709-bf4a-8fcf9e0c4bd5/pasted-text.txt:

```text
Interaction 003 — Rule A news foundation and sector sentiment

Read and follow AGENTS.md, context/PART_A_HANDOFF.md and
context/PROJECT_DECISIONS.md. Work only inside z5711503_projectB.

Do not tune portfolios, alter existing fund results, implement fusion, build
figures, write the report, modify Streamlit, push or deploy.

Use only:
- the official Project B data loader;
- the approved Part A methods;
- the local Week 8 and Week 9 course files already identified in the handoff.

Do not download sentiment models or lexicons. If the required local VADER
resource or Week 8 approval inputs cannot be found, stop and report the exact
missing dependency.

============================================================
1. Apply the approved Interaction 002 review corrections
============================================================

Update ai/AI_NOTES.md accurately:

- ChatGPT was used for course-material review, project planning and independent
  audit.
- Codex was used for repository setup, documentation and the implemented data
  foundation and walk-forward portfolio engine.
- CHUHAO PENG accepted the portfolio engine after independent review, but
  sentiment, fusion, app and report work remain pending.
- Do not retain future-tense wording suggesting implementation has not begun.
- Retain the living-draft status.

Update the status near the top of context/PROJECT_DECISIONS.md:

- portfolio methodology is locked and implemented through Interaction 002;
- portfolio outputs exist and passed technical review;
- no economic “best fund” conclusion has been approved;
- sentiment decisions below remain a predeclared design until Interaction 003
  is implemented and reviewed.

Do not change any implemented portfolio parameter or result.

============================================================
2. Complete the portfolio quality and provenance checks
============================================================

Add synthetic tests confirming:

- Minimum Variance variance is no greater than capped Equal Weight on the same
  feasible covariance input, within numerical tolerance;
- Maximum Sharpe objective is no worse than capped Equal Weight when the
  optimiser reports success;
- successful Risk Parity weights produce approximately equal percentage risk
  contributions on a well-conditioned synthetic covariance matrix;
- all optimisers are deterministic for identical inputs.

Do not alter optimisation settings merely to make tests pass. Report genuine
numerical limitations.

Create results/tables/run_manifest.csv with two columns:

key,value

Include at minimum:

- run timestamp in UTC;
- project name;
- current Git HEAD before the run;
- Python version;
- pandas, numpy, scipy, nltk and vader package/version information where
  applicable;
- official data source actually used;
- official source ZIP SHA-256 when a local or cached ZIP is available;
- sample end date;
- all locked portfolio parameters;
- all locked sentiment parameters;
- row counts and SHA-256 hashes of the mandatory generated output files,
  excluding run_manifest.csv itself.

The runner must generate this manifest reproducibly. Do not invent a source ZIP
hash when the downloaded bytes are unavailable.

============================================================
3. Lock the remaining sentiment implementation decisions
============================================================

Before implementation, update context/PROJECT_DECISIONS.md with:

Finance lexicon:
- reproduce the Week 8 approved finance-extension workflow exactly from the
  local course files;
- freeze the resulting approved lexicon as
  resources/finance_vader_lexicon.csv;
- record exact source paths, transformation rules, approved/rejected term
  counts and SHA-256;
- preserve the course implementation’s treatment of single tokens, special
  cases and boosters;
- where an approved exact token collides with base VADER, the frozen approved
  finance value takes precedence;
- do not add, remove or manually alter terms after observing Project B results;
- changed coverage or scores are not evidence of improved predictive accuracy.

Sector membership and coverage:
- derive ticker-sector mapping only from the official cleaned equity data;
- on each observed equity date, an eligible sector ticker is a mapped equity
  ticker with a valid adjusted-close return on that date;
- observed ticker count is the number of eligible sector tickers with at least
  one supplied headline mapped to that date;
- coverage = observed_ticker_count / eligible_ticker_count;
- a ticker-day without a supplied headline remains missing;
- a sector-day with no observed ticker sentiment remains missing;
- never fill missing ticker sentiment with zero.

Signal construction:
- score the original unmodified headline title;
- apply approved Rule A first;
- aggregate headline arithmetic mean to ticker-day;
- aggregate equal-weight observed ticker-days to sector-day;
- create both plain VADER and frozen finance-extended VADER;
- transform compound to a descriptive 0–100 index using
  50 * (compound + 1);
- calculate causal expanding z-scores separately by sector and model with
  minimum 252 available historical sector observations and sample standard
  deviation;
- the source-day z-score may use information available through that source day;
- shift the completed source-day causal z-score by exactly one observed equity
  trading day before trading use;
- after lagging, carry a wholly missing sector signal for at most five observed
  equity trading days using the predeclared linear coverage decay;
- age 0 means an actual previous-trading-day source signal; ages 1–5 are carried
  values; age 6 onward is missing;
- full-sample z-scores are descriptive only and never enter future fusion.

============================================================
4. Restore the complete Part A Rule A mapping
============================================================

Implement or adapt a row-level Rule A function in src/features.py.

For every cleaned headline preserve:

- ticker
- title
- original_utc_timestamp
- headline_calendar_date
- mapped_equity_trading_date
- mapping_delay_calendar_days
- mapping_status
- timestamp_time_of_day_status
- mapping_rule

Required behaviour:

- same observed cleaned-equity date maps to the same date;
- otherwise map to the next observed cleaned-equity date;
- preserve final-boundary rows with no following observed date in the mapping
  audit, but exclude them from sentiment calculations requiring a valid mapped
  date;
- do not infer verified publication time or after-close status;
- do not replace the original timestamp;
- reproduce the approved Part A reconciliation counts exactly unless the
  official source bytes differ, in which case stop and report.

Add tests for same-day, weekend, holiday/gap, final boundary, timestamp
preservation and the “mapped Monday can first trade Tuesday” rule.

============================================================
5. Implement sentiment
============================================================

Implement src/sentiment.py with small testable functions for:

- loading and validating the frozen finance lexicon;
- isolated creation of plain and finance-extended VADER analysers;
- prevention of shared mutable lexicon contamination between analysers/tests;
- scoring distinct raw titles once and joining scores back;
- headline-to-ticker-day aggregation;
- complete sector-date grid construction;
- ticker-day-to-sector aggregation and coverage;
- descriptive 0–100 index;
- descriptive full-sample z-score;
- causal expanding z-score;
- one-equity-trading-day lag;
- five-day carry and effective-coverage decay;
- audit and model-comparison tables.

Do not lowercase, strip punctuation, remove negation, remove boosters or score
the Part A tokenised text.

Generate:

Mandatory:
results/data/sector_sentiment_index.csv

Additional:
results/data/ticker_day_sentiment.csv
results/data/sector_sentiment_signal.csv
results/tables/news_mapping_audit.csv
results/tables/sentiment_data_audit.csv
results/tables/sentiment_model_comparison.csv
results/tables/finance_lexicon_audit.csv

Use these schemas.

sector_sentiment_index.csv:
date, sector, model, headline_count, observed_ticker_count,
eligible_ticker_count, coverage, compound_mean, index_0_100,
causal_expanding_mean, causal_expanding_std, causal_z,
descriptive_full_sample_z

ticker_day_sentiment.csv:
date, ticker, sector, model, headline_count, compound_mean, index_0_100

sector_sentiment_signal.csv:
effective_date, source_date, sector, model, source_compound_mean,
source_causal_z, signal_age, is_carried, source_coverage,
effective_coverage, trading_z

Requirements:

- model values are exactly plain_vader and finance_vader;
- dates are ISO format;
- maintain all observed equity dates and sectors in the sector index, including
  explicit missing sector-days;
- no row may imply that missing news equals neutral sentiment;
- the trading signal table must never use full-sample standardisation;
- stable sorting and unique documented keys;
- use sufficient numeric precision;
- do not manually edit outputs.

The comparison table must report without accuracy claims:

- distinct titles scored;
- headlines whose compound score changed;
- percentage changed;
- mean and median absolute score change;
- positive/neutral/negative classification changes under the documented ±0.05
  threshold;
- sector-index differences;
- approved and rejected finance-term counts.

============================================================
6. Runner and tests
============================================================

Update scripts/run_part_b.py so it reproducibly performs:

1. official data load and cleaning;
2. return panels and existing 12-fund engine;
3. complete Rule A mapping;
4. frozen lexicon validation;
5. plain and finance VADER scoring;
6. ticker-day and sector-day sentiment;
7. causal lagged trading signals;
8. all current portfolio and sentiment outputs;
9. run manifest and concise audits.

Do not implement fusion.

Add focused synthetic tests covering:

- analyser isolation and determinism;
- casing, punctuation, booster and negation preservation;
- frozen lexicon loading and collision precedence;
- distinct-title scoring and correct join-back;
- headline, ticker-day and equal-weight sector aggregation;
- eligible/observed ticker coverage;
- missing ticker-day and missing sector-day semantics;
- 0–100 transformation bounds;
- causal expanding standardisation with 252 minimum observations;
- future sentiment perturbation does not change earlier causal values;
- exact one-equity-day lag;
- five-day carry, linear coverage decay and age-six expiry;
- full-sample z-score cannot enter trading_z;
- output schemas, keys and ordering;
- the four new optimiser-quality tests from section 2.

Most tests must use synthetic fixtures and require no network.

============================================================
7. Independent verification
============================================================

Run:

python scripts/run_part_b.py
pytest -q
python scripts/check_handin.py
git diff --check
git status --short

Independently verify:

- Project A Rule A reconciliation;
- no original timestamp was overwritten;
- final-boundary unmapped rows are preserved in audit and excluded from scores;
- weekend/Monday news cannot affect Monday holdings;
- plain and finance analysers do not contaminate each other;
- sector coverage is between 0 and 1;
- explicit missing sector-days are not converted to neutral 50;
- causal values are unchanged by future-data perturbations;
- no trading row uses descriptive_full_sample_z;
- signal ages are only 0–5 and expired signals are absent/missing;
- mandatory output keys are unique;
- portfolio outputs remain numerically unchanged from Interaction 002;
- manifest hashes match actual files;
- no raw data, cache, secret or OS metadata is tracked.

Create:

ai/interaction_003_rule_a_and_sector_sentiment.md

Preserve this complete prompt verbatim. Include:

- files and course sources read;
- frozen lexicon provenance and hash;
- locked decisions;
- official data source used;
- commands and tests;
- Rule A counts;
- sentiment counts and missingness;
- plain-versus-finance comparison;
- anything wrong or risky;
- what was checked or corrected;
- exact changed-file list.

Do not call finance VADER more accurate unless labelled validation supports that
claim. Do not interpret investment performance or implement fusion.

Commit after successful validation:

docs: record reviewed portfolio baseline
feat: build causal sector sentiment pipeline

Report both commit hashes, exact changed-file list and final git status.
```

## Scope and outcome

This interaction applied the supplied post-Interaction-002 review status, added portfolio quality tests, froze the locally approved Week 8 finance lexicon, restored complete row-level Rule A mapping, and implemented plain and finance VADER sector sentiment with causal trading signals. It generated the requested sentiment, audit, and run-manifest files. It did not tune portfolios, alter portfolio outputs, implement fusion, build figures, write report prose, modify Streamlit, push, or deploy.

## Files and course sources read

Project B reads included AGENTS.md, context/PART_A_HANDOFF.md, context/PROJECT_DECISIONS.md, ai/AI_NOTES.md, the prior interaction records, the existing data/feature/portfolio/sentiment modules, the runner, tests, hand-in checker, requirements files, existing portfolio outputs, and the complete attached prompt.

The local read-only course sources used were:

- /Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/WEEK8_COMPLETION.md
- Week 8 vader_model/vader_tools.py and scripts 06, 09, and 10
- Week 8 candidate_terms.txt, human_review.csv, all ten raw_ratings/rater_*.txt files, and the generated approved/audit CSVs from script 09
- Week 9 fear_greed_tools.py and scripts 01 through 04 identified in the handoff

No course or Part A file was modified. Week 9 informed distinct-title scoring, the 0–100 transform, and the descriptive/causal distinction; its downloadable NLTK/finVADER path was not used because this interaction required the local Week 8 approved extension and prohibited downloads.

## Review corrections and locked decisions

- ai/AI_NOTES.md now records ChatGPT's course-review/planning/audit role, Codex's implemented repository/data/portfolio role, CHUHAO PENG's independent acceptance of the portfolio engine, and the still-pending review or implementation of sentiment, fusion, app, and report work.
- The decisions status records the implemented and technically reviewed portfolio baseline, no approved best-fund conclusion, and pending sentiment review.
- Sentiment decisions were locked before code: official membership and return eligibility; Rule A; unchanged titles; headline-to-ticker-day and equal-weight eligible-ticker-day-to-sector aggregation; missing-news semantics; the two exact model names; the 0–100 transform; 252-observation causal expanding sample-standard-deviation z-scores; one-equity-day lag; ages 1–5 carry; linear coverage decay; age-six expiry; and descriptive-only full-sample z-scores.
- No portfolio parameter, optimisation setting, or result changed.

## Frozen finance lexicon provenance

The required local implementation was available without download: Python 3.13.13, vaderSentiment 3.3.2 with 7,506 base terms, and nltk 3.6.2 recorded for provenance. The inputs contain 39 candidates, 10 raters, 390 frozen integer ratings, 29 approved terms, and 10 rejected terms. The approved set has 20 words and 9 phrases.

The Week 8 workflow groups ratings by exact term, computes arithmetic mean and sample standard deviation, rounds both to three decimals, applies sd < 2.5 and abs(mean) >= 0.5, then requires the human approve decision. Words update only the finance analyser. Phrases use SPECIAL_CASES plus a missing final head word at plus or minus 0.1. The course booster candidates preserve B_INCR/B_DECR treatment and only absent base boosters are added.

Frozen file: resources/finance_vader_lexicon.csv

Source: /Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/output/tables/09_finance_lexicon_approved.csv

Both SHA-256 values are 4c16eeab9edec5c970234d0a30bcbd89c84c21abf94e4677b8b9568c8b6a28c6, and byte comparison passed. The only approved exact-token collision with installed base VADER is litigation; the frozen finance value takes precedence only in the isolated finance analyser. Changed scores are not labelled accuracy improvements.

## Official data source

The frozen loader used its primary URL:
https://drive.google.com/uc?export=download&id=1h0Wy12_qgR_NZJqtSxI9LwPEVKgp5DzH

The runner hashed the downloaded ZIP bytes in memory without storing them:
9740a68c63e4edf2fbe03d91a5356728e9355a1070580052b66893d4c7463010

No other data source, downloaded model, downloaded lexicon, fabricated row, or raw data file was used.

## Rule A reconciliation

- cleaned audit rows: 146,836
- same observed equity date: 134,279
- shifted to next observed equity date: 12,551
- final-boundary unmapped rows retained: 6
- valid mapped rows entering scoring: 146,830
- missing preserved original timestamps: 0

The six boundary rows remain in news_mapping_audit.csv and are excluded from all scoring and aggregation. A regression test confirms weekend news mapped to Monday cannot trade before Tuesday.

## Sentiment counts and missingness

- distinct original titles scored once per model: 105,330
- ticker-day-model aggregates: 75,924
- complete equity-date by 10-sector by 2-model rows: 20,120
- explicit missing sector-model days: 476
- active causal trading signals: 14,890
- non-missing coverage range: 0 to 1
- duplicate ticker-day, sector-index, and signal keys: 0
- non-missing signal ages: exactly 0 through 5
- missing compound rows converted to neutral 50: 0

Plain and finance analysers have separate lexicons and temporarily isolated module-level phrase and booster dictionaries under a lock.

## Plain-versus-finance comparison

This is a change audit, not labelled accuracy validation:

- titles changed: 3,860 of 105,330, or 3.6646729327%
- mean absolute compound change: 0.0093647166
- median absolute change: 0
- classification changes at plus or minus 0.05: 1,199, or 1.1383271623%
- comparable sector rows: 9,822
- changed sector compound rows: 2,625, or 26.7257177764%
- mean absolute sector compound difference: 0.0066882932
- approved/rejected finance terms: 29/10

No predictive-accuracy, causal, investment-performance, or best-model claim is made.

## Portfolio quality and preservation

Synthetic tests confirm Minimum Variance variance is no greater than capped Equal Weight, successful Maximum Sharpe is no worse than capped Equal Weight, successful Risk Parity approximately equalises percentage risk contributions, and all four optimisers are deterministic.

All five Interaction 002 portfolio hashes remained byte-identical:

- fund_returns.csv: 709322f5158707667a220dccb30c1713032264d4378d0c8de412693a3d432756
- fund_weights.csv: 8f9c45fb2e20bea0f3353d0a830100c60b15c2c1a746790be39a63c395f872b7
- performance_metrics.csv: a1687e1de010ffb8b4349c46dbbc9b8aa94c110bf98e08817d03ef20f2aa7945
- solver_audit.csv: d9a27c3017175e088298ce2f5dd86e337936e2157c843e46cf3085ac7e39c339
- portfolio_data_audit.csv: 90607d31b514c0089db3ec1d4545a05667a7c729a297e471957cb77e10862568

The existing five Crypto Risk Parity fallbacks remain unchanged and recorded.

## Run manifest

results/tables/run_manifest.csv has key,value schema and 64 rows. It records the UTC timestamp, project, pre-run HEAD 42822ed136a23dccf653ff36135943bc3aa678bc, Python/package versions, actual source and ZIP hash, sample end, locked parameters, and row counts plus SHA-256 for all twelve generated outputs other than the manifest. Independent recomputation found 12 hash rows and zero mismatches. The manifest intentionally excludes its own hash and its timestamp changes on a new run.

## Commands and validation

Commands included dependency/version checks, sed/rg inspection, shasum -a 256, byte comparison, python -B scripts/run_part_b.py, focused and full pytest runs, independent pandas/hash checks, python -B scripts/check_handin.py, git diff --check, tracked-file guards, and git status --short.

- focused Rule A/sentiment/portfolio-quality tests: 26 passed after two test-assumption corrections
- all offline/synthetic project tests: 35 passed
- full pytest: 37 passed
- check_handin.py: 21 checks passed, no failures, and two expected reminders for ignored local Python cache and the out-of-scope report
- git diff --check: passed
- manifest hashes: 12/12 matched
- no raw data, cache, secret, OS metadata, parquet, or bytecode artifact is tracked

The checker's mechanical ready-to-zip/deploy line is not a claim that report, fusion, app changes, deployment, push, or hand-in exists.

## What was wrong or risky

- The first collision test incorrectly assumed approved default existed in base VADER. Inspection showed the actual approved collision is litigation.
- The original hand-in checker rejected every CSV outside results, including the explicitly required frozen derived lexicon.
- VADER SPECIAL_CASES and BOOSTER_DICT are mutable module dictionaries; naive extension would contaminate the plain model.
- Rule A Monday mapping alone is not Monday trading permission.
- Filling missing news with zero or 50 would create false observations.
- Full-sample z-scores would create look-ahead if used for trading.
- Changed scores are not evidence of better accuracy.
- Inventing a ZIP hash after discarding bytes would create false provenance.

## What was checked or corrected

- Corrected the collision test to litigation without altering optimiser settings.
- Added one exact-path checker exception for resources/finance_vader_lexicon.csv; every other outside-results CSV/Parquet remains blocked.
- Restored module state after each analyser batch.
- Preserved all Rule A rows and ISO UTC timestamps.
- Excluded boundary rows, retained complete grids, and preserved missingness.
- Verified future perturbations cannot change prior causal values.
- Verified active signals use causal source z with the exact lag and ages.
- Regenerated outputs without manual edits.
- Verified manifest and Interaction 002 hashes.

## Exact changed-file list

1. .gitignore
2. ai/AI_NOTES.md
3. ai/interaction_003_rule_a_and_sector_sentiment.md
4. context/PROJECT_DECISIONS.md
5. requirements-dev.txt
6. resources/finance_vader_lexicon.csv
7. scripts/check_handin.py
8. scripts/run_part_b.py
9. src/features.py
10. src/sentiment.py
11. tests/test_portfolio_methods.py
12. tests/test_rule_a.py
13. tests/test_sentiment.py
14. results/data/sector_sentiment_index.csv
15. results/data/sector_sentiment_signal.csv
16. results/data/ticker_day_sentiment.csv
17. results/tables/finance_lexicon_audit.csv
18. results/tables/news_mapping_audit.csv
19. results/tables/run_manifest.csv
20. results/tables/sentiment_data_audit.csv
21. results/tables/sentiment_model_comparison.csv

No existing portfolio CSV, fusion module, figure, report, streamlit_app.py, Part A file, course file, raw data, or deployment configuration changed.
