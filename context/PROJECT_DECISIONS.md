# Project B predeclared decisions

Status: portfolio and sentiment methodologies are locked, implemented, and technically reviewed through Interaction 003. Interaction 004 implemented the fixed fusion design and focused fusion figures, which remain pending review. No economic conclusion or fusion result has been approved; report and app work remain pending.

## Product

- Name: **Cross-Asset Allocation Lens**.
- Target user: a self-directed investor or junior portfolio analyst comparing systematic multi-asset funds.
- Product journey: compare fund universes and methods, inspect fact sheets, review equity-sector sentiment, and simulate an allocation across funds over their common OOS period.
- The product is analytical and educational, not personalised advice or a promise of returns.

## Fund menu

- Universes: **Equity**, **Crypto**, and **Combined**.
- Methods in every feasible universe: **Equal Weight**, **Minimum Variance**, **Risk Parity**, and **Maximum Sharpe**.
- Each universe-method pair is a separate investable prototype fund and receives its own metrics and current holdings.

## Backtest design

- Evaluation: expanding walk-forward out-of-sample backtest.
- Initial estimation window: 252 observations for Equity and Combined; 365 observations for Crypto.
- Rebalancing calendar: the decision date is the last observed return-panel date in each calendar month. The training sample includes information through that decision date. Target weights first become effective on the first observed return-panel date in the next calendar month. A final decision date with no following observation is not formed or reported.
- Information boundary: the estimation window ends on the decision date; target weights first apply on the next holding-period observation. No holding return may influence its own weights.
- Eligibility: use only information available through the decision date and enforce the common sample end of 2023-12-31. An asset must have a valid return on the decision date and at least the applicable initial-window count of valid historical returns through that date. Covariance and expected-return estimation use only complete historical rows across the assets eligible at that decision. If fewer than the applicable initial-window count of complete rows remains, skip and record the decision. Never fill missing returns. If a held asset has a missing realised return, report a missing fund return and an audit warning rather than impute it.
- Constraints: fully invested, long-only, and per-asset maximum weight `min(35%, 5 / number_of_assets)` using the eligible asset count at that decision. Validate finite weights, the fully invested sum to `1e-8`, the lower bound to `1e-10`, and the maximum-weight bound to `1e-8`.
- Covariance estimator: sample covariance with fixed 10% diagonal shrinkage, `0.9 * sample_covariance + 0.1 * diag(sample_covariance)`. This fixed value is not tuned.
- Maximum-Sharpe expected returns: expanding arithmetic means through the decision date, shrunk 50% toward their cross-sectional mean. This fixed value is not tuned.
- Optimisation: SciPy SLSQP with `maxiter=1000` and `ftol=1e-10`. Minimum Variance minimises portfolio variance. Maximum Sharpe maximises expected return divided by volatility. Risk Parity minimises squared deviations of asset risk contributions from their equal-risk-contribution target. Equal Weight is the capped equal-weight benchmark.
- Capped-simplex projection: use a deterministic Euclidean projection found by bisection of a common threshold, `clip(v - threshold, 0, cap)`, and validate feasibility, determinism, full investment, and bounds.
- Risk-free rate: zero for optimisation and Sharpe calculations.
- Return construction: simple adjusted-close returns within ticker, with no price forward filling.
- Combined calendar: calculate crypto returns first on the native seven-day calendar, then select those return observations onto equity trading dates. Do not merge price levels and then difference.
- Annualisation: Equity and Combined use 252; Crypto uses 365. Annualised mean return is daily arithmetic mean times the applicable factor, annualised volatility is daily sample standard deviation times the square root of that factor, and Sharpe is annualised mean excess return divided by annualised volatility. Growth of $1 and drawdown use compounded simple returns.
- Gross/net accounting: report gross return, turnover, cost, and net return separately. The initial investment has turnover 1.0. Later one-way turnover is `0.5 * sum(abs(target_weight - pretrade_drifted_weight))` over the union of old and new assets. Trading cost is `0.001 * turnover` (10 bps one-way). On an effective rebalance date, net return is `(1 - cost) * (1 + gross_return) - 1`; on other dates net return equals gross return.
- Solver fallback: record method, date, solver, success flag/message, and fallback use. On failure or infeasible/non-finite output, reuse the previous feasible target for that universe-method if it remains feasible for the current eligible universe; otherwise use capped equal weight. Never substitute silently.
- Investor simulator: use the intersection of available OOS fund-return dates, display the common period explicitly, and apply user allocations only to precomputed fund returns.

## Stable fund identifiers

- `equity_equal_weight`
- `equity_min_variance`
- `equity_risk_parity`
- `equity_max_sharpe`
- `crypto_equal_weight`
- `crypto_min_variance`
- `crypto_risk_parity`
- `crypto_max_sharpe`
- `combined_equal_weight`
- `combined_min_variance`
- `combined_risk_parity`
- `combined_max_sharpe`

## Sentiment design

- Baseline: plain VADER.
- Main model: finance-extended VADER using the frozen approved artifact `resources/finance_vader_lexicon.csv`. Its SHA-256 is `4c16eeab9edec5c970234d0a30bcbd89c84c21abf94e4677b8b9568c8b6a28c6`.
- Text input: the raw supplied headline title unchanged. Preserve casing, punctuation, boosters, contrast, and negation; do not score the Part A descriptive-token copy.
- Aggregation: score each headline; take the arithmetic mean within ticker and mapped equity day; then take an equal-weight mean across observed ticker-days within sector and day.
- Missingness: a ticker-day with no supplied headline is missing, not zero and not neutral. Sector coverage is the number of sector tickers with at least one supplied mapped headline divided by the number of eligible sector tickers.
- Calendar and lag: use inherited Rule A, then lag the sector signal by exactly one equity trading day before it can affect holdings.
- Trading standardisation: expanding, causal z-scores with a minimum of 252 available historical sector observations; the mean and sample standard deviation at a signal date use only values available through that signal date. A zero/undefined historical standard deviation yields a missing z-score, not zero.
- Descriptive standardisation: a full-sample z-score may be used only in clearly labelled historical figures and must never enter portfolio weights.
- Missing-sector carry: after lagging, carry the last available sector z-score for at most five equity trading days. Its effective coverage decays linearly by multiplying the source-day coverage by `(6 - age) / 6` for ages 1 through 5. From age 6 onward the signal is missing and no tilt is applied.

### Frozen finance lexicon provenance and installation

- Reproduce the local Week 8 approved workflow from:
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/09_build_finance_lexicon.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/10_extend_and_test_vader.py`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/provided_data/candidate_terms.txt`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/provided_data/raw_ratings/rater_01.txt` through `rater_10.txt`
  - `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/vader_model/provided_data/human_review.csv`
- The workflow aggregates 390 frozen integer ratings for 39 candidate terms across 10 raters using the arithmetic mean and sample standard deviation, rounds both to three decimals, requires `sd_rating < 2.5` and `abs(mean_rating) >= 0.5`, and then requires the recorded human decision `approve`.
- The frozen approved set contains 29 terms: 20 single words and 9 phrases. Ten terms are rejected. The approved artifact is byte-identical to the Week 8 output `output/tables/09_finance_lexicon_approved.csv`; neither approvals nor values may be edited after observing Project B results.
- Approved single words update only the finance analyser's lexicon. An approved exact-token collision with base VADER uses the frozen finance value. Approved phrases use the course `SPECIAL_CASES` treatment and add a missing final head word at `+0.1` or `-0.1` according to phrase direction so VADER checks the phrase.
- Preserve the course booster candidates: `sharply`, `materially`, and `steeply` use `B_INCR`; `modestly` and `marginally` use `B_DECR`; only candidates absent from the base booster dictionary are added. Plain and finance analysers must remain isolated so module-level phrase or booster state cannot contaminate the other model or later tests.
- Changed finance-term coverage, a changed compound score, or a changed sector index is not evidence of improved predictive accuracy without separate labelled validation.

### Sector membership and coverage

- Derive ticker-sector membership only from cleaned official equity prices and reject inconsistent mappings.
- On an observed equity date, an eligible sector ticker is a mapped equity ticker with a finite adjusted-close simple return on that date.
- Observed ticker count is the number of eligible sector tickers with at least one supplied headline mapped to that date. Coverage is `observed_ticker_count / eligible_ticker_count`; it is missing when the denominator is zero.
- A ticker-day without a supplied headline remains missing. A sector-day with no observed ticker sentiment remains missing. Never replace either with zero or neutral sentiment.

### Sector signal construction

- Score each distinct original unmodified headline title once with isolated plain and finance-extended VADER analysers, then join scores back to the valid Rule A rows.
- Apply Rule A before sentiment aggregation. Take an arithmetic mean from headlines to ticker-day, then an equal-weight arithmetic mean across observed eligible ticker-days to sector-day.
- For both `plain_vader` and `finance_vader`, transform sector compound to the descriptive index `50 * (compound + 1)`.
- Calculate full-sample z-scores only as labelled descriptive fields. Calculate trading z-scores causally and separately by sector and model with an expanding mean and sample standard deviation, at least 252 available historical sector observations, and information through the source date only. Zero or undefined standard deviation produces a missing z-score.
- Shift a completed source-date causal z-score by exactly one observed equity trading day. At the first eligible effective date its age is 0. If subsequent source days are wholly missing, carry ages 1 through 5 only and set effective coverage to `source_coverage * (6 - age) / 6`. At age 6 onward, the signal and effective coverage are missing. Full-sample z-scores never enter the trading signal.

## Fusion design

- Primary augmented fund identity:
  - fund ID: `equity_risk_parity_sentiment`;
  - universe: `equity`;
  - method: `risk_parity_sentiment`;
  - base fund: `equity_risk_parity`;
  - sentiment model: `finance_vader` only.
- Timing: use the `finance_vader` row from the causal sector-sentiment signal whose `effective_date` equals the base portfolio target's `effective_date`. For an age-zero signal, `source_date` equals the portfolio `decision_date`, and the target becomes investable on the following observed equity date. A carried signal must have a strictly earlier `source_date`. Every active `source_date` must be on or before the decision date; no later signal may affect the target.
- Prohibited inputs: `plain_vader` and `descriptive_full_sample_z` must not enter the primary overlay.
- Extension: coverage-aware finance-sentiment overlay at the sector level.
- Fixed tilt strength: `lambda = 0.10`; it will not be tuned on the full OOS sample.
- For sector `s` and decision date `t`, set `z_bounded = clip(causal_lagged_z, -2, 2)` and `multiplier = clip(1 + lambda * effective_coverage * z_bounded, 0.80, 1.20)`. A missing signal uses multiplier 1.0.
- Multiply every base Equity Risk Parity stock weight by its sector multiplier, renormalise, and enforce the same long-only maximum-weight constraint using a deterministic capped-simplex projection.
- The augmented target is held and drifted independently, and its turnover is calculated against its own pre-trade drifted weights. Its daily return is recalculated from its own holdings and the underlying equity returns, not copied from the base fund.
- If no sector has an active signal at a rebalance, the augmented target equals the exact base target within numerical tolerance.
- Evaluate base versus augmented annualised performance, Sharpe, maximum drawdown, gross return, turnover, trading cost, and net return over exactly the same OOS dates. A negative result remains reportable and does not justify retuning.

## Innovation claims to test later

- Coverage-aware finance-sentiment overlay with explicit missingness and staleness controls.
- Turnover and transaction-cost analysis for every fund.
- Investor allocation simulator using only the common precomputed OOS period.

These are design claims only until implemented and evaluated.

## Unresolved implementation details

The following must be resolved in a later documented decision before code or empirical output relies on them:

1. Figure design, report exhibit mapping, and app controls beyond the fixed product journey. These presentation choices must not alter the methodology.

No unresolved item may be filled in by convenience after viewing full-sample results. Record the decision, rationale, and tests first.
