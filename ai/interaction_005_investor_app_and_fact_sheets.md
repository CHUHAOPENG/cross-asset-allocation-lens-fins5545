# Interaction 005 — Investor app, fund fact sheets and allocation lab

Date: 2026-08-05
Project: /Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectB

## Prompt

The complete original prompt is preserved verbatim from `/Users/chris/.codex/attachments/d58b300b-82f8-498a-9c1a-c5b1a1438807/pasted-text.txt`:

```text
Interaction 005 — Investor app, fund fact sheets and allocation lab

Read and follow AGENTS.md and context/PROJECT_DECISIONS.md.
Work only inside z5711503_projectB.

Interaction 004 has passed technical review. The 13-fund analytical results are
now frozen. Do not change portfolio, sentiment or fusion methodology, parameters
or analytical values. Do not write the final report, push or deploy.

============================================================
1. Record the reviewed Fusion result
============================================================

Update ai/AI_NOTES.md accurately:

- Interaction 004 implemented the fixed coverage-aware fusion overlay.
- CHUHAO PENG accepted its technical implementation after independent review.
- In this sample it did not outperform the base Equity Risk Parity fund and had
  higher turnover; this negative result must remain visible and must not cause
  retuning.
- App work is beginning; final report, economic narrative and deployment remain
  pending.
- Retain the living-draft status.

Update the status in context/PROJECT_DECISIONS.md:

- portfolio, sentiment and fusion are locked and technically reviewed through
  Interaction 004;
- record that the fixed overlay produced a modest negative sample result and
  higher turnover;
- state that this is descriptive OOS evidence, not proof against or for
  sentiment predictability;
- app and final report remain pending.

Before app work, freeze the SHA-256 hashes of the current Interaction 004
analytical outputs in:

resources/interaction_004_analytic_hashes.csv

Columns:
path,sha256

Include all existing analytical CSV and PNG outputs except run_manifest.csv.
Every later runner execution must verify that these frozen files remain
byte-identical unless a separately approved analytical correction is made.

The only approved visual correction is moving the overlapping legend in
fusion_sector_multiplier_activity.png. Regenerate that figure without changing
its data, then update only its frozen hash and document why.

============================================================
2. Lock the app product decisions
============================================================

Record these app decisions before implementation:

Product:
- name: Cross-Asset Allocation Lens;
- user: self-directed investor or junior portfolio analyst;
- purpose: compare systematic funds, inspect a fact sheet, test a fund-level
  allocation and review sentiment/fusion evidence;
- analytical and educational only, not personalised financial advice.

App data:
- read committed precomputed files under results/ only;
- never load official raw data;
- never call data_access, ETL, optimisation, backtest, VADER or fusion code;
- never download anything;
- all dates and sample periods must be visible.

Performance display:
- use net results as the default;
- allow gross/net comparison where useful;
- identify 252 versus 365 annualisation;
- label current holdings as “latest target weights from the most recent
  rebalance”, not live market holdings;
- disclose that management fees, taxes and investor-level cross-fund costs are
  not included.

Allocation simulator:
- use only precomputed fund net returns over the exact common OOS period;
- default method: buy-and-hold fund sleeves, so weights drift naturally;
- optional method: reset to the selected target allocation on the first
  available date of each calendar month;
- do not apply additional cross-fund transaction costs;
- clearly disclose this limitation;
- never optimise or recommend the user allocation;
- require non-negative allocations summing to 100%.

============================================================
3. Create app-ready metadata
============================================================

Add pure functions to scripts/run_part_b.py or a small dedicated build module to
generate:

results/data/fund_catalog.csv

Schema:
fund_id, display_name, universe, method, short_description,
first_live_date, last_date, periods_per_year,
is_sentiment_augmented, base_fund_id

Create clear display names for all 13 funds.

Generate:

results/data/fund_current_holdings.csv

Schema:
fund_id, as_of_date, ticker, asset_class, target_weight, holding_rank

Requirements:

- one latest-rebalance target snapshot per fund;
- Equity assets labelled equity;
- Crypto assets labelled crypto;
- Combined funds correctly distinguish both asset classes;
- weights sum to one per fund;
- `as_of_date` is that fund’s latest target effective date;
- stable ordering by fund and descending weight.

Add both outputs and hashes to run_manifest.csv.

============================================================
4. Implement pure app utilities
============================================================

Create src/app_utils.py without importing Streamlit.

Implement tested functions for:

- loading committed app artifacts from a supplied root;
- exact schema and unique-key validation;
- fund labels and filtered comparison tables;
- common OOS period for selected funds;
- buy-and-hold allocation simulation;
- monthly target-reset allocation simulation;
- portfolio growth, drawdown and annualised metrics;
- latest target holdings;
- selected-fund weight history;
- sentiment time-series filtering;
- latest sector sentiment snapshot;
- base-versus-augmented fusion summary.

Allocation formulas:

Buy-and-hold:
- allocate one initial dollar across sleeves using the selected weights;
- compound each sleeve independently using its fund net returns;
- total portfolio value is the sum of sleeve values;
- do not reset weights after inception.

Monthly reset:
- begin with selected target weights;
- allow sleeves to drift daily;
- on the first available common-period date of each new calendar month, reset
  sleeve values to target weights using the previous total portfolio value;
- do not deduct additional cross-fund trading costs;
- record rebalance dates for disclosure.

Use only intersecting dates with finite selected-fund net returns.
Do not silently fill missing returns.

============================================================
5. Replace the starter Streamlit app
============================================================

Replace streamlit_app.py completely.

It must import only lightweight app dependencies and src.app_utils.
It must not import:

- src.data_access
- src.etl
- src.features
- src.portfolios
- src.sentiment
- src.fusion

Use cached loading of precomputed committed artifacts.

Create a coherent custom visual system:

- original app title and short value proposition;
- consistent accessible colour palette;
- clear typography and spacing;
- responsive wide layout;
- concise methodology and risk explanations;
- no claims that past results predict future performance.

Use five primary sections or tabs.

A. Fund Explorer

- filter by Equity, Crypto, Combined and Sentiment-Augmented;
- sortable comparison table;
- annualised return-versus-volatility scatter;
- select multiple funds for net or gross growth comparison;
- drawdown comparison;
- explicitly show each selected fund’s OOS period.

B. Fund Fact Sheet

For every one of the 13 funds:

- fund name, universe and method;
- OOS first and last date;
- growth of $1;
- annualised return;
- annualised volatility;
- Sharpe ratio;
- maximum drawdown;
- cumulative return;
- turnover and trading cost;
- fallback count where relevant;
- latest target holdings;
- top-holdings chart and full downloadable table;
- target-weight history through time;
- method and calendar explanation;
- 252/365 annualisation note.

Do not call the latest rebalance target a real-time holding.

C. Allocation Lab

- allow the user to select 2–6 funds;
- editable non-negative percentage allocations;
- validate that allocations total 100%;
- choose Buy & Hold or Monthly Reset;
- show the exact common OOS period;
- calculate from precomputed net returns only;
- show growth, drawdown, cumulative return, annualised return, volatility,
  Sharpe and maximum drawdown;
- allow download of the simulated daily series;
- disclose no extra management fee, tax or cross-fund transaction cost.

D. Sentiment Lab

- sector and model selectors;
- show `index_0_100` through time with genuine missing gaps;
- show coverage through time;
- optionally show causal z-score, clearly separated from descriptive index;
- latest sector snapshot;
- explain Rule A, one-trading-day lag, missing-news semantics and the frozen
  finance lexicon;
- never replace missing sentiment with 50 in the app.

E. Fusion Evidence

- compare Equity Risk Parity with the fixed sentiment-augmented version;
- show base and augmented metrics over identical dates;
- growth and drawdown;
- turnover and transaction-cost difference;
- sector-multiplier activity;
- latest base-versus-augmented target holdings;
- derive a neutral summary from fusion_comparison.csv;
- explicitly state that the overlay underperformed in this sample and was not
  retuned;
- do not describe either fund as universally better.

The app must fail gracefully with an actionable message if an artifact is
missing or has the wrong schema.

Add a visible data/sample disclosure and educational-use disclaimer.

Use Plotly for interactive charts and add an appropriate bounded Plotly
dependency to requirements.txt.

============================================================
6. App and artifact tests
============================================================

Add synthetic tests for src/app_utils.py covering:

- artifact schema validation;
- exact 13 fund catalogue IDs;
- current-holding weights sum to one;
- common-period calculation;
- buy-and-hold arithmetic;
- monthly reset timing and arithmetic;
- allocation rejection when negative or not equal to 100%;
- no missing-return imputation;
- metric and drawdown calculation;
- sentiment missing gaps remain missing;
- latest sentiment snapshot;
- fusion comparison uses identical dates.

Add app-level checks:

- streamlit_app.py contains no data_access or analytical-engine imports;
- Streamlit AppTest starts without an uncaught exception;
- all five investor-journey sections are present;
- every one of the 13 funds can render a fact-sheet selection;
- the app does not access the network;
- deployed requirements contain everything needed by the app and exclude
  vaderSentiment.

Keep vaderSentiment only in requirements-dev.txt for reproduction.

============================================================
7. Runner, presentation correction and validation
============================================================

Update scripts/run_part_b.py to:

- reproduce all existing analytics exactly;
- generate fund_catalog.csv and fund_current_holdings.csv;
- regenerate the Fusion multiplier figure with the legend outside the data
  region;
- update run_manifest.csv;
- verify all frozen Interaction 004 analytical hashes;
- permit only the documented figure-presentation hash change;
- never run Streamlit during the analytical runner.

Run:

python scripts/run_part_b.py
pytest -q
python scripts/check_handin.py
git diff --check
git status --short

Run an app health check:

1. launch Streamlit headlessly on a temporary local port;
2. query its health endpoint;
3. stop the process cleanly;
4. record the command, HTTP result and shutdown.

Also run Streamlit AppTest if available.

Independently verify:

- exactly 13 catalogue entries;
- every fund has a fact-sheet route/selection;
- holdings sum to one for each fund;
- original analytical CSV values are unchanged;
- no app code imports or executes analytical engines;
- no app network access;
- allocation simulation uses only selected common-period net returns;
- no missing value is silently filled;
- app labels latest target weights correctly;
- sentiment gaps remain gaps;
- Fusion negative result remains visible;
- manifest hashes match;
- no raw data, secret, cache or OS metadata is tracked.

Create:

ai/interaction_005_investor_app_and_fact_sheets.md

Preserve this complete prompt verbatim and record:

- files read and changed;
- reviewed Fusion conclusion;
- frozen analytical hashes;
- app design decisions;
- app artifact counts;
- allocation-method formulas;
- test and health-check results;
- anything wrong or risky;
- what was checked or corrected;
- exact changed-file list.

Commit:

docs: record reviewed fusion result
feat: build investor app and fund fact sheets

Report both commit hashes, app health-check result, exact changed-file list and
final git status.
```

## Files read

- `AGENTS.md`
- `context/PROJECT_DECISIONS.md`
- `ai/AI_NOTES.md`
- `ai/README.md`
- `ai/prompt_log_template.md`
- `requirements.txt`
- `requirements-dev.txt`
- `streamlit_app.py`
- `scripts/run_part_b.py`
- `src/fusion.py`
- the existing tests and all Interaction 004 CSV/PNG outputs
- the original Interaction 005 attachment named above

The app quality workflow also checked the dashboard brief, source boundary, metric consistency, default view, filters, missing states, and Streamlit-specific runtime validation. Supplied context files other than the approved decisions file, Part A, course materials, report files, and deployment state were not changed.

## Reviewed Fusion conclusion

CHUHAO PENG accepted Interaction 004's technical implementation after independent review. The fixed coverage-aware overlay had a lower net cumulative return than base Equity Risk Parity in this OOS sample by approximately `0.011906` and higher total turnover by approximately `0.521652`. This negative sample result remains visible in the app and did not cause retuning. It is descriptive OOS evidence, not proof for or against sentiment predictability and not a universal fund ranking.

## Frozen analytical hashes and presentation correction

- Before app implementation, 20 existing Interaction 004 analytical CSV/PNG outputs other than `run_manifest.csv` were recorded and verified in `resources/interaction_004_analytic_hashes.csv`.
- The sole approved analytical-file change was moving the multiplier-activity legend out of the data region. The underlying `fusion_sector_multipliers.csv` remained byte-identical.
- The corrected figure hash changed from `2953d764a74862170e436cc69a337896e0a12c8d51e7ef5ab51d12716398b3b0` to `9985f589a0dbe7a5b3d20c38a8fb45d1863d7908733ea01ed4e0635969ab994a`. The other two Fusion figure hashes remained unchanged.
- The runner verifies all 20 frozen hashes both before and after reproduction. The final independent audit verified all 20 again.

## App design decisions

- The product is **Cross-Asset Allocation Lens**, for a self-directed investor or junior portfolio analyst. It is analytical and educational only.
- The App reads cached committed artifacts under `results/` only. It imports no analytical engine, loads no official raw data, and contains no network client.
- Net performance is the default; gross comparison is optional. Every selected period and 252/365 annualisation convention is visible.
- Holdings are consistently labelled “latest target weights from the most recent rebalance,” not live holdings.
- The five investor-journey tabs are Fund Explorer, Fund Fact Sheet, Allocation Lab, Sentiment Lab, and Fusion Evidence. Plotly provides interactive charts under a consistent accessible palette.
- Management fees, taxes, and investor-level cross-fund transaction costs are explicitly excluded. Past OOS evidence is not presented as predictive or personalised advice.

## App artifacts and allocation formulas

- `fund_catalog.csv`: 13 rows, one per approved fund, with unique display names and the augmented fund linked to `equity_risk_parity`.
- `fund_current_holdings.csv`: 530 rows. Each fund uses its latest target effective date, each fund's weights sum to one within `1e-8`, and Combined funds distinguish equity and crypto assets.
- Buy & Hold starts with one dollar split by the selected weights, compounds each fund sleeve independently using only that fund's precomputed net return, and never resets the sleeve weights.
- Monthly Reset begins at the selected weights, permits daily sleeve drift, and on the first available common-period date of each calendar month resets sleeve values using the previous total portfolio value. The initial allocation and each reset date are recorded.
- Both methods use only the exact selected-fund date intersection with finite net returns. A common-date missing or non-finite value is excluded and disclosed; nothing is filled. No additional cross-fund cost is deducted.

## Commands, tests, and health check

- `python scripts/run_part_b.py` completed against the official Google Drive source ZIP with SHA-256 `9740a68c63e4edf2fbe03d91a5356728e9355a1070580052b66893d4c7463010`. It reproduced 13 funds, verified 20 frozen analytics, created 13 catalog rows and 530 holding rows, and produced a 103-row manifest.
- The initial AppTest identified a presentation-layer merge bug: duplicate OOS date columns were suffixed during the catalogue/metrics join. The utility was corrected to retain the catalog dates explicitly, and a regression test was added.
- `pytest -q`: `73 passed in 12.00s`. Streamlit AppTest was available; its focused suite passed 16 tests, including every one of the 13 fact-sheet selections.
- The first headless launch attempt was blocked by the sandbox's local-port restriction. The authorised localhost-only command was `streamlit run streamlit_app.py --server.headless true --server.address 127.0.0.1 --server.port 8765 --browser.gatherUsageStats false`.
- `GET http://127.0.0.1:8765/_stcore/health` returned HTTP `200`, content type `text/plain; charset=utf-8`, and body `ok`.
- Ctrl-C produced `Stopping...` and exit code `0`; a follow-up listener check found no process on port 8765.
- Final checks also ran `python scripts/check_handin.py`, `git diff --check`, and `git status --short`.

## Anything wrong or risky

- The starter App imported a raw-data loader and downloaded data at runtime. That violated the frozen/precomputed App boundary and was replaced completely.
- The first AppTest exposed the OOS-date merge error described above. Without AppTest, the default Explorer route would have failed before rendering.
- A date union can be mistaken for a common period. The utility now intersects actual per-fund date sets first; it does not classify non-shared crypto weekend dates as missing common observations.
- Monthly resets could be implemented with the current total after the reset-day return, causing a timing error. The implementation resets using the previous total before applying the new month's first return.
- Calling latest targets “current” or “live” would be misleading. Visible labels and tests protect the approved wording.
- Native interactive charts and allocation transforms can accidentally hide missing values. The utility never fills returns, sentiment Plotly traces use `connectgaps=False`, and 476 actual missing sentiment-index rows remain present.
- The App uses historical precomputed outputs and provides no recommendation. Its negative Fusion conclusion and excluded fee/cost limitations remain visible.
- The hand-in checker initially treated the required analytical-hash CSV as prohibited raw data because its derived-resource allowlist contained only the finance lexicon. The exact hash-manifest path was added to that narrow allowlist; no general CSV exception was introduced.

## What was checked or corrected

- Verified exact schemas and unique keys for every loaded App artifact and graceful actionable errors for missing or malformed files.
- Verified exactly 13 catalog entries, all 13 fact-sheet selections, 530 latest target rows, per-fund sums, latest effective dates, holding ranks, and Combined asset classes.
- Verified buy-and-hold arithmetic, monthly-reset timing/arithmetic, allocation constraints, growth, drawdown, annualisation, exact common periods, and no missing-return imputation.
- Verified sentiment filtering preserves gaps, latest snapshots do not carry values, and Fusion comparison periods are identical.
- Parsed App imports independently: only standard-library path handling, pandas, Plotly, Streamlit, and `src.app_utils` are used. No network client is present.
- Verified 20 frozen analytical hashes and 22 manifest artifact hashes; the manifest records the actual pre-run documentation commit.
- Verified deployed requirements include bounded Plotly and no runtime sentiment scorer; the pinned scorer remains in `requirements-dev.txt` for reproduction.
- Updated the hand-in checker to recognise only the required analytical-hash manifest as an additional allowed derived resource.
- No report, deployment, Part A, raw data, secret, cache, OS metadata, portfolio methodology, sentiment methodology, Fusion methodology, or analytical CSV value was changed.

## Exact changed-file list

- `.gitignore`
- `ai/AI_NOTES.md`
- `ai/interaction_005_investor_app_and_fact_sheets.md`
- `context/PROJECT_DECISIONS.md`
- `requirements.txt`
- `resources/interaction_004_analytic_hashes.csv`
- `results/data/fund_catalog.csv`
- `results/data/fund_current_holdings.csv`
- `results/figures/fusion_sector_multiplier_activity.png`
- `results/tables/run_manifest.csv`
- `scripts/run_part_b.py`
- `scripts/check_handin.py`
- `src/app_utils.py`
- `src/fusion.py`
- `streamlit_app.py`
- `tests/test_app_utils.py`
- `tests/test_streamlit_app.py`

## Post-review visual correction

Browser review found a real conflict between the App's forced light page background and inherited dark Streamlit widget/text styling. It affected page text, inactive tabs, form labels, captions, expanders, metric cards, alerts, data tables, and Plotly charts, creating unreadable pale-on-white text and mixed light/dark surfaces.

The correction explicitly locks Streamlit to the approved light theme, applies narrowly scoped dark-text CSS outside the dark hero banner, keeps the active tab distinct, and renders every Plotly figure through one light-presentation helper with `theme=None`. Visible OOS and effective dates are formatted as `YYYY-MM-DD`; comparison columns are ordered and formatted for normal laptop width; and the return-versus-volatility scatter uses human-readable fund-group and hover labels. The Fusion underperformance and higher-turnover result remains visible and was not retuned.

No analytical artifact, CSV value, PNG source data, portfolio output, sentiment output, Fusion output, runner, methodology, parameter, or interpretation changed. A final `git diff -- results src scripts context requirements.txt requirements-dev.txt AGENTS.md` was empty.

Validation results:

- focused Streamlit AppTest: `20 passed in 10.62s`, including all 13 fact sheets and no uncaught exception;
- full suite: the sandboxed first run had `76 passed` and one existing online smoke-test DNS failure; the final approved official-source run completed with `77 passed in 13.76s`;
- `python scripts/check_handin.py`: 21 checks passed with the expected cache and unwritten-report reminders;
- `git diff --check`: passed;
- headless health check at `http://127.0.0.1:8766/_stcore/health`: HTTP `200`, body `ok`, followed by a clean stop;
- manual Browser review at `1366 × 900`: all five tabs, the expanded disclosure, controls, tables, charts, labels, captions, and metric cards were readable; computed-style checks found no pale/white heading, paragraph, field label, caption, tab label, or expander text outside the hero banner, and browser logs contained no errors.

Exact changed-file list:

- `.streamlit/config.toml`
- `ai/interaction_005_investor_app_and_fact_sheets.md`
- `streamlit_app.py`
- `tests/test_streamlit_app.py`
