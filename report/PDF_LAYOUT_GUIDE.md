# Word/PDF layout guide

This guide records the formatting rules for `report/FINAL_REPORT.md`, `report/report.docx`, and `report/report.pdf`. CHUHAO PENG completed the Interaction 008 economic-interpretation review, but final visual approval of the regenerated Word/PDF remains pending.

## Page limit and document structure

- Keep the written narrative to a maximum of **10 pages**. References and appendices sit outside that narrative count; exhibits may be placed in an appendix so the main body remains concise.
- Confirm whether the course counts the title page within the limit; if the rule is ambiguous, use the conservative interpretation.
- Use a single-column main body on A4 paper. Use a landscape appendix page only where a dense exhibit, especially the all-sector small multiples, remains materially more readable.
- Keep methodology detail necessary to interpret results in the main body. Move audit-oriented figures and full lookup tables to the appendix.
- Do not reduce body text, captions, or axis labels below a comfortably readable size merely to meet the limit.

## Title page

Include only verified information:

- **Cross-Asset Allocation Lens**
- **FINS5545 Project B — Final Report**
- **CHUHAO PENG**
- **z5711503**
- submission date: **8 August 2026**
- repository URL and deployed Streamlit URL only after they actually exist and have been verified

Do not state that the report is personally approved until CHUHAO PENG has completed the required rewrite/review and approval.

## Suggested main-body evidence

The main body should carry the minimum evidence needed to understand the result:

1. **Table 1 — Net OOS performance by fund**, formatted from `results/tables/report_fund_summary.csv`.
2. **Figure 1 — Fund universe return–risk overview**, `results/figures/report_fund_return_volatility.png`.
3. **Figures 2 and 3 — Representative net growth and drawdown**, `report_selected_growth.png` and `report_selected_drawdown.png`; place side by side only if every label remains readable.
4. **Figure 5 — Materials sentiment index**, `report_materials_sentiment_index.png`, as the detailed missingness-aware example.
5. **Table 2 — Base versus fixed augmented Equity Risk Parity**, formatted from `results/tables/fusion_comparison.csv`.
6. **Figure 8 — Fusion net growth**, `results/figures/fusion_growth_of_one.png`, beside the negative-result interpretation.
7. **Figure 12 — Illustrative allocation**, `results/figures/report_allocation_example.png`, beside the app and cost-limit disclosure.

If the 10-page narrative limit becomes tight, keep Table 1, Figure 1, Table 2, and Figure 8 in the main body first. Move other exhibits to the appendix without removing their in-text references.

## Appendix exhibit order

Use this order so the appendix follows the report's analytical flow. Exhibits already retained in the main body do not need to be duplicated.

Place the cited **References** section after the written narrative and before Appendix A. Include only works cited in the report.

### Appendix A — Sentiment evidence

1. **Appendix Figure A1:** `results/figures/report_all_sector_sentiment_small_multiples.png` — all ten finance-VADER equity-sector indices on a common 0–100 scale with genuine gaps preserved. Prefer a full landscape page.
2. `results/figures/report_materials_sentiment_index.png` — Materials detailed index, if moved from the main body.
3. `results/figures/report_materials_trading_signal.png` — lagged causal trading signal and carry markers.
4. `results/figures/report_materials_coverage.png` — eligible-ticker headline coverage.

### Appendix B — Portfolio evidence

1. `results/figures/report_equity_weights_over_time.png` — Equity target weights through time.
2. `results/figures/report_selected_growth.png` — representative selected-fund growth, if moved from the main body.
3. `results/figures/report_selected_drawdown.png` — representative selected-fund drawdown, if moved from the main body.
4. `results/tables/report_fund_summary.csv` — full 13-fund lookup table, if the formatted main-body table is shortened.

### Appendix C — Fusion evidence

1. `results/figures/fusion_growth_of_one.png` — base versus augmented net growth, if moved from the main body.
2. `results/figures/fusion_drawdown.png` — base versus augmented net drawdown.
3. `results/figures/fusion_sector_multiplier_activity.png` — sector multiplier activity.
4. `results/figures/report_fusion_latest_weight_changes.png` — latest largest target-weight changes.
5. `results/tables/fusion_comparison.csv` — exact base/augmented metrics supporting Table 2.

### Appendix D — Allocation evidence and audit map

1. `results/figures/report_allocation_example.png` — illustrative allocation, if moved from the main body.
2. `results/tables/report_allocation_example_weights.csv` — exact illustrative weights.
3. `results/tables/report_allocation_example_metrics.csv` — exact illustrative summary metrics.
4. `results/tables/report_exhibit_catalog.csv` — exhibit-to-source and supported-claim audit map; include only if the final submission benefits from an audit appendix.

## Page numbering and Word styles

- Leave the title page unnumbered visually. Start visible Arabic page numbers on the first narrative page unless the course template requires another convention.
- Continue page numbering through the appendix, or use appendix numbering such as `A-1`, `A-2` consistently.
- Use Word heading styles for all numbered report headings so navigation and any table of contents update correctly.
- Keep figure/table captions attached to their exhibit and prevent headings from being stranded at the bottom of a page.
- Use page breaks rather than repeated blank lines to control exhibit placement.

## Captions and source notes

- Number main-body figures and tables exactly as referenced in `FINAL_REPORT.md`; label the all-sector exhibit **Appendix Figure A1**.
- Put the caption directly below each figure and above or below each table consistently.
- Each caption should state what is shown, the relevant period, units or scale, and any comparison basis needed to read it.
- Keep each source note immediately below its exhibit. Preserve the exact committed source filename(s).
- For the all-sector figure, state: finance-VADER only; ten equity sectors; 2020-01-02 to 2023-12-29; common 0–100 scale; missing dates remain gaps and are not replaced with 50.
- Do not use a caption or title to imply statistical significance, predictability, live holdings, or investment advice.

## Final checks before exporting `report/report.pdf`

1. Record that CHUHAO PENG completed the economic-interpretation review, then obtain separate final visual approval after the Interaction 008 Word/PDF regeneration.
2. Confirm the narrative is no more than 10 pages and the appendix is clearly separated.
3. Reconcile every displayed number against the committed CSV cited by the report.
4. Confirm every in-text figure/table reference matches its final caption and page location.
5. Ensure every embedded image is the committed high-resolution PNG and has not been stretched disproportionately.
6. Inspect all axes, legends, labels, dates, captions, and source notes at 100% zoom; no text may be clipped or unreadable.
7. Confirm all five app-tab names match `streamlit_app.py`: Fund Explorer, Fund Fact Sheet, Allocation Lab, Sentiment Lab, and Fusion Evidence.
8. Keep the fusion underperformance and higher-turnover result visible and unchanged.
9. Remove comments, tracked changes, placeholders, draft watermarks, private paths, and unverified URLs.
10. Update Word fields, page numbers, cross-references, and any table of contents immediately before export.
11. Export to `report/report.pdf`, then open the PDF and inspect every page, bookmark, link, image, caption, and page break.
12. Run the hand-in checker again only after the personally approved PDF exists; do not infer GitHub, deployment, public-repository, or Moodle completion from a local PDF.
