# Interaction 010 — Final live release and Moodle package

## Prompt

```text
Interaction 010B — Final live-release record and Moodle submission package

Work only inside z5711503_projectB.

The analytical project, final report and Streamlit application are frozen.
Do not modify:

- src analytical logic;
- streamlit_app.py;
- portfolio/sentiment/fusion methodology;
- canonical analytical CSV values;
- report/report.docx;
- report/report.pdf;
- approved figures;
- requirements or Streamlit runtime settings unless a genuine blocking error
  is discovered.

There is no blocking error.

============================================================
1. Record the verified live deployment
============================================================

The final verified public URLs are:

Public GitHub repository:
https://github.com/CHUHAOPENG/cross-asset-allocation-lens-fins5545

Live Streamlit application:
https://cross-asset-allocation-lens-fins5545.streamlit.app/

Deployment coordinates:

Repository:
CHUHAOPENG/cross-asset-allocation-lens-fins5545

Branch:
main

Main file:
streamlit_app.py

Streamlit Community Cloud runtime:
Python 3.14

Local analytical/reproduction development environment remains the previously
recorded Python 3.13 environment. Do not rewrite the analytical manifest to
pretend that the analytical pipeline was generated under Python 3.14.

============================================================
2. Record the read-only production audit
============================================================

Interaction 010A was a read-only audit of the actual public Streamlit URL.

Record the production-audit result accurately:

Overall:
PASS WITH MINOR ISSUES

Public access:
PASS

The app loaded without authentication and showed no login requirement,
deployment error, traceback, persistent spinner or redirect.

All five tabs passed:

1. Fund Explorer
2. Fund Fact Sheet
3. Allocation Lab
4. Sentiment Lab
5. Fusion Evidence

Verified behaviours included:

- all 13 funds available;
- Net/Gross switching worked;
- Crypto Risk Parity displayed five recorded fallbacks;
- Allocation Lab rejected invalid totals and both Buy & Hold and Monthly Reset
  worked;
- missing sentiment remained missing rather than being replaced with 50;
- Fusion Evidence retained the augmented fund's underperformance, lower Sharpe,
  higher turnover and no-retuning disclosure;
- refresh worked;
- browser console contained no error/warn logs;
- no uncaught Streamlit exception or failed visual asset was observed.

Value spot checks included approximately:

- Equity Risk Parity net cumulative return: 32.97%
- Equity Risk Parity + Sentiment net cumulative return: 31.78%
- net Sharpe: 0.713 versus 0.694
- Crypto Minimum Variance Sharpe: 0.934
- Equity Minimum Variance volatility: 12.70%
- Combined Risk Parity Sharpe: 0.774
- Fusion annualised tracking error: 0.29%
- Crypto Risk Parity fallback count: 5

The only cosmetic findings were:

- some Fusion comparison-table values are displayed as raw decimals rather
  than percentages;
- the widest comparison tables require modest internal horizontal scrolling.

These were judged non-blocking and no code or analytical change was
recommended before final release.

Do not invent a complete network waterfall. Record that browser developer
diagnostics were available and console checks passed, but request-level network
response codes were not individually enumerated.

============================================================
3. Update final project status
============================================================

Update README.md.

The Links / Live project section must now contain:

Public GitHub repository:
https://github.com/CHUHAOPENG/cross-asset-allocation-lens-fins5545

Live Streamlit application:
https://cross-asset-allocation-lens-fins5545.streamlit.app/

Remove any wording that says Streamlit deployment is pending.

Do not change the analytical description.

Update ai/AI_NOTES.md accurately:

- CHUHAO PENG personally reviewed and approved the final report;
- the public GitHub repository is live;
- the Streamlit Community Cloud application is live;
- the production app passed the read-only Interaction 010A audit with only
  non-blocking cosmetic findings;
- no further analytical or app change was recommended;
- Moodle upload is the only remaining release action after final package
  verification.

Update context/PROJECT_DECISIONS.md only for release-status wording:

- portfolio, sentiment, fusion, app and report are frozen;
- GitHub publication is complete;
- Streamlit deployment and public production audit are complete;
- Moodle submission remains pending.

If docs/STUDENT_DEPLOY.md contains placeholders or "pending" deployment wording,
update only the release-status section with the two verified URLs and Python
3.14 Cloud runtime. Do not rewrite the instructional content unnecessarily.

============================================================
4. Create the final Interaction 010 record
============================================================

Create:

ai/interaction_010_final_live_release_and_moodle_package.md

Preserve this full Interaction 010B prompt verbatim.

Also record that Interaction 010A was read-only and therefore created no project
file or commit.

Include:

- verified GitHub URL;
- verified Streamlit URL;
- Streamlit runtime Python 3.14;
- distinction from the Python 3.13 analytical environment;
- production audit verdict;
- five-tab results;
- value spot checks;
- cosmetic findings;
- explicit decision not to change code because no blocking or important issue
  was found;
- final validation commands;
- final ZIP details;
- exact changed-file list;
- remaining manual Moodle action.

============================================================
5. Confirm all required hand-in artifacts
============================================================

Verify that the repository contains at minimum:

PROJECT_BRIEF.md
README.md
AGENTS.md
CLAUDE.md
SUBMISSION_CHECKLIST.md

streamlit_app.py
requirements.txt
requirements-dev.txt
.streamlit/config.toml

report/report.pdf
report/report.docx
report/FINAL_REPORT.md

results/data/fund_returns.csv
results/data/fund_weights.csv
results/data/sector_sentiment_index.csv
results/tables/performance_metrics.csv
results/tables/run_manifest.csv

ai/AI_NOTES.md
all substantive Interaction 001-010 records

Confirm that the final PDF still contains:

Submission date: 8 August 2026

and does not contain:

Pending confirmation

Do not regenerate the PDF.

============================================================
6. Final integrity verification
============================================================

Verify again:

- 20/20 Interaction 004 frozen analytical hashes match;
- report/report.pdf SHA-256 is still:
  ad3ff7c4f9f978b1b3615a69a89509dd503355cae562bd8bcd8cdde20370d9b6
- report/report.docx SHA-256 is still:
  c01a3a839d0963d1ebf90c706a9bfbfaaee803c33de37d1d8a2d81604a6fa824
- no analytical output changed in this interaction;
- streamlit_app.py is unchanged;
- no secrets or authentication tokens are present;
- no localhost URL remains in final public-facing documentation;
- no "Streamlit application: Pending" wording remains.

Run:

pytest -q
python scripts/check_handin.py
git diff --check

Expected:
- existing full test suite passes;
- hand-in checker passes with no real failure.

============================================================
7. Commit the final release documentation
============================================================

Commit only the final documentation/status changes:

docs: record live deployment and final release

Do NOT push from Codex.

After the commit:

git status --short

must be clean.

Record the new local commit SHA.

============================================================
8. Generate the FINAL Moodle ZIP
============================================================

After the final commit, create a fresh archive from the final repository state.

Use the existing clean packaging script.

Final filename:

z5711503_projectB_FINAL_20260808.zip

The ZIP must be created outside the repository.

Verify:

unzip -t passes

and that the archive contains none of:

.git
.DS_Store
._*
__MACOSX
__pycache__
*.pyc
.pytest_cache
nested ZIP files
secrets/tokens

Confirm that it DOES contain:

report/report.pdf
report/report.docx
README.md
streamlit_app.py
requirements.txt
results/
ai/

Run scripts/check_handin.py against the clean extracted package if practical.

Calculate and record the final ZIP SHA-256 and file size.

============================================================
9. Final response
============================================================

Report:

- local final-release commit SHA;
- exact changed-file list;
- pytest result;
- hand-in checker result;
- 20/20 frozen hash result;
- report PDF/DOCX hash confirmation;
- verified public GitHub URL;
- verified public Streamlit URL;
- final ZIP absolute path;
- final ZIP filename;
- final ZIP SHA-256;
- final ZIP size;
- archive integrity/hygiene result;
- final git status;
- remaining user action.

The only remaining action should be:

Upload the verified final ZIP to Moodle and submit the required GitHub and
Streamlit URLs in the course submission interface.

Do not push, deploy, modify analytics or claim Moodle submission has occurred.
```

## Interaction 010A read-only production audit

Interaction 010A opened the actual public Streamlit application without authentication and made no project-file change or commit. The overall verdict was **PASS WITH MINOR ISSUES**. Public access and all five tabs passed: Fund Explorer, Fund Fact Sheet, Allocation Lab, Sentiment Lab, and Fusion Evidence.

Verified behaviours included all 13 funds, working Net/Gross switching, five Crypto Risk Parity fallbacks, allocation-total rejection plus working Buy & Hold and Monthly Reset modes, preserved missing sentiment, and the visible negative Fusion result with lower Sharpe, higher turnover, and no retuning. Refresh worked. Browser developer diagnostics were available; console checks contained no error or warning, and no uncaught Streamlit exception or failed visual asset was observed. Request-level network response codes were not individually enumerated.

Value spot checks were approximately 32.97% versus 31.78% net cumulative return for base versus sentiment-augmented Equity Risk Parity; 0.713 versus 0.694 net Sharpe; 0.934 Crypto Minimum Variance Sharpe; 12.70% Equity Minimum Variance volatility; 0.774 Combined Risk Parity Sharpe; 0.29% Fusion annualised tracking error; and five Crypto Risk Parity fallbacks.

The only findings were cosmetic: several Fusion comparison-table values use raw decimals rather than percentage formatting, and the widest tables require modest internal horizontal scrolling. No blocking or important issue was found, so no code or analytical change was recommended.

## Verified live release

- Public GitHub repository: https://github.com/CHUHAOPENG/cross-asset-allocation-lens-fins5545
- Live Streamlit application: https://cross-asset-allocation-lens-fins5545.streamlit.app/
- Deployment coordinates: `CHUHAOPENG/cross-asset-allocation-lens-fins5545`, branch `main`, main file `streamlit_app.py`.
- Streamlit Community Cloud runtime: Python 3.14.
- Local analytical and reproduction environment: Python 3.13. The analytical manifest was not rewritten for the Cloud runtime.

## Final validation and package record

Validation was run from the project root with the existing Python 3.13 environment. The first sandboxed `pytest -q` attempt reached `81 passed, 1 failed` because the official-data smoke test could not resolve either authorised data host. The same suite was rerun with approved network access and passed `82 passed`. No source, result, or official data was changed or fabricated. Test-created `tests/__pycache__`, `scripts/__pycache__`, `src/__pycache__`, and 20 `.pyc` files were removed before the hand-in check.

Final validation commands and results:

- `PYTHONPATH="$PWD" MPLCONFIGDIR=/private/tmp/projectb_interaction010b_mpl /Users/chris/Desktop/fins\ 5545/fins-agent/.venv/bin/pytest -q`: `82 passed in 14.74s` on the authorised network rerun.
- `/Users/chris/Desktop/fins\ 5545/fins-agent/.venv/bin/python scripts/check_handin.py`: `23 checks passed`; no warning or failure.
- `git diff --check`: passed.
- Interaction 004 frozen analytical hashes: `20/20` matched.
- `report/report.pdf` SHA-256: `ad3ff7c4f9f978b1b3615a69a89509dd503355cae562bd8bcd8cdde20370d9b6`.
- `report/report.docx` SHA-256: `c01a3a839d0963d1ebf90c706a9bfbfaaee803c33de37d1d8a2d81604a6fa824`.
- `streamlit_app.py` SHA-256 remained `96d2b4afa8c01f459679ba849ab1857e95013093e9d7d0898db34c80fafa6f78` and had no diff.
- No `src/`, app, requirements, Streamlit configuration, report, results, or analytical file had a diff.
- The PDF remained 20 pages. Its cover visibly showed `Submission date: 8 August 2026`; full-document extraction found no `Pending confirmation`.
- All required hand-in artifacts and ten substantive Interaction 001-010 records were present.
- Public-facing README, deployment guide, and report source contained no pending Streamlit wording, `localhost`, or `127.0.0.1` URL.
- Targeted secret-pattern and authentication-token scan returned no file match.

The final archive is created after the documentation commit at `/Users/chris/Desktop/fins 5545/fins-agent/fins2026/z5711503_projectB_FINAL_20260808.zip` using `scripts/make_submission_zip.sh`. Its post-commit SHA-256, size, archive hygiene, extracted-package checker result, and the local commit SHA are external release metadata reported in the final response. An archive cannot truthfully embed its own final digest, and a commit cannot embed its own commit SHA.

## Changed files

- `README.md`
- `ai/AI_NOTES.md`
- `ai/interaction_010_final_live_release_and_moodle_package.md`
- `context/PROJECT_DECISIONS.md`
- `docs/STUDENT_DEPLOY.md`

## Remaining user-controlled action

Upload the verified final ZIP to Moodle and submit the required GitHub and Streamlit URLs in the course submission interface. Moodle submission has not occurred in this interaction.
