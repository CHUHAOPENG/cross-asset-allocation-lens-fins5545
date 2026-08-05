# Project B permanent instructions

## Scope and boundaries

- Work only inside `z5711503_projectB`. Treat `z5711503_projectA`, course-week folders, and the supplied Project B files `context/DATA_GUIDE.md`, `context/project_context.md`, and `context/verify_ai_output.md` as read-only.
- Use Part A only through the approved handoff in `context/PART_A_HANDOFF.md`. Do not copy the Part A tree or raw data.
- Follow `context/PROJECT_DECISIONS.md`. Never change a parameter, estimator, constraint, calendar rule, mapping rule, cost rule, or model silently. Record and approve a decision change before implementation.
- Do not invent data, results, citations, course requirements, provenance, or student approval. Flag uncertainty and distinguish a design choice from an empirical result.

## Inherited data rules

- Load official data through `src/data_access.py`; never commit raw CSV or Parquet files. Preserve source paths, schemas, row reconciliations, parameters, package versions, and output provenance.
- Reuse Part A cleaning and Rule A calendar logic deliberately. Preserve original UTC timestamps and map a headline's UTC calendar date to the same observed cleaned-equity trading date or, if absent, the next one.
- Calculate simple returns within ticker on adjusted close using the native calendar and no fill. Never forward-fill prices. Calculate crypto returns on the native seven-day calendar before selecting them onto equity dates for Combined funds.
- Enforce no look-ahead: a holding period may use only information available strictly before it. Equity and Combined metrics use 252 periods per year; Crypto metrics use 365.

## Funds and sentiment

- Build Equity, Crypto, and Combined universes with Equal Weight, Minimum Variance, Risk Parity, and Maximum Sharpe methods under the predeclared long-only and maximum-weight rules.
- Use expanding walk-forward OOS estimation, monthly rebalancing, a zero risk-free rate, recorded deterministic solver fallback, and the predeclared 10 bps one-way cost model. Report gross return, turnover, trading cost, and net return separately.
- Score unaltered headline text: preserve casing, punctuation, boosters, and negation. Plain VADER is the baseline and the predeclared finance-extended VADER is the main model.
- Aggregate headline to ticker-day and then equal-weight ticker-days to sector. A ticker-day with no supplied headline is missing, not neutral. Lag trading sentiment by one equity trading day and standardise it causally; full-sample standardisation is descriptive only.
- Carry a wholly missing sector signal for no more than five equity trading days under the predeclared staleness rule; afterwards apply no sentiment tilt.
- Apply only the fixed, bounded, coverage-aware sector tilt in `context/PROJECT_DECISIONS.md` to the Equity Risk Parity fund. Do not tune tilt strength on the full test sample.

## Outputs, app, and verification

- The mandatory app artifacts are exactly:
  - `results/data/fund_returns.csv`
  - `results/data/fund_weights.csv`
  - `results/data/sector_sentiment_index.csv`
  - `results/tables/performance_metrics.csv`
- Store derived app data in `results/data/`, report tables in `results/tables/`, and figures in `results/figures/`. The Streamlit app must read precomputed artifacts only; it must not run optimisers, backtests, VADER, or data downloads.
- Add focused tests for calendars, lagging, training/holding boundaries, constraints, fallback, turnover/costs, aggregation, missing-news semantics, standardisation, and output schemas. Run `pytest -q` and `python scripts/check_handin.py` before a milestone.
- Keep runs deterministic where practical. Record commands, inputs, parameters, warnings, test results, exact changed files, and verification/corrections in `ai/`. The student must review AI-written code, numbers, claims, and report prose.
- Preserve each substantive user prompt verbatim in its interaction log, maintain `ai/AI_NOTES.md` as a living first-person summary, and never claim student authorship or approval before it is actually provided.
- Do not commit secrets, caches, OS metadata, editor backups, or raw data. Do not push, deploy, publish, or claim GitHub/Streamlit/Moodle completion without explicit authorisation and direct verification.
