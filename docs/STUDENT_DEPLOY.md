# Student Guide: Deploying Your Streamlit App for Hand-in

This project folder is a standalone Git repository, and the Streamlit entrypoint
is `streamlit_app.py` at its root. The app reads committed artifacts under
`results/`; it does not run an analytical engine, load raw data, or make a network
request at runtime.

## Verified release status

- Public GitHub repository: https://github.com/CHUHAOPENG/cross-asset-allocation-lens-fins5545
- Live Streamlit application: https://cross-asset-allocation-lens-fins5545.streamlit.app/
- Deployment coordinates: repository `CHUHAOPENG/cross-asset-allocation-lens-fins5545`, branch `main`, main file `streamlit_app.py`.
- Streamlit Community Cloud runtime: Python 3.14.
- Local analytical and reproduction environment: Python 3.13. The analytical manifest remains unchanged.
- Logged-out production audit: PASS WITH MINOR ISSUES; no code or analytical change was recommended.
- Remaining action: upload the verified final package and submit the two public URLs to Moodle.

## What you submit (Part B, Station 4)
- A **live public Streamlit Community Cloud URL**.
- A **public GitHub repository** (the contents of your `<zID>_projectB` folder).
- The repo runs from a clean checkout using the committed app artifacts under
  `results/`.

## Step-by-step

1. **Run the local gates from the project root.**

   ```bash
   pytest -q
   python scripts/check_handin.py
   git diff --check
   git status --short
   streamlit run streamlit_app.py --server.headless true
   ```

   In another terminal, check `/_stcore/health` on the local address reported by Streamlit.

2. **Create the public GitHub repository and add `origin`.** These commands derive
   the authenticated account name, so no fabricated URL is needed:

   ```bash
   gh auth status
   GH_OWNER="$(gh api user --jq .login)"
   gh repo create "$GH_OWNER/z5711503_projectB" --public --description "FINS5545 Project B - Cross-Asset Allocation Lens"
   git remote add origin "https://github.com/$GH_OWNER/z5711503_projectB.git"
   git remote -v
   ```

3. **Push the existing `main` branch.**

   ```bash
   git branch --show-current
   git push -u origin main
   ```

4. **Confirm the repository is public.**

   ```bash
   GH_OWNER="$(gh api user --jq .login)"
   gh repo view "$GH_OWNER/z5711503_projectB" --json nameWithOwner,url,visibility
   test "$(gh repo view "$GH_OWNER/z5711503_projectB" --json visibility --jq .visibility)" = "PUBLIC"
   ```

5. **Deploy through Streamlit Community Cloud.** The current official Community
   Cloud workflow is browser-based. Sign in at `https://share.streamlit.io`, choose
   **Create app**, select the authenticated `z5711503_projectB` repository, choose branch
   `main`, set the main file path to `streamlit_app.py`, select Python 3.14, and
   deploy. Record the real URL only after Streamlit reports success.

6. **Verify the published result.** Open the GitHub repository and the Streamlit
   URL in a fresh logged-out browser, confirm the repository visibility is public,
   all five app tabs load, and no secrets or private paths are exposed. Then submit
   the real public repository URL, live Streamlit URL, and clean ZIP to Moodle.

## Repository boundary

Run every command from the `z5711503_projectB` root. Confirm that
`git rev-parse --show-toplevel` resolves to that folder before adding the remote;
do not publish the surrounding course repository.

## Common pitfalls
- **Missing app artifact.** The app errors on Cloud because a precomputed file under
  `results/data/` was not committed. The starter `.gitignore` keeps `results/`
  committed while blocking raw data - do not re-ignore it.
- **Missing requirement.** Test in a fresh virtual environment; the app's deps are in
  `requirements.txt` (no `nltk`).
- **Absolute paths or committed raw data.** These break the clean-checkout boundary.
  The app should continue to read only the committed precomputed artifacts.
- **Private at hand-in.** Markers cannot open a private app. Make it public and
  re-test the URL before the deadline.
- **Heavy compute on every click.** Do not add modelling to the app runtime;
  continue to load the committed outputs under `results/`.

## Troubleshooting (failures we actually hit)
- **`gh` lost auth mid-session** (push fails): re-run `gh auth login -h github.com -w`
  and push again.
- **Your private repo is not in Streamlit's picker:** link your GitHub account in
  Streamlit settings, or use "Paste GitHub URL" and paste the URL of the
  `streamlit_app.py` file.
- **`results/data` not committed -> the app errors on Cloud:** the starter
  `.gitignore` keeps `results/` committed; commit your precomputed artifacts and push
  before deploying.
- **Unexpected analytical or network import:** stop and remove it from the app
  runtime; deployment should not need raw-data access or VADER resources.
