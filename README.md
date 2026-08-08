# Cross-Asset Allocation Lens

Cross-Asset Allocation Lens is a FINS5545 Project B repository containing an audited walk-forward fund engine, a coverage-aware sector-sentiment extension, a fixed sentiment-fusion experiment, and a Streamlit investor interface. It compares 13 systematic fund prototypes across Equity, Crypto, and Combined universes.

The principal empirical finding is deliberately unrevised: the predeclared sentiment overlay did not improve base Equity Risk Parity over the common 2021–2023 OOS sample and produced higher turnover. The app and report keep that negative result visible.

This project is analytical and educational only. It is not personalised financial advice, a live trading system, or a promise of future returns.

## Links

- **Public GitHub repository:** https://github.com/CHUHAOPENG/cross-asset-allocation-lens-fins5545
- **Live Streamlit application:** https://cross-asset-allocation-lens-fins5545.streamlit.app/

## Quick start

The repository is designed for Python 3.11 or later. From the project root, create and activate a virtual environment, then choose one installation path.

App-only installation:

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Full analytical reproduction and tests:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python scripts/run_part_b.py
python scripts/build_report_artifacts.py
pytest -q
python scripts/check_handin.py
```

`scripts/run_part_b.py` loads only the official course source through `src/data_access.py` and reproduces canonical artifacts under `results/`. It may require network access unless the official ZIP is already available through the loader's cache. It never substitutes fabricated data.

`scripts/build_report_artifacts.py` is presentation-only. It reads committed analytical outputs, creates the report figures and tables, and calculates the report's explicitly illustrative allocation. It does not load raw data, fit models, optimise portfolios, score sentiment, or rerun fusion.

## What the project contains

- `streamlit_app.py` — five-tab investor interface reading committed outputs only.
- `.streamlit/config.toml` — explicit accessible light theme and local server settings.
- `src/` — data cleaning, return construction, portfolio methods, sentiment, fusion, and app utilities.
- `scripts/run_part_b.py` — canonical end-to-end analytical runner.
- `scripts/build_report_artifacts.py` — deterministic report-only presentation builder.
- `scripts/check_handin.py` — repository hand-in checks.
- `results/data/` — committed app-ready return, weight, sentiment, and fusion artifacts.
- `results/tables/` — metrics, audits, manifests, and report tables.
- `results/figures/` — analytical and report figures.
- `report/FINAL_REPORT.md` — complete report source with linked evidence and limitations.
- `tests/` — analytical, timing, integrity, app, and report-artifact regression tests.
- `context/` — project decisions, data guide, and approved Part A handoff.
- `ai/` — AI-use notes and verbatim interaction records.

## Analytical design

The base fund set combines three universes with four methods:

| Universe | Calendar and annualisation | Methods |
|---|---|---|
| Equity | Observed equity dates; 252 | Equal Weight, Minimum Variance, Risk Parity, Maximum Sharpe |
| Crypto | Native seven-day dates; 365 | Equal Weight, Minimum Variance, Risk Parity, Maximum Sharpe |
| Combined | Observed equity dates; 252 | Equal Weight, Minimum Variance, Risk Parity, Maximum Sharpe |

The engine uses an expanding walk-forward OOS schedule, month-end decisions effective on the next observed holding date, long-only fully invested constraints, a dynamic asset cap, fixed covariance/mean shrinkage, recorded solver fallbacks, and a 10-basis-point one-way turnover cost. Missing returns are never filled. Crypto returns are calculated on their native calendar before selection onto equity dates for Combined funds.

News uses conservative Rule A calendar-date mapping followed by an additional one-observed-equity-day trading lag. No supplied news remains missing rather than neutral. The causal sector signal uses expanding standardisation, bounded five-day carry, and coverage decay. The primary overlay uses the frozen finance-VADER signal with fixed `lambda = 0.10`; its parameters are not retuned after observing performance.

The exact locked decisions are recorded in `context/PROJECT_DECISIONS.md`. The reproducibility manifest records the official source checksum, environment, constants, row counts, and canonical output hashes in `results/tables/run_manifest.csv`.

## Application behavior

The app reads precomputed committed files under `results/` and has no imports from the analytical engines or network layer. Its five tabs are exactly:

- **Fund Explorer** — filter and compare all 13 funds on net or gross metrics, return versus volatility, growth, and drawdown.
- **Fund Fact Sheet** — inspect one fund's OOS metrics, gross/net growth, methodology, latest historical target weights, weight history, and target-table download.
- **Allocation Lab** — simulate user-specified weights across two to six funds using Buy & Hold or Monthly Reset on the exact common finite OOS period; it does not optimise or recommend weights.
- **Sentiment Lab** — inspect a selected sector/model's gap-preserving index, coverage, optional causal z-score, latest sector snapshot, and Rule A/lag/missingness disclosure.
- **Fusion Evidence** — compare base and sentiment-augmented Equity Risk Parity, including net growth, drawdown, turnover, cost, sector multiplier activity, latest target changes, and the unrevised negative result.

The Allocation Lab accepts two to six non-negative fund weights summing to 100% and simulates Buy & Hold or Monthly Reset over the exact common OOS intersection. It does not optimise or recommend an allocation. Fund-level returns include the recorded analytical trading costs, but the simulator applies no additional management fee, tax, or cross-fund transaction cost.

## Reports and evidence

Open [`report/FINAL_REPORT.md`](report/FINAL_REPORT.md) for the Markdown source, [`report/report.docx`](report/report.docx) for the editable course-formatted report, and [`report/report.pdf`](report/report.pdf) for the technically checked PDF export. The complete report figure-to-source map is in `results/tables/report_exhibit_catalog.csv`.

The Word and PDF files have been generated, technically reviewed, and personally reviewed by CHUHAO PENG. The current report version is approved to proceed to final deployment. Portfolio, sentiment, fusion, app, and report analytics remain frozen.

## Validation

Run the local hand-in gates from the project root:

```bash
pytest -q
python scripts/check_handin.py
git diff --check
git status --short
```

To validate the local app:

```bash
streamlit run streamlit_app.py --server.headless true
```

Then open `/_stcore/health` on the local address shown by Streamlit. A local pass does not prove that the repository has been pushed, made public, deployed, or submitted.

## Hand-in boundary

The repository excludes raw data, virtual environments, caches, secrets, and local ZIP files. `scripts/make_submission_zip.sh` creates a clean ZIP outside the project directory and validates its archive structure. Public GitHub publication, Streamlit deployment, and logged-out production verification are complete. Uploading the verified final ZIP and submitting the two public URLs to Moodle remains the final user-controlled release step.
