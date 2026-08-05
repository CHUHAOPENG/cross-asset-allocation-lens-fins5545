# Interaction 004 — Coverage-aware sentiment fusion

Date: 2026-08-05
Project: /Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectB

## Prompt

The complete original prompt is preserved verbatim from `/Users/chris/.codex/attachments/abd26ca7-8292-4071-824a-824fc4d24e1e/pasted-text.txt`:

```text
Interaction 004 — Coverage-aware sentiment fusion

Read and follow AGENTS.md, context/PART_A_HANDOFF.md and
context/PROJECT_DECISIONS.md. Work only inside z5711503_projectB.

Interaction 003 has passed technical review. Do not change the existing
portfolio estimators, sentiment scores, Rule A mapping, frozen lexicon,
causal signal construction, or any predeclared parameter.

Do not push, deploy, write the final report, or redesign Streamlit in this
interaction.

============================================================
1. Record the completed reviews and clean dependencies
============================================================

Update ai/AI_NOTES.md accurately:

- Interaction 003 implemented the Rule A and causal sector-sentiment pipeline.
- CHUHAO PENG accepted the sentiment pipeline after independent technical review.
- Fusion, app and report remain pending review or implementation.
- Retain the living-draft status and do not claim a best fund.

Update the status at the top of context/PROJECT_DECISIONS.md:

- portfolio and sentiment methodologies are locked and technically reviewed
  through Interaction 003;
- no economic conclusion or fusion result has yet been approved.

Correct the reproducibility documentation:

- the implementation uses vaderSentiment==3.3.2, not NLTK VADER;
- remove nltk from requirements-dev.txt if no project code imports it;
- correct README.md and requirements comments accordingly;
- remove the unused NLTK package-version row from future manifests if the
  dependency is removed;
- do not modify supplied context/DATA_GUIDE.md.

============================================================
2. Lock the fusion timing and identity
============================================================

Record these decisions before implementation:

Primary augmented fund:
- fund_id: equity_risk_parity_sentiment
- universe: equity
- method: risk_parity_sentiment
- base fund: equity_risk_parity
- sentiment model: finance_vader only

Timing:
- use the finance-vader row from sector_sentiment_signal.csv whose
  effective_date equals the portfolio target effective_date;
- therefore an age-zero signal uses sentiment from the portfolio decision date
  and becomes investable on the following observed equity date;
- carried signals may use only an earlier source_date;
- require source_date <= decision_date;
- no signal dated after the decision date may affect the target;
- do not use plain_vader or descriptive_full_sample_z in the primary overlay.

Fixed rule:
- lambda = 0.10;
- z_bounded = clip(trading_z, -2, 2);
- multiplier =
  clip(1 + lambda * effective_coverage * z_bounded, 0.80, 1.20);
- missing trading_z or effective_coverage gives multiplier 1.0;
- multiply every base Equity Risk Parity stock target by its sector multiplier;
- renormalise and apply the existing deterministic capped-simplex projection;
- apply the same long-only dynamic asset cap as the base fund;
- never tune lambda, clipping, carry length or multiplier bounds after viewing
  results.

============================================================
3. Implement src/fusion.py
============================================================

Replace the starter placeholder with small testable functions for:

- validating the ticker-sector mapping;
- selecting the causal finance signal for each effective date;
- calculating sector multipliers;
- applying sector multipliers to base stock weights;
- capped-simplex projection using the existing portfolio implementation;
- constructing all augmented monthly targets;
- drifted daily holdings and gross returns;
- augmented turnover, cost and net returns;
- augmented performance metrics;
- fusion timing, multiplier and projection audits.

Use the existing equity return panel, existing equity_risk_parity base targets,
official ticker-sector mapping and precomputed causal signal.

At every rebalance:

1. Start from the exact base Equity Risk Parity target weights.
2. Join each stock to its official sector.
3. Use the finance-vader signal available on the target effective date.
4. Calculate the fixed multiplier.
5. Project to the same capped simplex.
6. Apply the augmented target from that effective date until the next rebalance.
7. Drift augmented holdings independently of the base fund.
8. Calculate augmented turnover against its own pre-trade drifted weights.

If no sector has an active signal, the augmented target must equal the base
target within numerical tolerance.

Do not reuse the base fund’s realised daily return as the augmented return.
Recalculate it from augmented drifted holdings and the underlying equity returns.

============================================================
4. Integrate the augmented fund
============================================================

Append the augmented fund to the mandatory files:

results/data/fund_returns.csv
results/data/fund_weights.csv
results/tables/performance_metrics.csv

After integration they must contain exactly 13 fund IDs.

The original 12 fund rows must remain numerically and textually unchanged when
filtered to their original fund IDs.

Use the existing schemas.

For fund_weights.csv:

- solver_success = True because the deterministic projection passed;
- fallback_used = False unless a genuine projection fallback is implemented
  and recorded;
- target and pre-trade weights must represent the augmented fund, not the base.

For performance_metrics.csv:

- use periods_per_year = 252;
- calculate gross and net metrics using exactly the same functions and
  conventions as the base funds;
- fallback_count = 0 unless a genuine recorded fallback occurs.

Do not add the augmented fund to solver_audit.csv as an SLSQP optimisation.
Use a separate fusion audit.

============================================================
5. Additional fusion outputs
============================================================

Create:

results/data/fusion_sector_multipliers.csv

Schema:
decision_date, effective_date, sector, model, source_date, signal_age,
trading_z, effective_coverage, z_bounded, multiplier, has_active_signal

Create:

results/tables/fusion_rebalance_audit.csv

Schema:
decision_date, effective_date, fund_id, eligible_asset_count, asset_cap,
active_signal_sector_count, carried_signal_sector_count,
base_weight_sum, augmented_weight_sum, maximum_base_weight,
maximum_augmented_weight, l1_target_change, projection_distance,
turnover, trading_cost, timing_valid, constraints_valid

Create:

results/tables/fusion_comparison.csv

One row for the base and one row for the augmented fund, plus explicit delta
rows or columns covering:

- common first and last date;
- observations;
- cumulative return gross and net;
- annualised return gross and net;
- annualised volatility gross and net;
- Sharpe gross and net;
- maximum drawdown gross and net;
- total turnover;
- average rebalance turnover;
- total trading cost;
- rebalance count;
- tracking error versus base;
- correlation with base.

Create:

results/tables/fusion_yearly_comparison.csv

Schema:
year, fund_id, observations, cumulative_return_gross, cumulative_return_net,
annualised_volatility_gross, annualised_volatility_net, total_turnover,
total_trading_cost

Create:

results/tables/fusion_current_holdings.csv

Schema:
as_of_date, ticker, sector, base_weight, augmented_weight,
weight_change, latest_signal_source_date, latest_signal_age,
latest_trading_z, latest_effective_coverage, latest_multiplier

Do not label a positive or negative result as proof that sentiment predicts
returns.

============================================================
6. Focused analytical figures
============================================================

Generate reproducibly with matplotlib:

results/figures/fusion_growth_of_one.png
- base versus augmented gross and net growth;
- clearly label the OOS period.

results/figures/fusion_drawdown.png
- base versus augmented net drawdown.

results/figures/fusion_sector_multiplier_activity.png
- show the sector multipliers through time or at rebalance dates;
- make missing/no-tilt periods distinguishable from active tilts.

Use readable titles, axes, legends and source notes. Do not manually edit PNGs.

============================================================
7. Tests
============================================================

Add synthetic tests covering:

- multiplier formula and clipping;
- missing signal gives exactly 1.0;
- age-zero source date is the decision date when effective date is next day;
- carried source date is strictly earlier;
- source_date can never exceed decision_date;
- plain_vader and descriptive full-sample values cannot enter fusion;
- stock-to-sector mapping;
- no-signal target equals base target;
- projected weights sum to one and obey the cap;
- identical inputs give deterministic targets;
- future sentiment perturbation cannot change earlier augmented targets;
- augmented daily return is calculated from augmented holdings;
- augmented holdings drift independently;
- initial and later turnover;
- trading-cost reconciliation;
- base 12 rows are unchanged;
- mandatory schemas and exactly 13 fund IDs;
- comparison tables use identical dates.

Most tests must use synthetic data and require no network.

============================================================
8. Runner, manifest and independent validation
============================================================

Update scripts/run_part_b.py to run:

1. the existing portfolio engine;
2. the existing sentiment pipeline;
3. the fixed fusion overlay;
4. all 13 funds and fusion outputs;
5. the three fusion figures;
6. the updated run manifest.

Replace the Interaction 002 whole-file hash guard with a stronger preservation
check:

- preserve and verify hashes or exact frame equality for the original 12 fund
  subsets;
- allow only the intentional appended augmented rows.

Update run_manifest.csv with:

- all locked fusion parameters;
- 13-fund output counts and hashes;
- every new fusion table and figure hash;
- the actual git HEAD before the run;
- the corrected dependency list.

Run:

python scripts/run_part_b.py
pytest -q
python scripts/check_handin.py
git diff --check
git status --short

Independently verify:

- exactly 13 fund IDs;
- original 12 funds are unchanged;
- augmented dates equal the base Equity Risk Parity dates;
- no signal uses source_date after decision_date;
- age-zero uses the decision date;
- every multiplier lies in [0.80, 1.20];
- every target sums to one and respects the recorded cap;
- augmented returns reconcile to augmented holdings;
- gross/net/cost accounting is exact;
- base and augmented comparison periods are identical;
- no parameter was selected from realised fusion performance;
- manifest hashes match;
- no raw data, cache, secret or OS metadata is tracked.

Create:

ai/interaction_004_coverage_aware_sentiment_fusion.md

Preserve this complete prompt verbatim and record:

- files read and changed;
- review corrections;
- final fusion decisions;
- timing convention;
- commands and tests;
- output counts;
- multiplier and active-signal summaries;
- base-versus-augmented metrics without promotional language;
- anything wrong or risky;
- what was checked or corrected;
- exact changed-file list.

Commit:

docs: record reviewed sentiment baseline
feat: add coverage-aware sentiment fund

Report both commit hashes, exact changed-file list and final git status.
```

## Files read

- `AGENTS.md`
- `context/PART_A_HANDOFF.md`
- `context/PROJECT_DECISIONS.md`
- `ai/README.md`
- `ai/prompt_log_template.md`
- `ai/AI_NOTES.md`
- `README.md`
- `requirements.txt`
- `requirements-dev.txt`
- `src/portfolios.py`
- `src/sentiment.py`
- `src/fusion.py`
- `scripts/run_part_b.py`
- existing tests and generated portfolio/sentiment CSV artifacts
- the original Interaction 004 attachment named above

The supplied `context/DATA_GUIDE.md`, Part A tree, course materials, report, and Streamlit application were not modified.

## Review corrections

- Recorded that Interaction 003 implemented Rule A and the causal sector-sentiment pipeline and that CHUHAO PENG accepted that pipeline after independent technical review.
- Kept economic interpretation, fusion approval, app work, and report work explicitly unapproved or pending as applicable.
- Confirmed that project code imports `vaderSentiment`, not `nltk`; removed the unused NLTK development dependency and future manifest row and corrected the README and requirements comments.
- Updated the run manifest to record `vaderSentiment` and matplotlib versions without the unused NLTK or `vader` distribution rows.

## Final fusion decisions and timing convention

- The only augmented fund is `equity_risk_parity_sentiment`, with universe `equity`, method `risk_parity_sentiment`, base `equity_risk_parity`, and model `finance_vader`.
- Each target uses the finance signal whose effective date equals the target effective date. An active age-zero source equals the portfolio decision date; an active carried source is strictly earlier; all active source dates are on or before the decision date.
- The fixed rule is `lambda = 0.10`, z-score clipping to `[-2, 2]`, and multiplier clipping to `[0.80, 1.20]`; missing signal inputs give exactly 1.0. These values were predeclared and were not selected from fusion performance.
- The augmented target uses the existing deterministic capped-simplex projection and base dynamic cap, then maintains its own daily drift, pre-trade weights, turnover, costs, gross returns, and net returns.
- `plain_vader` and descriptive full-sample z-scores do not enter the overlay.

## Commands, tests, and independent checks

- `python scripts/run_part_b.py` initially stopped because sandbox DNS could not reach the two official loader URLs. It was rerun without changing the loader in an authorised network context and completed using the official Google Drive source.
- `pytest -q` initially needed the repository on `PYTHONPATH` in this environment; 44 tests passed and the existing online smoke test then hit the same sandbox DNS restriction. The authorised full rerun passed: `45 passed in 3.89s`.
- An independent reconstruction from official underlying equity returns reconciled augmented gross returns, augmented pre-trade weights, and turnover with maximum absolute errors of approximately `1.05e-16`, `1.11e-16`, and `2.91e-16`, respectively.
- The independent check also verified identical base/augmented dates, causal source timing, all 20 output SHA-256 manifest entries, the recorded pre-run Git HEAD, and the explicit no-tuning manifest statement.
- The three generated PNGs were visually inspected for readable titles, axes, legends, OOS dates, missing-signal distinction, and source notes.
- Final validation commands also included `python scripts/check_handin.py`, `git diff --check`, and `git status --short`.

## Output counts and signal summary

- Mandatory outputs contain exactly 13 fund IDs: 11,157 daily fund-return rows, 19,080 target-weight rows, and 13 performance rows.
- The augmented fund has 753 daily observations and 36 rebalances from 2021-01-04 through 2023-12-29.
- The multiplier table has 360 sector-rebalance rows: 354 active-signal rows, including 351 age-zero rows and 3 carried rows. The observed multiplier range is exactly 0.80 to 1.20.
- The fusion rebalance audit has 36 rows; yearly comparison has 6 rows; current holdings has 50 rows; the manifest has 92 rows.
- The original 12 fund subsets remain byte-for-byte identical under the preserved CSV-text hashes, and exact in-memory frame equality was also checked before appending the augmented rows. `solver_audit.csv` was not extended with the projection-based fund.

## Base-versus-augmented metrics

Both funds use the same 753 OOS dates from 2021-01-04 through 2023-12-29. The base gross/net cumulative returns are 0.332254/0.329722 and the augmented values are 0.321014/0.317816. Base gross/net Sharpe values are 0.717739/0.713393 and augmented values are 0.699420/0.693909. Base/augmented total turnover is 1.901901/2.423553, total trading cost is 0.001902/0.002424, net maximum drawdown is -0.194018/-0.196272, net tracking error versus base is 0.002884, and net-return correlation is 0.999814. These sample results are descriptive and are not proof that sentiment predicts returns or that either fund is best.

## What was wrong or risky

- The reproducibility documentation and manifest still referred to NLTK even though the implementation used the separate `vaderSentiment==3.3.2` package.
- A whole-file hash guard for the three mandatory fund artifacts would necessarily reject the intentional thirteenth-fund append and was not sufficient to express the real preservation requirement.
- The first runner and smoke-test attempts were blocked by sandbox DNS, not by an analytical or data-integrity failure. Treating that environmental failure as permission to substitute data would have been wrong.
- A fused return copied from the base fund, a signal after the decision date, shared drifted holdings, or silent retuning would each create a material methodological error. Focused tests and independent reconstruction cover these risks.
- The augmented and base paths are highly correlated in this sample. Small differences and a bounded historical comparison do not support a prediction claim.

## What was checked or corrected

- Corrected dependency documentation and removed the unused NLTK dependency and manifest entry.
- Replaced the whole-file guard with original-12 exact frame equality plus byte-preserving original-subset CSV hashes while allowing only the augmented rows.
- Verified exact schemas, keys, 13 identifiers, 252-period annualisation, zero fusion fallback count, target sums, cap bounds, successful projection flags, and separate fusion audit treatment.
- Verified no future source date, exact age-zero decision-date identity, earlier carried sources, missing-signal multiplier 1.0, and multiplier bounds.
- Verified independent holdings drift, underlying-return reconstruction, initial/later turnover, trading cost, gross/net accounting, common comparison dates, figure generation, and manifest hashes.
- No portfolio estimator, sentiment score, Rule A mapping, frozen lexicon, causal signal construction, report file, Streamlit file, supplied context file, Part A file, or course material was changed.

## Exact changed-file list

- `README.md`
- `ai/AI_NOTES.md`
- `ai/interaction_004_coverage_aware_sentiment_fusion.md`
- `context/PROJECT_DECISIONS.md`
- `requirements-dev.txt`
- `requirements.txt`
- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/data/fusion_sector_multipliers.csv`
- `results/figures/fusion_drawdown.png`
- `results/figures/fusion_growth_of_one.png`
- `results/figures/fusion_sector_multiplier_activity.png`
- `results/tables/fusion_comparison.csv`
- `results/tables/fusion_current_holdings.csv`
- `results/tables/fusion_rebalance_audit.csv`
- `results/tables/fusion_yearly_comparison.csv`
- `results/tables/performance_metrics.csv`
- `results/tables/run_manifest.csv`
- `scripts/run_part_b.py`
- `src/fusion.py`
- `tests/test_fusion.py`
