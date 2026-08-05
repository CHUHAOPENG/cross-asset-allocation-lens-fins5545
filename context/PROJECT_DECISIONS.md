# Project B predeclared decisions

Status: design baseline for Interaction 001. This file predeclares methodology before Project B empirical work. It does not claim that portfolios, sentiment scores, backtests, figures, or app artifacts exist.

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
- Rebalancing: monthly. The exact within-month decision-day convention is unresolved below and must be fixed before implementation.
- Information boundary: the estimation window ends on the decision date; target weights first apply on the next holding-period observation. No holding return may influence its own weights.
- Constraints: fully invested, long-only, and per-asset maximum weight `min(35%, 5 / number_of_assets)` using the eligible asset count at that decision.
- Risk-free rate: zero for optimisation and Sharpe calculations.
- Return construction: simple adjusted-close returns within ticker, with no price forward filling.
- Combined calendar: calculate crypto returns first on the native seven-day calendar, then select those return observations onto equity trading dates. Do not merge price levels and then difference.
- Annualisation: Equity and Combined use 252; Crypto uses 365. Annualised mean return is daily arithmetic mean times the applicable factor, annualised volatility is daily sample standard deviation times the square root of that factor, and Sharpe is annualised mean excess return divided by annualised volatility. Growth of $1 and drawdown use compounded simple returns.
- Gross/net accounting: report gross return, turnover, cost, and net return separately. One-way turnover at a rebalance is `0.5 * sum(abs(target_weight - pretrade_drifted_weight))`; the initial investment has turnover 1.0. Trading cost is `0.001 * turnover` (10 bps one-way) and is deducted once on the effective rebalance date.
- Solver fallback: record method, date, solver, success flag/message, and fallback use. On failure or infeasible/non-finite output, reuse the previous feasible target for that universe-method if it remains feasible for the current eligible universe; otherwise use capped equal weight. Never substitute silently.
- Investor simulator: use the intersection of available OOS fund-return dates, display the common period explicitly, and apply user allocations only to precomputed fund returns.

## Sentiment design

- Baseline: plain VADER.
- Main model: finance-extended VADER. The exact frozen lexicon artifact and collision precedence remain unresolved; once approved they must be versioned and must not change between scoring and reproduction.
- Text input: the raw supplied headline title unchanged. Preserve casing, punctuation, boosters, contrast, and negation; do not score the Part A descriptive-token copy.
- Aggregation: score each headline; take the arithmetic mean within ticker and mapped equity day; then take an equal-weight mean across observed ticker-days within sector and day.
- Missingness: a ticker-day with no supplied headline is missing, not zero and not neutral. Sector coverage is the number of sector tickers with at least one supplied mapped headline divided by the number of eligible sector tickers.
- Calendar and lag: use inherited Rule A, then lag the sector signal by exactly one equity trading day before it can affect holdings.
- Trading standardisation: expanding, causal z-scores with a minimum of 252 available historical sector observations; the mean and sample standard deviation at a signal date use only values available through that signal date. A zero/undefined historical standard deviation yields a missing z-score, not zero.
- Descriptive standardisation: a full-sample z-score may be used only in clearly labelled historical figures and must never enter portfolio weights.
- Missing-sector carry: after lagging, carry the last available sector z-score for at most five equity trading days. Its effective coverage decays linearly by multiplying the source-day coverage by `(6 - age) / 6` for ages 1 through 5. From age 6 onward the signal is missing and no tilt is applied.

## Fusion design

- Base fund: Equity Risk Parity.
- Extension: coverage-aware finance-sentiment overlay at the sector level.
- Fixed tilt strength: `lambda = 0.10`; it will not be tuned on the full OOS sample.
- For sector `s` and decision date `t`, set `z_bounded = clip(causal_lagged_z, -2, 2)` and `multiplier = clip(1 + lambda * effective_coverage * z_bounded, 0.80, 1.20)`. A missing signal uses multiplier 1.0.
- Multiply every base Equity Risk Parity stock weight by its sector multiplier, renormalise, and enforce the same long-only maximum-weight constraint using a deterministic capped-simplex projection.
- Evaluate base versus augmented annualised performance, Sharpe, maximum drawdown, gross return, turnover, trading cost, and net return over exactly the same OOS dates. A negative result remains reportable and does not justify retuning.

## Innovation claims to test later

- Coverage-aware finance-sentiment overlay with explicit missingness and staleness controls.
- Turnover and transaction-cost analysis for every fund.
- Investor allocation simulator using only the common precomputed OOS period.

These are design claims only until implemented and evaluated.

## Unresolved implementation details

The following must be resolved in a later documented decision before code or empirical output relies on them:

1. Whether the monthly decision date is the last available observation of each calendar month or another fixed monthly convention.
2. Asset eligibility rules for missing returns, listing history, and changing universes; the minimum-variance/covariance panel policy must not use future completeness.
3. Expected-return estimator for Maximum Sharpe, covariance estimator/regularisation for all optimisers, numerical tolerances, and exact solver choices.
4. The exact capped-simplex projection implementation and validation tolerances for weights, risk contributions, and constraint feasibility.
5. The frozen finance lexicon source, its package/version or checked-in artifact, term collision precedence, and an evaluation plan that distinguishes changed coverage from improved accuracy.
6. Output schemas beyond the four mandatory filenames, fund identifiers/display labels, and how solver/fallback audit rows are serialised.
7. Figure design, report exhibit mapping, and app controls beyond the fixed product journey. These presentation choices must not alter the methodology.

No unresolved item may be filled in by convenience after viewing full-sample results. Record the decision, rationale, and tests first.
