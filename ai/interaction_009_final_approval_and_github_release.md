# Interaction 009 — Final student approval and public GitHub release

## Prompt

```text
Interaction 009 — Final student approval and public GitHub release

Work only inside z5711503_projectB.

CHUHAO PENG has reviewed the final report and has now approved the current
student-reviewed report version to proceed to final deployment.

Submission date remains:

8 August 2026

All analytical logic, canonical CSV values, portfolio/sentiment/fusion
parameters, approved figures, report economic conclusions and Streamlit
behaviour are frozen.

Do not alter analytical results or retune anything.

============================================================
1. Record final student approval
============================================================

Update ai/AI_NOTES.md accurately:

- CHUHAO PENG has personally reviewed the economic interpretations and the
  regenerated final Word/PDF report;
- the current report version is approved to proceed to final deployment;
- portfolio, sentiment, fusion, app and report analytics are frozen;
- GitHub publication and Streamlit deployment are now the remaining release
  steps;
- Moodle submission remains pending.

Update context/PROJECT_DECISIONS.md only for final status wording.

Create:

ai/interaction_009_final_approval_and_github_release.md

Preserve this full prompt verbatim and record all commands, checks, URLs and
changed files.

============================================================
2. Pre-push safety audit
============================================================

Before creating any remote, verify:

- git status --short is clean;
- current branch is main;
- report/report.pdf exists;
- report cover says 8 August 2026;
- no "Pending confirmation" exists;
- no raw project data ZIP is tracked;
- no .DS_Store, __MACOSX, __pycache__, *.pyc or secrets are tracked;
- no localhost URL appears in README or report;
- no private /Users/chris path appears in files intended for the public repo;
- CLAUDE.md truthfully states Claude Code was not used;
- all required results and AI logs are committed;
- 20/20 frozen Interaction 004 analytical hashes still match.

Run:

pytest -q
python scripts/check_handin.py
git diff --check

Do not continue if any real FAIL occurs.

============================================================
3. GitHub authentication check
============================================================

Run:

gh auth status

If GitHub CLI is not installed or not authenticated:

STOP.

Report the exact issue and give the minimum command the user must run.
Do not fabricate a repository or URL.

If authenticated, record the authenticated GitHub account.

============================================================
4. Create the public repository and push
============================================================

First confirm that no origin remote already exists.

Preferred public repository name:

cross-asset-allocation-lens-fins5545

Check whether that repository name already exists under the authenticated
account.

If it does not exist, create it from the current local repository using GitHub
CLI as a PUBLIC repository, add it as origin and push main.

Use the equivalent of:

gh repo create cross-asset-allocation-lens-fins5545 \
  --public \
  --source=. \
  --remote=origin \
  --push

Do not initialise a new README, .gitignore or licence remotely because the
local repository already contains them.

If the repository name already exists:
- do not overwrite or delete anything;
- stop and report the existing repository URL/status so CHUHAO PENG can decide.

============================================================
5. Verify the public GitHub repository
============================================================

After push, verify with GitHub CLI that:

- repository visibility is PUBLIC;
- default branch is main;
- local HEAD equals remote main HEAD;
- origin points to the created repository;
- report/report.pdf exists remotely;
- streamlit_app.py exists remotely;
- requirements.txt exists remotely;
- results/ committed app artifacts exist remotely.

Record the exact verified GitHub repository URL.

Do not claim public status unless verified.

============================================================
6. Update README with the verified repository URL
============================================================

Only after the public repository URL has been verified:

Update README.md with a small "Live project" or "Links" section containing:

- Public GitHub repository: the actual verified URL
- Streamlit application: Pending final Community Cloud deployment

Do not invent the Streamlit URL.

Commit:

docs: record public repository link

Push this commit to origin/main.

Verify local HEAD == origin/main again.

============================================================
7. Prepare Streamlit deployment coordinates
============================================================

Report the exact values CHUHAO PENG must use in Streamlit Community Cloud:

Repository:
<actual owner>/<actual repo>

Branch:
main

Main file path:
streamlit_app.py

Python:
3.13

Confirm:
- requirements.txt is at repository root;
- .streamlit/config.toml is committed;
- the app requires no secrets;
- the app performs no runtime network calls;
- the app reads committed results only.

Do NOT fabricate or guess the final streamlit.app URL.

============================================================
8. Create a pre-deployment clean ZIP
============================================================

Run scripts/make_submission_zip.sh.

Create a clean archive named:

z5711503_projectB_predeployment_20260808.zip

Verify:

unzip -t
no .git
no .DS_Store
no __MACOSX
no __pycache__
no *.pyc
report/report.pdf exists

Record its SHA-256.

This is NOT yet the final Moodle ZIP because the verified Streamlit URL is
still pending.

============================================================
9. Final report
============================================================

Run:

git status --short
git log -3 --oneline
git remote -v

Report:

- GitHub account;
- verified public repo URL;
- final local commit hash;
- remote main hash;
- whether they match;
- exact README change;
- pytest result;
- check_handin result;
- clean ZIP path and SHA-256;
- exact Streamlit deployment coordinates;
- remaining manual user action.

Do not deploy Streamlit yourself unless a supported authenticated deployment
mechanism is actually available. Do not fake success.

Commit any required AI/status documentation before the final push.

Final git status must be clean.
```


## Final student approval

CHUHAO PENG personally reviewed the economic interpretations and the regenerated final Word/PDF report. The current report version is approved to proceed to final deployment. Portfolio, sentiment, fusion, app, report analytics, approved figures, and economic conclusions remain frozen.

## Authorised release scope

Interaction 009 authorises creation and verification of the named public GitHub repository, publication of branch `main`, recording the verified repository URL, preparation of the pre-deployment ZIP, and release-coordinate documentation. Streamlit Community Cloud deployment itself is not authorised unless a supported authenticated deployment mechanism is directly available, and no Streamlit URL may be invented. Moodle submission remains pending.

## Release state before publication

At the start of this interaction, the local repository was on `main` at `e2d571ce8efbb8e6b1d55dfb34ceaef2360d80e0` with a clean working tree. GitHub authentication, repository-name availability, remote creation, publication, and ZIP preparation had not yet been performed or claimed.
