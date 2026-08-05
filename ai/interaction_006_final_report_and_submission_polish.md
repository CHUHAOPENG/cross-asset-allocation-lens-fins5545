# Interaction 006 — Final report, submission polish and clean hand-in package

## Prompt

```text
Interaction 006 — Final report, submission polish and clean hand-in package

Read and follow AGENTS.md, context/PROJECT_DECISIONS.md,
context/PART_A_HANDOFF.md and the existing AI logs.
Work only inside z5711503_projectB.

Interaction 005 has passed technical and visual review. All analytical outputs,
portfolio logic, sentiment logic, fusion logic and app behaviour are now frozen.

Do not change:
- any analytical methodology;
- any portfolio, sentiment or fusion parameter;
- any analytical CSV values;
- any already-approved chart data;
- app product scope.

Do not push or deploy in this interaction.

============================================================
1. Update project status documents accurately
============================================================

Update ai/AI_NOTES.md so it truthfully states:

- ChatGPT was used for course review, planning, audit and final review guidance;
- Codex was used for implementation and documentation;
- portfolio, sentiment, fusion and app have now been implemented and reviewed;
- the fusion overlay underperformed the base fund in-sample/OOS and was not
  retuned;
- the final report and submission packaging are being completed now;
- the note remains a living first-person summary.

Update the status text near the top of context/PROJECT_DECISIONS.md:

- portfolio, sentiment, fusion and app are locked and reviewed through
  Interaction 005 plus the post-review visual correction;
- the fixed fusion overlay produced a modest negative OOS result and higher
  turnover;
- this remains descriptive evidence, not proof for or against predictability;
- final reporting and hand-in packaging are now being completed.

============================================================
2. Prepare final report outputs
============================================================

Create all remaining report-ready figures and tables under results/ without
changing existing approved analytics.

Add report figures as needed under:
results/figures/

The report should use already-approved analytical outputs and may generate new
presentation figures derived from committed CSVs, but must not recompute
alternative strategies or change numerical results.

At minimum create clear report-quality figures for:

A. Fund universe overview
- comparative net annualised return vs volatility scatter for the 13 funds;
- legible labels or grouped legend;
- suitable for insertion into the report.

B. Selected growth comparison
- net growth of $1 for representative funds:
  one Equity, one Crypto, one Combined, and the sentiment-augmented fund.

C. Selected drawdown comparison
- net drawdown for the same representative funds.

D. Sentiment evidence
- one sector sentiment index example with preserved gaps;
- one sector causal z-score / tradable signal example;
- one sector coverage example.

E. Fusion evidence
- base vs augmented net growth;
- base vs augmented net drawdown;
- sector multiplier activity;
- latest largest target-weight changes.

F. Allocation lab demonstration
- a simple static illustration or table based on the app-ready outputs, showing
  an example multi-fund allocation and its summary metrics, clearly labelled as
  an illustrative simulation from committed fund net returns.

Also create any concise summary tables needed for the report under:
results/tables/

============================================================
3. Write the final report
============================================================

Replace report/OUTLINE.md with a complete polished final report in Markdown:

report/FINAL_REPORT.md

Target: a strong submission-ready report, concise but substantive.

Suggested structure:

1. Title and project objective
2. Product overview
3. Data and inherited Part A processing
4. Portfolio construction methodology
5. Sentiment methodology
6. Fixed sentiment fusion methodology
7. Results
   - fund comparison
   - sentiment evidence
   - fusion evidence
   - investor app and allocation functionality
8. Limitations
9. Conclusion
10. Appendix / artifact guide

Requirements:

- use a neutral academic/professional tone;
- write clearly and directly;
- distinguish descriptive findings from claims of predictability;
- explicitly mention:
  - Rule A mapping;
  - crypto native-calendar return handling;
  - OOS walk-forward design;
  - 252 vs 365 annualisation;
  - missing-news semantics;
  - one-trading-day lag;
  - five-day sentiment carry with coverage decay;
  - fixed lambda=0.10 overlay;
  - fusion underperformed and had higher turnover;
  - app is educational/analytical only and not personalised advice.
- include references to the exact figure and table filenames where useful;
- do not fabricate citations to outside literature;
- do not claim statistical significance that was not tested.

The report must read as a final student-authored deliverable, not an AI log.

============================================================
4. Rewrite README for final delivery
============================================================

Replace starter-style README.md with a clean final project README containing:

- project title;
- one-paragraph overview;
- repository structure;
- key artifacts produced;
- how to run the analytical pipeline;
- how to launch the Streamlit app;
- dependency notes;
- what is frozen and what is illustrative;
- limitations;
- hand-in notes.

Remove obsolete starter instructions such as renaming the folder.

============================================================
5. Clean dependency separation
============================================================

Make the dependency split cleaner:

requirements.txt:
- only what is needed to run the Streamlit app and load committed artifacts.

requirements-dev.txt:
- everything needed for full reproduction, testing and analytical regeneration.

If streamlit_app.py and src/app_utils.py do not use scipy, matplotlib, requests,
pyarrow, or vaderSentiment directly, move those out of requirements.txt and keep
them only in requirements-dev.txt where appropriate.

Ensure tests and README reflect the split accurately.

============================================================
6. Final hand-in hygiene
============================================================

Add a small helper script if useful, for example:

scripts/make_submission_zip.sh

It should create a clean final submission archive excluding:
- .git
- __pycache__
- *.pyc
- .DS_Store
- ._*
- __MACOSX

Do not create the final zip inside the repo if that complicates exclusions.

Also ensure .gitignore sensibly excludes these transient files.

============================================================
7. Validation
============================================================

Run:

python scripts/run_part_b.py
pytest -q
python scripts/check_handin.py
git diff --check
git status --short

Also verify:

- no frozen analytical artifact changed unexpectedly;
- the approved Interaction 004 analytic hashes still pass;
- the final report references existing files only;
- README instructions match the actual repo;
- requirements.txt supports the app;
- requirements-dev.txt supports full reproduction;
- the app still loads after any dependency cleanup.

Run a final Streamlit health check:
- start on a temporary local port,
- confirm HTTP 200,
- stop cleanly.

============================================================
8. AI record
============================================================

Create:

ai/interaction_006_final_report_and_submission_polish.md

Preserve this complete prompt verbatim and record:

- files read and changed;
- final reporting decisions;
- new report figures/tables added;
- README and dependency cleanup;
- hand-in packaging approach;
- tests and health-check results;
- anything wrong or risky;
- what was checked or corrected;
- exact changed-file list.

============================================================
9. Commits
============================================================

Make two commits after validation:

docs: write final report and project README
chore: polish submission package

Report:
- both commit hashes,
- final git status,
- exact changed-file list,
- the path and name of the clean submission zip if created.
```

## Files read

- `AGENTS.md`
- `context/PROJECT_DECISIONS.md`
- `context/PART_A_HANDOFF.md`
- `PROJECT_BRIEF.md`
- `README.md` and `report/OUTLINE.md` as they existed before this interaction
- `SUBMISSION_CHECKLIST.md`, `CLAUDE.md`, and `docs/STUDENT_DEPLOY.md`
- `ai/README.md`, `ai/prompt_log_template.md`, `ai/AI_NOTES.md`, and Interaction 001–005 logs
- committed analytical files under `results/data/` and `results/tables/`
- existing fusion figures under `results/figures/`
- `streamlit_app.py`, `src/app_utils.py`, the analytical runner, checker, tests, dependency files, and Streamlit configuration
- the original Interaction 006 attachment named above

No protected Project A file, private workspace file, course material, or raw dataset was modified.

## Final reporting decisions

- Report all 13 funds in the summary and return–risk figure.
- Hold the method constant for path comparisons by selecting Equity, Crypto, and Combined Risk Parity, then show the frozen sentiment-augmented Equity Risk Parity fund separately.
- Use Materials as the sentiment example because its genuine gaps make the approved missing-news policy visible, not because of an observed return outcome.
- Use an equal 25% Buy & Hold allocation across those four displayed funds as an illustrative, non-optimised, non-recommended app demonstration over the exact common OOS intersection.
- Reuse the three already-approved fusion figures and create only the missing report presentation views from committed artifacts.

These are presentation choices only. No analytical methodology, parameter, canonical analytical CSV, approved chart data, or app scope changed.

## New report figures and tables

The report builder added nine presentation figures:

- `results/figures/report_fund_return_volatility.png`
- `results/figures/report_selected_growth.png`
- `results/figures/report_selected_drawdown.png`
- `results/figures/report_equity_weights_over_time.png`
- `results/figures/report_materials_sentiment_index.png`
- `results/figures/report_materials_trading_signal.png`
- `results/figures/report_materials_coverage.png`
- `results/figures/report_fusion_latest_weight_changes.png`
- `results/figures/report_allocation_example.png`

It also added four report tables:

- `results/tables/report_fund_summary.csv`
- `results/tables/report_allocation_example_weights.csv`
- `results/tables/report_allocation_example_metrics.csv`
- `results/tables/report_exhibit_catalog.csv`

## README and dependency cleanup

`README.md` now documents the product, analytical boundary, app-only and full-reproduction commands, repository structure, frozen versus illustrative artifacts, limitations, validation, and hand-in boundary. Obsolete folder-renaming instructions were removed.

`requirements.txt` now contains only Streamlit, pandas, NumPy, and Plotly for the app. SciPy, PyArrow, Requests, Matplotlib, the pinned `vaderSentiment==3.3.2`, and pytest are in `requirements-dev.txt`. A regression test verifies this separation and the report artifact references.

## Hand-in packaging approach

`scripts/make_submission_zip.sh` creates the ZIP in the project parent directory by default, refuses to overwrite an existing archive, excludes Git metadata, virtual environments, caches, compiled Python, macOS metadata, secrets, environment files, and ZIP files, then validates the archive with `unzip -t`. `.gitignore` carries matching transient-file exclusions.

## Tests and health-check results

- `MPLCONFIGDIR=/private/tmp/projectb-mpl ../../.venv/bin/python scripts/run_part_b.py`: passed after approved access to the official source; official ZIP SHA-256 `9740a68c63e4edf2fbe03d91a5356728e9355a1070580052b66893d4c7463010`, 12 base funds, 13 total funds, 5 logged fallbacks, 0 constraint violations, and 20 frozen analytics verified.
- `MPLCONFIGDIR=/private/tmp/projectb-report-mpl ../../.venv/bin/python scripts/build_report_artifacts.py`: passed; 9 report figures and 4 report tables validated.
- `MPLCONFIGDIR=/private/tmp/projectb-test-mpl ../../.venv/bin/python -m pytest -q`: `80 passed in 14.26s` with approved official-source access for the smoke test.
- Clean Python 3.13 app-only environment: `pip install -r requirements.txt` passed and direct app execution exited 0.
- Clean Python 3.13 full environment: `pip install -r requirements.txt -r requirements-dev.txt` passed; report builder passed; `pytest -q --ignore=tests/test_smoke.py` reported `78 passed, 2 warnings` in 21.07 seconds. The warnings are existing NumPy generic-timedelta deprecations in `src/features.py`; frozen source code was not changed in this reporting interaction.
- `../../.venv/bin/python scripts/check_handin.py`: 21 checks passed. It retained two non-blocking reminders for generated Python caches and the not-yet-personally-approved/exported PDF; the ZIP helper excludes the caches and this interaction does not claim the course PDF exists.
- `git diff --check`: passed.
- Report-reference validation: 24 local references checked; 0 missing.
- Interaction 006 verbatim-prompt comparison: exact match.
- Streamlit app-only health check: temporary `127.0.0.1:8766/_stcore/health` returned HTTP `200` with body `ok`; the server then stopped cleanly.

## Anything wrong or risky

- The first return–risk figure compressed the Equity and Combined labels because Crypto occupies a much larger risk scale. It was corrected to two explicitly differently scaled panels so all 13 labels remain readable without changing any point value.
- The first latest-fusion-weight figure clipped the largest negative value label into the ticker label. Symmetric horizontal padding corrected the presentation without changing the weights.
- The course hand-in checker expects a PDF or DOCX and will retain a reminder until CHUHAO PENG personally reviews/rewrites the report and exports the course-formatted PDF. This interaction creates the requested Markdown report source and does not claim final student approval.
- Dependency declarations can be checked and exercised locally, but successful installation on another clean machine still depends on compatible package availability.
- The system-default `python3` was Python 3.9, below the documented Python 3.11+ support boundary, and failed on the existing `zip(..., strict=True)` call after installing app dependencies. The supported-runtime validation was repeated in clean Python 3.13 environments and passed; no source compatibility change was made.
- The first sandboxed runner and pytest smoke-test attempts could not resolve the official data hosts. They were repeated with approved official-source network access and passed. No alternate or fabricated data were used.

## What was checked or corrected

- All nine new report figures were visually inspected; the two presentation issues above were corrected and rechecked.
- Report values were reconciled to committed fund, sentiment, fusion, and allocation artifacts.
- The report distinguishes descriptive OOS evidence from predictability and significance claims and keeps the negative fusion result visible.
- The end-to-end runner changed only the expected manifest timestamp and recorded pre-run Git head; all 20 frozen analytical artifacts retained their approved hashes.
- App-only and full dependency files were installed in clean supported Python environments, and the app and report workflow were exercised there.
- Archive contents and commit boundaries are verified after the two required commits.

## Exact changed-file list

- `.gitignore`
- `README.md`
- `ai/AI_NOTES.md`
- `ai/interaction_006_final_report_and_submission_polish.md`
- `context/PROJECT_DECISIONS.md`
- `report/OUTLINE.md` (deleted)
- `report/FINAL_REPORT.md` (added)
- `requirements-dev.txt`
- `requirements.txt`
- `results/figures/report_allocation_example.png`
- `results/figures/report_equity_weights_over_time.png`
- `results/figures/report_fund_return_volatility.png`
- `results/figures/report_fusion_latest_weight_changes.png`
- `results/figures/report_materials_coverage.png`
- `results/figures/report_materials_sentiment_index.png`
- `results/figures/report_materials_trading_signal.png`
- `results/figures/report_selected_drawdown.png`
- `results/figures/report_selected_growth.png`
- `results/tables/report_allocation_example_metrics.csv`
- `results/tables/report_allocation_example_weights.csv`
- `results/tables/report_exhibit_catalog.csv`
- `results/tables/report_fund_summary.csv`
- `results/tables/run_manifest.csv`
- `scripts/build_report_artifacts.py`
- `scripts/make_submission_zip.sh`
- `tests/test_report_artifacts.py`
