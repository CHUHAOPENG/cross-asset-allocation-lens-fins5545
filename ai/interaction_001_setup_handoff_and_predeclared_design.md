# Interaction 001 — setup, Part A handoff, and predeclared design

Date: 2026-08-05
Project: `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectB`

## Prompt

The complete original prompt is preserved verbatim from `/Users/chris/.codex/attachments/41a92a4a-2dcf-4504-9022-b013e3527f52/pasted-text.txt`:

```text
Interaction 001 — Project setup, Part A handoff and predeclared design

Project root:
 /Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectB

Read-only Part A:
 /Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectA

Use this interpreter if present:
 /Users/chris/Desktop/fins 5545/fins-agent/.venv/bin/python

Do not install packages, download data, build models, generate analytical
results, push to GitHub, or modify files outside Project B.

1. Read completely:
- PROJECT_BRIEF.md
- README.md
- SUBMISSION_CHECKLIST.md
- AGENTS.md and CLAUDE.md
- context/*
- scripts/*
- src/*
- tests/*
- streamlit_app.py
- report/OUTLINE.md
- requirements files

Read from Part A only what is needed for the handoff:
- context/student_decisions.md
- src/etl.py
- src/features.py
- scripts/run_part_a.py
- tests/test_station1_etl.py
- tests/test_station2_features.py
- tests/test_station2_timestamp_diagnostic.py
- results/tables/feature_dictionary.csv
- results/tables/calendar_alignment_summary.csv

Locate and inspect the relevant Week 5, Week 8 and Week 9 code under
/Users/chris/Desktop/fins 5545/. Record exact paths used. If a required path
cannot be found, report it; do not invent a substitute.

2. Replace AGENTS.md with concise permanent project instructions covering:
- Project B scope and folder boundaries
- approved Part A calendar and news-mapping inheritance
- no price forward filling
- no look-ahead
- native-calendar crypto returns before equity-date selection
- 252/365 annualisation rules
- causal sentiment lag and standardisation
- no-headline observations are missing, not automatically neutral
- exact mandatory output filenames
- precomputed Streamlit artifacts only
- testing, provenance, AI logging and reproducibility
- no silent parameter or methodology changes

Do not modify the supplied files under context/.

3. Create context/PART_A_HANDOFF.md documenting:
- reusable Part A decisions and functions
- exact source paths
- what will be reused, adapted or excluded
- the Rule A news mapping
- crypto calendar treatment
- Part A limitations that must remain disclosed

Do not copy the entire Part A folder and do not copy raw data.

4. Create context/PROJECT_DECISIONS.md and predeclare:

Product:
- Cross-Asset Allocation Lens
- target user: a self-directed investor or junior portfolio analyst comparing
  systematic multi-asset funds

Fund universes:
- Equity
- Crypto
- Combined

Methods:
- Equal Weight
- Minimum Variance
- Risk Parity
- Maximum Sharpe

Backtest:
- expanding walk-forward OOS
- initial window 252 observations for Equity and Combined
- initial window 365 observations for Crypto
- monthly rebalancing
- weights use information available strictly before the holding period
- long-only
- maximum asset weight = min(35%, 5 / number_of_assets)
- risk-free rate = 0
- Combined uses crypto returns calculated on the native seven-day calendar,
  then selected onto equity trading dates
- report gross results, turnover and net results using a predeclared 10 bps
  one-way trading-cost assumption
- solver failures must be recorded and use an explicit deterministic fallback

Sentiment:
- Plain VADER baseline
- finance-extended VADER as the main model
- preserve raw casing, punctuation, boosters and negation
- aggregate headline -> ticker-day -> equal-weight sector
- ticker-days with no supplied headline remain missing
- lag signals by at least one equity trading day
- trading standardisation must be causal
- full-sample standardisation may be used only for descriptive figures
- an entirely missing sector signal may be carried forward for at most five
  equity trading days, after which no sentiment tilt is applied

Fusion:
- apply a bounded, coverage-aware sector sentiment tilt to the Equity Risk
  Parity fund
- use a fixed predeclared tilt strength rather than selecting the best value
  using the full test sample
- compare base versus augmented performance, drawdown, turnover and net return

Innovation:
- coverage-aware finance-sentiment overlay
- transaction-cost and turnover analysis
- investor allocation simulator in the app using the common OOS period

Record unresolved implementation details explicitly. Do not claim empirical
results.

5. Create:
 ai/interaction_001_setup_handoff_and_predeclared_design.md

It must contain the prompt, files read, decisions recorded, commands run,
validation results and exact changed-file list. Keep it factual and concise.

6. Initialise Project B as a standalone Git repository on branch main if it is
not already one. Do not push. Make one baseline commit only after validation:
 chore: initialise Project B design baseline

7. Validate:
- folder name is z5711503_projectB
- official starter files are present
- no raw CSV/parquet outside results/
- no .DS_Store, AppleDouble, secrets or cache files
- Part A and course-week files were not modified
- run pytest -q
- run python scripts/check_handin.py
- show git status --short
- show the commit hash if the commit succeeded

Stop after setup and design. Do not implement portfolios, sentiment, fusion,
figures, report or Streamlit features in this interaction.
```

The detailed method choices in the supplied prompt were transcribed into `context/PROJECT_DECISIONS.md`, including all fund universes/methods, expanding OOS windows, constraints, 252/365 rules, 10 bps cost, VADER designs, causal lag/standardisation, missing-news treatment, fusion, and innovations.

## Files read

Project B files were read completely:

- `PROJECT_BRIEF.md`, `README.md`, `SUBMISSION_CHECKLIST.md`, `AGENTS.md`, `CLAUDE.md`
- all existing files under `context/`, `scripts/`, `src/`, and `tests/`
- `streamlit_app.py`, `report/OUTLINE.md`, `requirements.txt`, and `requirements-dev.txt`

Part A reads were limited to the nine exact paths listed in `context/PART_A_HANDOFF.md`. The relevant Week 5/8/9 paths inspected are also listed there. The attached prompt was read from `/Users/chris/.codex/attachments/41a92a4a-2dcf-4504-9022-b013e3527f52/pasted-text.txt`.

## Decisions recorded

- Project/folder boundaries and supplied-context immutability.
- Approved Part A ETL, Rule A, native-calendar returns, crypto selection, no-fill logic, reusable functions/tests, exclusions, provenance, and continuing limitations.
- Cross-Asset Allocation Lens product, user, three universes, four methods, expanding walk-forward design, windows, constraints, annualisation, trading costs, and deterministic fallback.
- Plain VADER baseline; finance-extended VADER main model; unchanged headline text; headline-to-ticker-day-to-sector aggregation; missing-news semantics; one-day lag; causal standardisation; five-day decaying carry.
- Fixed bounded coverage-aware overlay on Equity Risk Parity with `lambda = 0.10` and no full-sample tuning.
- Innovation areas and seven explicitly unresolved implementation decisions.

No empirical Project B result is claimed.

## What was wrong or risky

- The original Interaction 001 log initially summarised the request instead of preserving the complete substantive prompt verbatim. That created a completeness gap in the graded AI workflow record.
- Without a first-person living summary, later readers could confuse Codex's documentation with the student's final authorship, review, or approval.
- The data-loading smoke test could have triggered a prohibited download when the official ZIP was unavailable locally; the original run blocked network access and reported the resulting failure instead of fabricating data.

## What was checked or corrected

- The original Codex attachment was confirmed available and was copied into the fenced text block above without reconstruction or paraphrase. This post-review correction fixed the prompt-completeness gap.
- `ai/AI_NOTES.md` was added as a living first-person draft using only the review and approval facts explicitly provided by CHUHAO PENG.
- `AGENTS.md` now requires verbatim substantive prompts, maintenance of the living AI summary, and no premature authorship or approval claims.
- The original factual summary, decisions, commands, validation results, and changed-file record below were retained.

## Commands run

Read-only inspection used `sed`, `find`, `rg`, `wc -l`, `git rev-parse`, `git status --short`, and `shasum -a 256`. File changes were applied only through a patch. Validation used the course interpreter with `pytest -q`, `pytest --collect-only -q`, and `python -B scripts/check_handin.py`; bytecode and pytest cache creation were disabled. The full pytest run used fail-fast local proxy settings so the prohibited data download could not occur. Repository setup used `git init -b main`, followed at the end by `git add -A` and `git commit -m "chore: initialise Project B design baseline"`. No push command was run.

## Validation results

- Folder name: `z5711503_projectB` — pass.
- Official starter presence: every checked required starter path was present — pass.
- Raw `.csv`/`.parquet` outside `results/`: none.
- `.DS_Store`, AppleDouble, Python/pytest caches, and compiled bytecode: none.
- Secret-file candidates (`.env*`, `secrets.toml`, private-key filename patterns): none.
- Supplied Project B context, all nine inspected Part A files, and all inspected Week 5/8/9 files matched their pre-change SHA-256 hashes after the edits — pass.
- Test collection: two tests collected.
- `pytest -q`: one passed and one failed. `test_imports` passed. `test_data_loads` could not load the online bundle because there is no local `project_data.zip` and this interaction prohibited a download; the run used blocked local proxies and downloaded nothing. This is an environment/data-availability failure, not an assertion failure in changed code. A later authorised run can set `FINS_DATA_ZIP` to a local official ZIP and rerun the unchanged test.
- `python -B scripts/check_handin.py`: 17 checks passed, no failures, and six expected setup-stage reminders (report absent, results empty, and the four mandatory analytical artifacts not yet built). The script ended with `All checks passed - ready to zip and deploy.` That mechanical message does not claim the report, results, deployment, or hand-in exists.
- Standalone repository: initialised at the Project B root on branch `main`; no remote or push was created.

## Exact changed-file list

1. `AGENTS.md` — replaced the supplied placeholder with permanent Project B rules.
2. `context/PART_A_HANDOFF.md` — created.
3. `context/PROJECT_DECISIONS.md` — created.
4. `ai/interaction_001_setup_handoff_and_predeclared_design.md` — created.

No code, supplied `context/` file, Part A file, course-week file, result, report, or Streamlit feature was modified in this interaction.

## Post-review correction changed-file list

1. `AGENTS.md` — added the permanent prompt-preservation, living-summary, and approval-integrity rule.
2. `ai/AI_NOTES.md` — created as a first-person living draft.
3. `ai/interaction_001_setup_handoff_and_predeclared_design.md` — preserved the complete original prompt and documented the completeness risk and correction.

No portfolio, sentiment, fusion, result, report, figure, or Streamlit implementation was created by this correction.

## Post-review correction validation

- `ai/AI_NOTES.md` exists and ends with the required living-draft status.
- The fenced prompt text matches the complete original attachment in content and line order; validation normalised only the attachment's missing terminal newline.
- Git reports exactly the three correction paths listed above; protected project paths have no diff.
- `python scripts/check_handin.py` passed 17 checks with the same six expected setup-stage reminders and no failures.
- `git diff --check` passed.
- A pre-existing untracked `.DS_Store` was moved intact to a temporary quarantine path before validation; it was not committed or counted as a project content change.
- Post-review inspection and validation used `sed`, `rg`, `diff`, `git diff --name-only`, `git diff --check`, `git status --short`, and the course Python interpreter. No analytical command, data download, push, or deployment ran.
