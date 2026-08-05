# Interaction 007 — Personally reviewed PDF and deployment preparation

## Prompt

```text
Interaction 007 — Personally reviewed PDF and deployment preparation

Work only inside z5711503_projectB.

All analytical logic, CSV values, portfolio results, sentiment results, fusion
results, app behaviour and approved figures are frozen. Do not change them.

This interaction prepares the final report PDF and deployment files. Do not
claim personal approval unless CHUHAO PENG explicitly confirms the final report
text after reviewing it.

1. Preflight

Read completely:

- report/FINAL_REPORT.md
- report/PDF_LAYOUT_GUIDE.md
- README.md
- SUBMISSION_CHECKLIST.md
- docs/STUDENT_DEPLOY.md
- PROJECT_BRIEF.md
- context/PROJECT_DECISIONS.md
- ai/AI_NOTES.md
- scripts/check_handin.py
- requirements.txt
- streamlit_app.py

Confirm that all report image and table references exist.

2. Create an editable Word report

Generate:

report/report.docx

Use the content of report/FINAL_REPORT.md, but format it as a professional
course report:

- A4;
- readable business-school formatting;
- title page with:
  Cross-Asset Allocation Lens
  FINS5545 Project B — Final Report
  CHUHAO PENG
  z5711503
  submission date placeholder unless confirmed;
- maximum 10 pages for the written narrative;
- clearly separated appendices;
- consistent Heading 1/2/3 styles;
- page numbers;
- readable captions and source notes;
- tables formatted for page width;
- high-resolution committed figures only;
- Appendix Figure A1 on a landscape appendix page if needed;
- no private paths;
- no unverified GitHub or Streamlit URLs;
- no AI-log language in the report.

Preserve the report's neutral findings, especially:
- crypto drawdown risk;
- Maximum Sharpe not dominating OOS;
- fixed sentiment overlay underperformance;
- higher overlay turnover;
- no retuning and no predictability claim.

Do not materially rewrite economic conclusions unless instructed by CHUHAO
PENG. Record any compression needed to meet the page limit.

3. Generate PDF

Export:

report/report.pdf

After export, inspect every PDF page for:

- narrative page count;
- appendix separation;
- clipped text;
- cropped tables;
- stretched or unreadable figures;
- captions separated from figures;
- missing symbols;
- incorrect page breaks;
- private paths or placeholders;
- all 10 sectors visible in Appendix Figure A1.

Report exact:
- total PDF pages;
- narrative pages;
- appendix pages;
- PDF SHA-256;
- file size.

Do not state that the report is personally approved yet.

4. Deployment preparation

Verify that:

- requirements.txt contains only app dependencies;
- streamlit_app.py reads committed results only;
- no analytical runner or network call occurs at app runtime;
- .streamlit/config.toml is present;
- app health check returns HTTP 200;
- README deployment instructions are accurate.

Prepare exact commands for:

- creating the public GitHub repository;
- adding the remote;
- pushing branch main;
- confirming the repository is public;
- deploying streamlit_app.py through Streamlit Community Cloud.

Do not create a fake URL.
Do not claim the repo or app is online unless directly verified.

5. Final status records

Update ai/AI_NOTES.md and context/PROJECT_DECISIONS.md only after the files
actually exist:

- report.docx and report.pdf have been generated and technically checked;
- personal student approval remains pending until CHUHAO PENG confirms it;
- GitHub, deployment and Moodle remain pending unless actually completed.

Append:

## Interaction 007 PDF and deployment preparation

to a new file:

ai/interaction_007_pdf_and_deployment_preparation.md

Preserve this full prompt verbatim and record:
- report formatting decisions;
- page counts;
- PDF inspection;
- hashes;
- tests;
- app health result;
- exact changed-file list;
- unresolved user-controlled actions.

6. Validation

Run:

pytest -q
python scripts/check_handin.py
git diff --check
git status --short

The checker should no longer warn that report/report.pdf is missing.

Commit:

docs: add course-formatted final report

Do not push until CHUHAO PENG has reviewed the Word and PDF files.

Report the commit hash, PDF details, exact changed-file list and final status.
```

## Interaction 007 PDF and deployment preparation

### Preflight and reference check

The required report, project, status, deployment, checker, dependency, and app files were read completely before report generation. The Markdown report contained 25 local image and table references covering 24 unique files; every referenced file existed. No frozen analytical artifact was modified.

### Report formatting decisions

- `report/FINAL_REPORT.md` remains the source narrative. Its economic conclusions and numerical claims were preserved.
- The editable report uses A4 pages, compact business-school styling, consistent heading styles, page numbers after the unnumbered title page, width-controlled tables, committed high-resolution figures, captions, and source notes.
- The title page contains the required project title, course, student name, zID, and the intentional submission-date status `Pending confirmation` because no date was confirmed.
- To keep the written narrative below the 10-page limit, Figures 1, 5, and 8 and Tables 1 and 2 remain in the main body. Supporting portfolio, sentiment, fusion, and allocation exhibits were moved to clearly labelled appendices. This was presentation compression only; no analytical conclusion was rewritten.
- Appendix Figure A1 is placed on a landscape A4 appendix page. All other pages are portrait A4.
- The 13 figures are inline and have descriptive Word alt text. The final Word structural and accessibility audits reported zero findings.

### Page counts and PDF inspection

- Total PDF pages: 19.
- Title pages: 1 unnumbered page.
- Written narrative pages: 7, within the maximum of 10.
- Appendix pages: 11.
- Appendix Figure A1: physical PDF page 9, landscape.

Every PDF page was visually inspected. The final render has clear appendix separation, no clipped text, cropped table, stretched or unreadable figure, separated caption, missing symbol, or incorrect page break. It contains no private path, AI-log language, or unverified GitHub or Streamlit URL. The only placeholder is the explicitly required unconfirmed submission date. Appendix Figure A1 visibly contains Comm, Consumer, Energy, Financials, Healthcare, Industrials, Materials, RealEstate, Tech, and Utilities on the preserved common 0–100 scale. A coordinate-level audit also confirmed that the Appendix D tables remain inside their intended columns.

### PDF identity

- Path: `report/report.pdf`.
- SHA-256: `20a09dfdca10f9d2a2d667133adc3505eb49b2d92c54ccf340d06e675aa34f74`.
- File size: 3,045,236 bytes.

### Deployment audit and preparation

- `requirements.txt` contains only Streamlit, pandas, NumPy, and Plotly.
- `streamlit_app.py` imports the rendering stack and `src.app_utils`; `src.app_utils` loads committed CSV artifacts under `results/`. The app runtime imports no analytical runner and performs no network call.
- `.streamlit/config.toml` is present with headless server settings and the approved explicit light theme.
- `README.md` now points to the Markdown, Word, and PDF report files and accurately keeps personal approval, publishing, deployment, and Moodle submission pending.
- `docs/STUDENT_DEPLOY.md` now removes obsolete hosted-raw-ZIP and cold-start-download claims and records executable GitHub CLI commands for creating the public repository, adding `origin`, pushing `main`, and verifying public visibility. It also records the current official browser workflow for Streamlit Community Cloud.
- No remote was added, repository created, branch pushed, public setting changed, or Streamlit URL claimed.

### Tests and health check

- `PYTHONPATH="$PWD" pytest -q` with approved official-source access: 82 passed, 2 existing NumPy generic-timedelta deprecation warnings.
- The first sandboxed smoke-test attempt could not resolve the two official data hosts. The suite was repeated with approved network access; no data were fabricated and no frozen source was changed.
- `python scripts/check_handin.py`: 22 checks passed. The missing-PDF warning is gone; one non-blocking reminder remains for auto-generated Python caches before ZIP creation.
- Streamlit health endpoint: HTTP 200 with body `ok`.
- Streamlit root page: HTTP 200.
- The local server stopped cleanly after the health check.

### Exact changed-file list

- `README.md`
- `ai/AI_NOTES.md`
- `ai/interaction_007_pdf_and_deployment_preparation.md`
- `context/PROJECT_DECISIONS.md`
- `docs/STUDENT_DEPLOY.md`
- `report/report.docx`
- `report/report.pdf`

### Unresolved user-controlled actions

CHUHAO PENG's personal rewrite and approval remain pending. Creating and pushing the GitHub repository, confirming the public setting, deploying through Streamlit Community Cloud, recording the verified URLs, recreating any final submission ZIP after approval, and submitting through Moodle also remain pending. This interaction does not claim any of those actions are complete.
