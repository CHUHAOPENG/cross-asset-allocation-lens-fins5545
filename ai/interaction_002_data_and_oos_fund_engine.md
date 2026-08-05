# Interaction 002 — data foundation and walk-forward fund engine

Date: 2026-08-05
Project: `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectB`

## Prompt

The complete original prompt is preserved verbatim from `/Users/chris/.codex/attachments/eeedd501-d883-4e5e-9816-fc2daac45b2c/pasted-text.txt`:

```text
Interaction 002 — Data foundation and walk-forward fund engine

Read and follow AGENTS.md, context/PART_A_HANDOFF.md,
context/PROJECT_DECISIONS.md, and the supplied Project B context files.
Work only inside z5711503_projectB.

This interaction may use the official course data through the frozen
src/data_access.py loader. First search under /Users/chris/Desktop/fins 5545
for an existing official project_data.zip and use FINS_DATA_ZIP if found.
Otherwise the loader may download only from its supplied official primary or
backup URL. Do not edit data_access.py, commit raw data, use other data, or
fabricate results. If official data cannot be loaded, stop and report.

============================================================
1. Correct the living AI summary
============================================================

Update ai/AI_NOTES.md:

- State that ChatGPT was used for course-material review, project planning and
  independent audit, while Codex was used for repository work and implementation.
- Replace the broad “reviewed and approved” claim with an accurate statement:
  I reviewed the proposed product and methodology and allowed them to be recorded
  as a working design baseline; unresolved implementation choices still require
  review before use.
- Retain the living-draft status and do not claim future work is complete.

Record this correction in the Interaction 002 log.

============================================================
2. Lock the remaining portfolio decisions
============================================================

Before writing analytical code, update context/PROJECT_DECISIONS.md to resolve
the portfolio-engine items as follows:

Calendar:
- Each decision date is the last observed date of a calendar month.
- Training includes data through that decision date.
- Target weights become effective on the first observed date of the next month.
- The effective date begins the next holding period.
- Do not create a final decision if no following observation exists.

Eligibility:
- Cap all source samples at 2023-12-31.
- An asset is eligible at a decision date only if it has a valid return on that
  date and at least the applicable initial-window number of valid historical
  returns through that date.
- Use only information available at that decision.
- Build the covariance input from complete historical rows across the currently
  eligible assets.
- If complete rows are fewer than the applicable initial window, skip that
  rebalance and record the reason.
- Never fill a missing return. If a realised holding-period return is missing,
  output a missing fund return and an audit warning rather than imputing it.

Estimators:
- Covariance is the sample covariance with fixed 10% diagonal shrinkage:
  0.90 * sample_covariance + 0.10 * diagonal(sample_covariance).
- Maximum-Sharpe expected returns are expanding historical arithmetic means,
  shrunk 50% toward the cross-sectional mean at that decision.
- These fixed values are methodological choices, not full-sample-tuned values.

Optimisation:
- Use scipy SLSQP with maxiter=1000 and ftol=1e-10.
- Fully invested, long-only, and use the existing dynamic maximum-weight rule.
- Use capped equal weight as the deterministic initial point.
- Validate sum-to-one within 1e-8, finite weights, lower bound within 1e-10,
  and maximum bound within 1e-8.
- Minimum Variance minimises portfolio variance.
- Maximum Sharpe maximises expected return divided by volatility.
- Risk Parity minimises squared deviations of asset risk contributions from
  equal risk contributions.
- Equal Weight is the capped equal-weight benchmark.
- Preserve the previously declared fallback and log every failure.

Projection:
- Implement deterministic Euclidean projection onto the capped simplex using
  bisection on the threshold in clip(v - threshold, 0, cap).
- Validate feasibility and deterministic output.

Accounting:
- At the first live rebalance, turnover is 1.0.
- Later turnover is 0.5 times the L1 distance between target weights and the
  pre-trade drifted weights over the union of old and new assets.
- Trading-cost fraction is 0.001 * turnover.
- On a rebalance date:
  net_return = (1 - trading_cost_fraction) * (1 + gross_return) - 1.
- On other dates, net_return equals gross_return.
- Keep gross return, turnover, cost and net return separate.

Identifiers:
- Use lowercase stable IDs:
  equity_equal_weight, equity_min_variance, equity_risk_parity,
  equity_max_sharpe;
  crypto_equal_weight, crypto_min_variance, crypto_risk_parity,
  crypto_max_sharpe;
  combined_equal_weight, combined_min_variance, combined_risk_parity,
  combined_max_sharpe.

============================================================
3. Implement the inherited data foundation
============================================================

Implement src/etl.py and src/features.py by adapting the approved Part A methods,
not by importing from Project A.

Required behaviour:
- official loader only;
- deterministic cleaning and sorting;
- exact duplicate checks;
- sample cap at 2023-12-31;
- adjusted-close simple returns within ticker with fill_method=None;
- no price forward filling;
- observed cleaned-equity calendar;
- crypto native-calendar returns calculated before equity-date selection;
- Equity, Crypto and Combined wide return panels;
- schema, row-count, ticker, date-range, missingness and finite-value audits.

Do not implement sentiment in this interaction.

============================================================
4. Implement the OOS fund engine
============================================================

Implement src/portfolios.py with small testable functions for:

- capped-simplex projection;
- equal weight;
- minimum variance;
- risk parity;
- maximum Sharpe;
- optimiser validation and deterministic fallback;
- monthly decision/effective-date schedule;
- drifted portfolio weights;
- turnover and trading costs;
- walk-forward OOS backtesting;
- performance metrics;
- current holdings;
- solver and data-quality audit records.

Generate all 12 predeclared funds.

Required mandatory outputs now:

results/data/fund_returns.csv
results/data/fund_weights.csv
results/tables/performance_metrics.csv

Also create:

results/tables/solver_audit.csv
results/tables/portfolio_data_audit.csv

Use these schemas:

fund_returns.csv:
date, fund_id, universe, method, periods_per_year, gross_return, turnover,
trading_cost, net_return, growth_gross, growth_net, drawdown_gross,
drawdown_net, is_rebalance

fund_weights.csv:
decision_date, effective_date, fund_id, universe, method, ticker,
target_weight, pretrade_weight, asset_cap, eligible_asset_count,
solver_success, fallback_used

performance_metrics.csv:
fund_id, universe, method, first_live_date, last_date, observations,
periods_per_year, cumulative_return_gross, annualised_return_gross,
annualised_volatility_gross, sharpe_gross, max_drawdown_gross,
cumulative_return_net, annualised_return_net, annualised_volatility_net,
sharpe_net, max_drawdown_net, total_turnover, average_rebalance_turnover,
total_trading_cost, rebalance_count, fallback_count

Use ISO dates, stable sorting and sufficient numeric precision.
Do not manually alter outputs after generation.

============================================================
5. Runner and tests
============================================================

Update scripts/run_part_b.py so this interaction reproducibly:

1. loads and audits data;
2. builds the three return universes;
3. runs all 12 OOS funds;
4. writes the five portfolio outputs;
5. prints concise date, row-count, fallback and constraint summaries.

Keep sentiment, fusion, figures, report and app work for later interactions.

Add focused tests covering at minimum:

- returns isolated within ticker and no fill;
- crypto native-calendar calculation before equity-date selection;
- monthly decision/effective-date boundary;
- future-data perturbation does not change earlier weights;
- capped-simplex feasibility and determinism;
- all four methods obey constraints;
- deterministic fallback;
- drifted weights;
- initial and later turnover;
- cost deduction;
- 252 versus 365 metrics;
- output schemas, uniqueness and date ordering.

Use synthetic fixtures for unit tests so most tests do not require network data.
Retain the supplied smoke tests.

============================================================
6. Verification and records
============================================================

Run:

python scripts/run_part_b.py
pytest -q
python scripts/check_handin.py
git diff --check
git status --short

Perform independent checks on generated outputs:

- exactly 12 fund IDs;
- no duplicate date-fund rows;
- no duplicate effective-date-fund-ticker weight rows;
- each target-weight group sums to one within tolerance;
- no weight is negative or above its recorded cap;
- every return date is on the correct universe calendar;
- first live dates occur after the required estimation windows;
- earlier weights are unchanged by a future-return perturbation test;
- gross/net reconciliation is exact;
- report all solver failures and fallback counts honestly;
- no raw data, cache, secret or OS metadata is tracked.

Create:
ai/interaction_002_data_and_oos_fund_engine.md

Preserve this complete prompt verbatim and include:
- files read and changed;
- final locked decisions;
- data source actually used;
- commands;
- tests;
- key audit counts;
- solver/fallback findings;
- anything wrong or risky;
- what was checked or corrected;
- exact changed-file list.

Do not interpret which fund is “best” and do not tune any method after viewing
results. Do not implement sentiment, fusion, figures, report or Streamlit.

Make two commits after validation:

docs: clarify AI workflow roles
feat: build walk-forward fund engine

Report both commit hashes and final git status.
```

## Scope and outcome

This interaction implemented only the inherited data foundation and the walk-forward portfolio engine. It generated the five requested portfolio CSV files. It did not implement sentiment, fusion, figures, report content, or Streamlit, and it makes no claim about which fund is best.

## AI workflow correction

`ai/AI_NOTES.md` was corrected to distinguish the tools accurately: ChatGPT was used for course-material review and project planning and will be used for independent audit; Codex was used for repository work, documentation, and implementation. The former broad approval claim was replaced with the exact working-design-baseline statement supplied in the prompt. The file remains a living first-person draft and does not claim that later work is complete or approved.

## Files read

Project B reads included:

- `AGENTS.md`
- `context/PART_A_HANDOFF.md`, `context/PROJECT_DECISIONS.md`, `context/DATA_GUIDE.md`, `context/project_context.md`, and `context/verify_ai_output.md`
- `ai/README.md`, `ai/prompt_log_template.md`, `ai/AI_NOTES.md`, and the Interaction 001 log
- `src/data_access.py`, `src/etl.py`, `src/features.py`, and `src/portfolios.py`
- `scripts/run_part_b.py`, `scripts/check_handin.py`, `tests/test_smoke.py`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`, `README.md`, and `CLAUDE.md`
- the complete attached Interaction 002 prompt

Read-only reference inspection was limited to the Part A ETL/features implementations and their three inherited regression-test files identified in `context/PART_A_HANDOFF.md`, plus the Week 5 OOS portfolio engine and its tests identified by that handoff. No Part A or course-week file was modified.

## Final locked decisions

Before analytical code was written, `context/PROJECT_DECISIONS.md` was updated to lock:

- last-observed-calendar-month decision dates, information through the decision, next-observed-month effective dates, and no unusable terminal decision;
- causal asset eligibility, complete-row estimation, initial-window enforcement, no return filling, and explicit missing-realised-return handling;
- fixed 10% diagonal covariance shrinkage and fixed 50% cross-sectional mean shrinkage for Maximum Sharpe;
- SLSQP with `maxiter=1000` and `ftol=1e-10`, capped equal-weight starts, the four objective definitions, required validation tolerances, and explicit fallback;
- deterministic capped-simplex bisection projection;
- initial and drifted later turnover, 10 bps one-way cost, and exact rebalance/non-rebalance net-return accounting;
- the exact twelve lowercase identifiers, including the required `*_min_variance` suffix.

No parameter was selected after comparing portfolio performance.

## Official data source actually used

No `project_data.zip` was found under `/Users/chris/Desktop/fins 5545`, and no local `FINS_DATA_ZIP` override was used. The first sandboxed runner attempt could not resolve either official host. After the official-data network request was explicitly authorised, the unchanged frozen loader successfully used its supplied primary URL:

`https://drive.google.com/uc?export=download&id=1h0Wy12_qgR_NZJqtSxI9LwPEVKgp5DzH`

The backup URL was not needed on the successful run. No other data source was used, no raw ZIP or parquet file was written into the repository, and no data were fabricated.

## Commands and validation

Commands used included:

- `rg --files -g 'project_data.zip' '/Users/chris/Desktop/fins 5545'`
- `python scripts/run_part_b.py` (one sandbox DNS failure, then successful authorised official-loader runs; rerun after the fund-ID correction)
- `pytest -q tests/test_data_foundation.py tests/test_portfolio_methods.py tests/test_walk_forward.py` — 19 passed
- `pytest -q` — 21 passed, including the retained official-data smoke tests
- `python scripts/check_handin.py` — 20 checks passed, no failures, and three expected reminders
- `git diff --check` — passed
- `git status --short`
- independent pandas checks of schemas, keys, calendars, windows, weights, accounting, missingness, solver status, and fallback counts
- `git ls-files` guards for raw data, caches, secrets, OS metadata, parquet, and compiled Python artifacts

The hand-in reminders were expected at this scoped stage: generated Python cache exists locally but is ignored and untracked; no report exists; and `sector_sentiment_index.csv` does not exist because sentiment and report work were explicitly prohibited in this interaction.

## Tests and independent checks

Synthetic tests cover ticker-isolated `adjClose.pct_change(fill_method=None)`, missing-price propagation, native-calendar crypto calculation before equity-date selection, monthly decision/effective boundaries, future-return perturbation, capped-simplex feasibility/determinism, all four methods' constraints, forced solver fallback, exact drift recursion, initial/later union turnover, cost deduction, 252/365 metrics, missing held returns, schemas, unique keys, stable ordering, and latest current holdings.

Independent output checks confirmed:

- exactly 12 required fund IDs;
- 10,404 date-fund return rows with no duplicate date-fund key;
- 17,280 weight rows with no duplicate effective-date-fund-ticker key;
- 36 live monthly rebalances per fund;
- target-weight sums with maximum absolute error about `1.02e-13`;
- no negative target weight and no recorded-cap violation;
- Equity and Combined returns only on observed equity dates; Crypto retains native weekend dates;
- first live dates after the required estimation histories;
- zero missing live gross or net fund returns in the official run;
- exact gross/net reconciliation;
- 132 recorded pre-live skips across all fund-method schedules while initial histories were insufficient;
- no raw data, cache, secret, OS metadata, parquet, or compiled Python artifact tracked.

Data audits reconciled 50,300 raw/clean equity price rows, 14,620 raw and 14,610 clean crypto price rows after excluding the ten 2024-01-01 rows, and 149,683 raw and 146,836 clean news rows after removing 2,847 exact headline-key duplicates. Wide-panel missing cells are only the expected first native returns: 50 Equity, 10 Crypto, and 50 Combined.

## Solver and fallback findings

All final weight groups are feasible. Five Crypto Risk Parity decisions used the explicit `previous_feasible_target` fallback: 2021-04-30, 2022-12-31, 2023-01-31, 2023-06-30, and 2023-08-31. In each case SLSQP returned status 8 (positive directional derivative) and an invalid raw sum-to-one result. The audit records `solver_success=False`, `fallback_used=True`, the message, and the feasible fallback; none was silently labelled successful. All other live solves used their direct or SLSQP result.

## What was wrong or risky

- The first implementation derived fund IDs directly from the method name and therefore produced `*_minimum_variance`, while the complete prompt required `*_min_variance`. Verbatim prompt review caught this before final validation and commit.
- The first sandboxed official-data run failed at DNS resolution. Treating that as a data result or substituting another dataset would have been wrong.
- Return filling, differencing crypto only after equity alignment, forming weights from holding-period data, static rather than drifted turnover, and silently accepting solver failures would each bias the backtest.
- Risk Parity had five genuine numerical failures. Hiding, projecting, or retrospectively tuning them would misrepresent solver performance.
- The hand-in checker mechanically says “ready to zip and deploy” when blocking checks pass; this interaction does not claim the absent sentiment artifact, report, app work, deployment, or hand-in is complete.

## What was checked or corrected

- Corrected the AI role and approval language while retaining the living-draft status.
- Locked unresolved portfolio choices before implementation.
- Corrected the stable Minimum Variance fund-ID suffix from `minimum_variance` to `min_variance` and regenerated every output.
- Used only the frozen official loader and confirmed the successful primary URL.
- Ported the approved Part A no-fill/native-calendar behaviours into standalone Project B code rather than importing Project A.
- Added deterministic projection, solver validation/fallback, walk-forward timing, drift, turnover, cost, metrics, holdings, and audit functions with synthetic regression tests.
- Reproduced outputs from code and did not manually edit generated CSVs.
- Preserved the complete substantive prompt above rather than summarising it.

## Exact changed-file list

1. `ai/AI_NOTES.md`
2. `ai/interaction_002_data_and_oos_fund_engine.md`
3. `context/PROJECT_DECISIONS.md`
4. `scripts/run_part_b.py`
5. `src/etl.py`
6. `src/features.py`
7. `src/portfolios.py`
8. `tests/test_data_foundation.py`
9. `tests/test_portfolio_methods.py`
10. `tests/test_walk_forward.py`
11. `results/data/fund_returns.csv`
12. `results/data/fund_weights.csv`
13. `results/tables/performance_metrics.csv`
14. `results/tables/solver_audit.csv`
15. `results/tables/portfolio_data_audit.csv`

No `src/data_access.py`, sentiment/fusion module, figure, report file, `streamlit_app.py`, Part A file, course material, or other supplied context file was changed.
