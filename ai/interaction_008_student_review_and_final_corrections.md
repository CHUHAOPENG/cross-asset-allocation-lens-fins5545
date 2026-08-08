# Interaction 008 — Student-reviewed final corrections and hand-in readiness

## Prompt

```text
Interaction 008 — Student-reviewed final corrections and hand-in readiness

Work only inside z5711503_projectB.

CHUHAO PENG has now personally reviewed the report's economic interpretation
and supplied specific corrections. Treat these as student-directed edits.

All analytical logic, portfolio/sentiment/fusion parameters, canonical CSV
values, approved analytical figures, and Streamlit behaviour are frozen.

Do not rerun or retune alternative strategies.
Do not push or deploy in this interaction.

Submission date is confirmed as:

8 August 2026

============================================================
1. Preserve the student review in the AI workflow
============================================================

Create:

ai/interaction_008_student_review_and_final_corrections.md

Preserve this full prompt verbatim.

Record that CHUHAO PENG personally reviewed the following interpretations:

- there is no single best fund because the answer depends on the objective;
- Maximum Sharpe optimises estimated ex-ante Sharpe and need not maximise
  realised OOS Sharpe;
- Crypto's high sample returns must be interpreted together with very deep
  drawdowns;
- finance-VADER score/classification changes are sensitivity evidence, not
  evidence of superior accuracy;
- the fixed fusion rule must not be retuned after seeing its OOS result;
- Section 8 limitations are accepted but should add the possible fixed-universe
  selection/survivorship limitation;
- the three recommendations are accepted, with Recommendations 2 and 3 to be
  made more operationally concrete.

Record that the student requested the formatting and wording corrections below.

Do not claim final post-regeneration visual approval yet. State that the
student-directed economic review has occurred, while final inspection of the
new Word/PDF remains pending.

============================================================
2. Final report source corrections
============================================================

Update report/FINAL_REPORT.md without changing any canonical analytical value.

A. Executive summary — "best by objective"

Retain the conclusion that there is no single best fund, but make it more
specific. Add a concise sentence explaining that "best" depends on the
objective.

Use the actual committed values and communicate approximately:

- Crypto Minimum Variance had the highest sample Sharpe among the 13 funds
  (0.934), but suffered a -72.73% maximum drawdown;
- Equity Minimum Variance had the lowest volatility within Equity (12.70%);
- Combined Risk Parity had the highest Sharpe within Combined (0.774).

Do not call any fund universally best.

B. Maximum Sharpe interpretation

In Section 4, retain the current OOS finding but soften causal language.

Use wording consistent with:

"The result is consistent with noisy expected-return estimates: Maximum Sharpe
optimises an estimated ex-ante objective, which does not guarantee the highest
realised OOS Sharpe."

You may also mention the observed higher turnover and binding constraints, but
do not present any single mechanism as proven.

C. Crypto drawdown economic meaning

After the paragraph discussing Crypto drawdowns, add one concise sentence:

- recovering from a -72.73% drawdown requires approximately +267%;
- recovering from a -81.59% drawdown requires approximately +443%.

Explain that this makes the economic meaning of the loss path more severe than
the drawdown percentage alone may suggest.

These are arithmetic break-even recoveries, not forecasts.

D. finance-VADER interpretation

Retain the current distinction:

- 3,860 changed compound scores;
- 1,199 changed +/-0.05 classifications;
- these demonstrate model sensitivity only.

Do not describe the finance lexicon as more accurate or predictive without a
labelled validation sample.

E. Tracking error units

Replace:

"tracking error is 0.00288"

with:

"tracking error is 0.00288, or approximately 0.29% annualised"

The existing fusion implementation calculates tracking error as the standard
deviation of daily active returns multiplied by sqrt(252). Do not alter that
calculation or the CSV.

F. Fixed-universe limitation

Add one bullet to Section 8 stating carefully that the supplied 50-equity /
10-crypto asset universe is treated as fixed and the project does not verify
point-in-time constituent membership.

Therefore selection/survivorship bias cannot be ruled out.

Do NOT state that survivorship bias has been proven to exist.

G. Recommendations 2 and 3

Keep the existing recommendations but make them more executable.

For Recommendation 2, specify a future implementation-cost sensitivity grid,
for example:
- 10 bps,
- 25 bps,
- 50 bps one-way transaction cost,

and explain that rankings should be rechecked across that range. These are
future sensitivity scenarios, not new current-project results.

For Recommendation 3, make the monitoring recommendation operational. State
that a production version should predefine data-health / signal-health
thresholds before launch. A sensible example may include:
- reverting to the base portfolio after the existing five-day maximum stale
  signal window;
- defining a minimum effective-coverage threshold before live deployment;
- escalating or reverting on failed solver/data-health checks.

If an example coverage threshold is shown, label it explicitly as a proposed
future operational threshold, not as a validated optimum.

============================================================
3. Course-supported method references
============================================================

The Week 10 revision lecture supplied the following references. Add concise
in-text citations only where directly relevant and add a References section
outside the written-narrative count.

Use only references actually cited in the report.

At minimum consider:

- Markowitz, H. (1952), "Portfolio Selection", The Journal of Finance,
  7(1), 77-91.
- Sharpe, W. F. (1966), "Mutual Fund Performance", The Journal of Business,
  39(1), 119-138.
- Maillard, S., Roncalli, T., & Teiletche, J. (2010), "The Properties of
  Equally Weighted Risk Contribution Portfolios", The Journal of Portfolio
  Management, 36(4), 60-70.
- DeMiguel, V., Garlappi, L., & Uppal, R. (2009), "Optimal versus Naive
  Diversification: How Inefficient is the 1/N Portfolio Strategy?",
  Review of Financial Studies, 22(5), 1915-1953.
- Hutto, C. J., & Gilbert, E. (2014), "VADER: A Parsimonious Rule-Based
  Model for Sentiment Analysis of Social Media Text", ICWSM, 8(1), 216-225.
- Tetlock, P. C. (2007), "Giving Content to Investor Sentiment: The Role of
  Media in the Stock Market", Journal of Finance, 62(3), 1139-1168.

Do not invent additional literature.
Do not change the project's custom methodology to match the lecture examples.

Suggested usage:
- Markowitz / Sharpe / Maillard in the portfolio-method discussion;
- DeMiguel in the cautious discussion of Equal Weight as a difficult OOS
  benchmark;
- Hutto & Gilbert when introducing VADER;
- Tetlock only as general motivation for studying news sentiment.

============================================================
4. Appendix D human-readable formatting
============================================================

Do not alter:

results/tables/report_allocation_example_weights.csv
results/tables/report_allocation_example_metrics.csv

Those remain machine-readable source artifacts.

In the human-facing Markdown/Word/PDF Appendix tables, format:

Appendix Table D1:
- 0.25 -> 25.0%

Appendix Table D2:
- Cumulative Return 0.3313467147 -> 33.13%
- Annualised Return 0.1493763267 -> 14.94%
- Annualised Volatility 0.3259476117 -> 32.59%
- Sharpe 0.4582832373 -> 0.458
- Max Drawdown -0.5059418559 -> -50.59%

Keep dates, observations, periods-per-year and excluded-date count in their
natural formats.

============================================================
5. Word/PDF formatting corrections
============================================================

Regenerate:

report/report.docx
report/report.pdf

The cover MUST contain:

Submission date: 8 August 2026

There must be no occurrence of:

Pending confirmation

in either Word or PDF.

Improve the Section 5 page break. In the current PDF, the opening paragraph of
Section 5 is split awkwardly across pages after "The finance".

Prefer either:
- keeping the Section 5 heading and its first paragraph together; or
- starting Section 5 on the next narrative page.

Do not compress text excessively just to keep the old pagination.

Narrative may increase from 7 to 8 pages if necessary, but must remain <=10
written-narrative pages. Appendices and References remain outside the narrative
limit.

Maintain:
- readable A4 layout;
- current title-page design;
- current figure quality;
- Appendix A1 with all ten sectors;
- no clipped tables or captions;
- no private paths or unverified deployment URLs.

============================================================
6. Remove the unused CLAUDE starter placeholder
============================================================

CLAUDE.md is still the supplied placeholder even though Claude Code was not used.

Do not pretend that Claude was used.

Replace CLAUDE.md with a short truthful note such as:

# Claude Code status

Claude Code was not used for this Project B build. Codex was the implementation
agent used by CHUHAO PENG. The operative project-specific agent instructions are
recorded in AGENTS.md, and the interaction/prompt records are under ai/.

This file is retained because CLAUDE.md was part of the supplied starter
structure; it is not an additional AI workflow log.

Ensure the phrase "replace this placeholder" no longer exists in CLAUDE.md.

============================================================
7. AI status update
============================================================

Update ai/AI_NOTES.md accurately:

- CHUHAO PENG has now personally reviewed the report's economic interpretations
  and directed the Interaction 008 corrections;
- do not say the regenerated PDF has received final visual approval until that
  occurs;
- portfolio, sentiment, fusion and app analytics remain frozen;
- GitHub push/public setting, Streamlit deployment, final logged-out URL check,
  final clean ZIP and Moodle submission remain pending.

Update context/PROJECT_DECISIONS.md only if needed for final status wording.
Do not alter analytical decisions.

============================================================
8. Clean local hygiene before validation
============================================================

Remove transient local files before running the final hand-in checker:

- .DS_Store
- report/.DS_Store
- __pycache__/
- *.pyc
- pytest caches if present

Do not delete committed analytical files.

============================================================
9. Validation
============================================================

Run:

pytest -q
python scripts/check_handin.py
git diff --check
git status --short

Additionally verify programmatically:

- both report.docx and report.pdf contain "8 August 2026";
- neither contains "Pending confirmation";
- tracking-error wording contains approximately 0.29% annualised;
- Appendix D report presentation uses percentages while source CSVs are
  byte-for-byte analytically unchanged;
- narrative page count remains <=10;
- every PDF page has been visually inspected;
- all references cited in text appear in the References section;
- no uncited reference is required, and no reference was invented;
- CLAUDE.md contains no starter-placeholder wording;
- all canonical Interaction 004 analytical hashes remain 20/20 unchanged;
- Streamlit local health remains HTTP 200.

============================================================
10. Commit
============================================================

Commit only after all validation succeeds:

docs: apply student-reviewed final report corrections

Do not push or deploy.

Report:

- commit hash;
- exact changed-file list;
- Word page count;
- PDF total pages;
- PDF narrative-page count;
- appendix/reference-page count;
- PDF SHA-256;
- tests;
- check_handin result;
- app health result;
- final git status;
- any remaining user-controlled action.
```

## Student-directed economic review

CHUHAO PENG personally reviewed and accepted the report's economic interpretation that there is no universally best fund because the answer depends on the objective; Maximum Sharpe optimises an estimated ex-ante objective and need not maximise realised OOS Sharpe; Crypto's high sample returns must be interpreted with its very deep drawdowns; finance-VADER score and classification changes are sensitivity evidence rather than proof of superior accuracy; and the fixed fusion rule must not be retuned after observing its OOS result.

CHUHAO PENG also accepted the existing Section 8 limitations while directing the addition of the possible fixed-universe selection/survivorship limitation. The three recommendations were accepted, with Recommendations 2 and 3 directed to become more operationally concrete.

## Student-requested corrections

The student directed the best-by-objective executive-summary clarification, softened Maximum Sharpe mechanism language, arithmetic Crypto recovery examples, annualised tracking-error units, fixed-universe limitation, executable future cost-sensitivity grid, operational data/signal-health controls, course-supported citations, human-readable Appendix D formatting, confirmed submission date, Section 5 page-break correction, truthful Claude Code status, and final hygiene and validation steps.

## Status before regeneration

The student-directed economic review has occurred. Final post-regeneration visual approval of the new Word and PDF remains pending. Portfolio, sentiment, fusion, and app analytics remain frozen, and no push or deployment is authorised in this interaction.

## Report formatting and technical inspection

The Word report was regenerated in A4 course-report format with the confirmed submission date 8 August 2026. Section 5 now begins on a new narrative page with its first paragraph intact. The rendered Word document and PDF each contain 20 pages: one title page, seven narrative pages, one References page, and eleven appendix pages. References and appendices remain outside the narrative-page limit.

Codex visually inspected every one of the 20 regenerated PDF pages. No clipped text or tables, cropped or stretched figures, separated captions, missing symbols, private paths, placeholders, or unverified URLs were found. Appendix Figure A1 visibly contains all ten equity sectors. This is a technical visual inspection, not CHUHAO PENG's final post-regeneration visual approval.

The final PDF is 3,051,794 bytes with SHA-256 `ad3ff7c4f9f978b1b3615a69a89509dd503355cae562bd8bcd8cdde20370d9b6`.

## Validation evidence

- `pytest -q`: 82 passed, with two existing NumPy deprecation warnings. The first sandboxed run had 81 passes and one smoke-test failure because DNS access to the two official data ZIP URLs was blocked; the same suite passed after authorised network access. No course code or data were changed to bypass the failure.
- `python scripts/check_handin.py`: 23 checks passed; the checker no longer reports a missing PDF.
- `git diff --check`: passed.
- Streamlit headless health endpoint and root page: HTTP 200.
- Frozen Interaction 004 analytical hashes: 20/20 verified unchanged.
- The finance-VADER figure input contains all ten equity sectors. It retains 238 missing compound values, and none of those missing observations has an index value of 50.
- Appendix D source hashes remain unchanged: `report_allocation_example_weights.csv` is `80b338349c489193e90a80a45babe2df129b2a3ab3921f5a3e62e73686451488`; `report_allocation_example_metrics.csv` is `00e4092fa1af88d2a3fc033918954a3779241b4f60f35f37ad3c0298564d351b`.
- All 25 local report links resolve. All six references are cited in the narrative, and no uncited or invented reference was added.
- The DOCX accessibility audit reported zero high-, medium-, or low-severity findings; all four table geometries are internally consistent; 13 figures are inline; and all seven sections use A4 dimensions, with only Appendix Figure A1 in landscape orientation.

## Exact changed-file list

- `CLAUDE.md`
- `ai/AI_NOTES.md`
- `ai/interaction_008_student_review_and_final_corrections.md`
- `context/PROJECT_DECISIONS.md`
- `report/FINAL_REPORT.md`
- `report/PDF_LAYOUT_GUIDE.md`
- `report/report.docx`
- `report/report.pdf`

## Remaining student-controlled actions

CHUHAO PENG's final visual review and approval of the regenerated Word and PDF remain pending. GitHub push and public-repository confirmation, Streamlit deployment, the final logged-out public-URL check, creation of a refreshed clean submission ZIP, and Moodle submission also remain pending. No push or deployment occurred.
