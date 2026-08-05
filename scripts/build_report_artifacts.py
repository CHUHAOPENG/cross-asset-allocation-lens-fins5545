"""Build report-only figures and tables from committed analytical artifacts.

This script does not load raw data, fit a model, optimise a portfolio, or alter
the approved analytical CSVs. It applies presentation transforms to the
committed results and creates the illustrative allocation used in the report.

Run from the project root:

    python scripts/build_report_artifacts.py
"""
from __future__ import annotations

import pathlib
import sys
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import app_utils  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGURES = ROOT / "results/figures"
TABLES = ROOT / "results/tables"
DATA = ROOT / "results/data"

INK = "#1F2933"
MUTED = "#5F6F7F"
GRID = "#DDE5EC"
NAVY = "#17324D"
BLUE = "#2F6B9A"
CYAN = "#5AA6A6"
ORANGE = "#D97745"
GOLD = "#C99A2E"
RED = "#B94A48"
PURPLE = "#8B5FBF"
PAPER = "#FFFFFF"

REPRESENTATIVE_FUNDS = [
    "equity_risk_parity",
    "crypto_risk_parity",
    "combined_risk_parity",
    "equity_risk_parity_sentiment",
]
REPRESENTATIVE_COLORS = {
    "Equity — Risk Parity": BLUE,
    "Crypto — Risk Parity": ORANGE,
    "Combined — Risk Parity": CYAN,
    "Equity — Risk Parity + Sentiment": RED,
}
EQUITY_METHOD_FUNDS = [
    "equity_equal_weight",
    "equity_min_variance",
    "equity_risk_parity",
    "equity_max_sharpe",
]
SENTIMENT_SECTOR = "Materials"
SENTIMENT_MODEL = "finance_vader"
EXPECTED_EQUITY_SECTORS = (
    "Comm",
    "Consumer",
    "Energy",
    "Financials",
    "Healthcare",
    "Industrials",
    "Materials",
    "RealEstate",
    "Tech",
    "Utilities",
)

REPORT_FIGURES = [
    "report_fund_return_volatility.png",
    "report_selected_growth.png",
    "report_selected_drawdown.png",
    "report_equity_weights_over_time.png",
    "report_materials_sentiment_index.png",
    "report_materials_trading_signal.png",
    "report_materials_coverage.png",
    "report_all_sector_sentiment_small_multiples.png",
    "report_fusion_latest_weight_changes.png",
    "report_allocation_example.png",
]
REPORT_TABLES = [
    "report_fund_summary.csv",
    "report_allocation_example_weights.csv",
    "report_allocation_example_metrics.csv",
    "report_exhibit_catalog.csv",
]


def _style_axis(axis: plt.Axes, *, grid_axis: str = "y") -> None:
    axis.set_facecolor(PAPER)
    axis.tick_params(colors=INK, labelsize=9)
    axis.xaxis.label.set_color(INK)
    axis.yaxis.label.set_color(INK)
    axis.title.set_color(INK)
    axis.grid(True, axis=grid_axis, color=GRID, linewidth=0.8, alpha=0.75)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#AAB7C4")
    axis.spines["bottom"].set_color("#AAB7C4")


def _finish_figure(
    figure: plt.Figure,
    path: pathlib.Path,
    *,
    source_note: str,
    top: float = 0.88,
) -> None:
    figure.patch.set_facecolor(PAPER)
    figure.text(0.01, 0.012, source_note, fontsize=8, color=MUTED, ha="left")
    figure.tight_layout(rect=(0, 0.045, 1, top))
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor=PAPER)
    plt.close(figure)


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    output = frame.copy()
    for column in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[column]):
            output[column] = output[column].dt.strftime("%Y-%m-%d")
    path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(path, index=False, float_format="%.10g")


def _method_label(method: str) -> str:
    return {
        "equal_weight": "Equal Weight",
        "minimum_variance": "Minimum Variance",
        "risk_parity": "Risk Parity",
        "max_sharpe": "Maximum Sharpe",
        "risk_parity_sentiment": "Risk Parity + Sentiment",
    }[method]


def _build_fund_summary(artifacts: app_utils.AppArtifacts) -> pd.DataFrame:
    catalog = artifacts.fund_catalog[[
        "fund_id", "display_name", "universe", "method",
        "first_live_date", "last_date", "periods_per_year",
    ]].copy()
    metrics = artifacts.performance_metrics.drop(
        columns=["universe", "method", "first_live_date", "last_date", "periods_per_year"]
    )
    summary = catalog.merge(metrics, on="fund_id", validate="one_to_one")
    summary["universe"] = summary["universe"].str.title()
    summary["method"] = summary["method"].map(_method_label)
    columns = [
        "fund_id", "display_name", "universe", "method", "first_live_date",
        "last_date", "observations", "periods_per_year",
        "cumulative_return_net", "annualised_return_net",
        "annualised_volatility_net", "sharpe_net", "max_drawdown_net",
        "total_turnover", "total_trading_cost", "rebalance_count",
        "fallback_count",
    ]
    return summary[columns].sort_values("display_name", kind="mergesort").reset_index(drop=True)


def _fund_scatter(summary: pd.DataFrame) -> None:
    figure, axes = plt.subplots(
        1, 2, figsize=(13, 6.8), gridspec_kw={"width_ratios": [1.45, 1]}
    )
    style = {
        "Equity": (BLUE, "o"),
        "Crypto": (ORANGE, "s"),
        "Combined": (CYAN, "D"),
    }
    panels = [
        (axes[0], ["Equity", "Combined"], "Equity and Combined"),
        (axes[1], ["Crypto"], "Crypto"),
    ]
    for axis, universes, panel_title in panels:
        for universe in universes:
            colour, marker = style[universe]
            rows = summary.loc[summary["universe"].eq(universe)]
            axis.scatter(
                rows["annualised_volatility_net"],
                rows["annualised_return_net"],
                s=72,
                color=colour,
                marker=marker,
                edgecolor=PAPER,
                linewidth=0.9,
                label=universe,
                zorder=3,
            )
        axis.set_title(panel_title, loc="left", fontsize=11, fontweight="bold")

    augmented = summary.loc[summary["fund_id"].eq("equity_risk_parity_sentiment")].iloc[0]
    axes[0].scatter(
        [augmented["annualised_volatility_net"]],
        [augmented["annualised_return_net"]],
        s=155,
        facecolors="none",
        edgecolors=RED,
        linewidth=2.0,
        marker="o",
        label="Sentiment overlay",
        zorder=4,
    )

    short_labels = {
        "combined_equal_weight": "Combined EW",
        "combined_max_sharpe": "Combined Max Sharpe",
        "combined_min_variance": "Combined Min Var",
        "combined_risk_parity": "Combined RP",
        "crypto_equal_weight": "Crypto EW",
        "crypto_max_sharpe": "Crypto Max Sharpe",
        "crypto_min_variance": "Crypto Min Var",
        "crypto_risk_parity": "Crypto RP",
        "equity_equal_weight": "Equity EW",
        "equity_max_sharpe": "Equity Max Sharpe",
        "equity_min_variance": "Equity Min Var",
        "equity_risk_parity": "Equity RP",
        "equity_risk_parity_sentiment": "Equity RP + Sentiment",
    }
    offsets = {
        "combined_equal_weight": (6, 7),
        "combined_max_sharpe": (6, 6),
        "combined_min_variance": (-106, -15),
        "combined_risk_parity": (6, 7),
        "crypto_equal_weight": (6, 7),
        "crypto_max_sharpe": (6, -14),
        "crypto_min_variance": (-86, 7),
        "crypto_risk_parity": (-66, -14),
        "equity_equal_weight": (-65, -15),
        "equity_max_sharpe": (6, -15),
        "equity_min_variance": (-78, 7),
        "equity_risk_parity": (-57, 7),
        "equity_risk_parity_sentiment": (6, -16),
    }
    for row in summary.itertuples(index=False):
        axis = axes[1] if row.universe == "Crypto" else axes[0]
        axis.annotate(
            short_labels[row.fund_id],
            (row.annualised_volatility_net, row.annualised_return_net),
            xytext=offsets[row.fund_id],
            textcoords="offset points",
            fontsize=8.2,
            color=INK,
        )

    panel_limits = [
        ((0.105, 0.235), (0.045, 0.185)),
        ((0.62, 0.86), (0.56, 0.71)),
    ]
    for axis, (x_limits, y_limits) in zip(axes, panel_limits, strict=True):
        axis.set_xlim(*x_limits)
        axis.set_ylim(*y_limits)
        axis.xaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
        axis.yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
        axis.set_xlabel("Net annualised volatility")
        _style_axis(axis, grid_axis="both")
        axis.legend(frameon=False, ncol=2, loc="upper left", fontsize=8.5)
    axes[0].set_ylabel("Net annualised arithmetic return")
    figure.suptitle("Fund universe return–risk overview", x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
    figure.text(
        0.01, 0.91,
        "Thirteen walk-forward funds; panels use different scales for readability, with native OOS calendars and 252/365 annualisation.",
        fontsize=10.5, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_fund_return_volatility.png",
        source_note="Source: results/tables/performance_metrics.csv and results/data/fund_catalog.csv. Returns are net of the recorded 10 bps one-way cost model.",
        top=0.88,
    )


def _selected_return_figures(artifacts: app_utils.AppArtifacts) -> None:
    labels = app_utils.fund_label_map(artifacts.fund_catalog)
    selected = artifacts.fund_returns.loc[
        artifacts.fund_returns["fund_id"].isin(REPRESENTATIVE_FUNDS)
    ].copy()
    selected["Fund"] = selected["fund_id"].map(labels)
    for value_column, filename, title, y_label, percent in (
        ("growth_net", "report_selected_growth.png", "Selected-fund net growth of $1", "Growth of $1", False),
        ("drawdown_net", "report_selected_drawdown.png", "Selected-fund net drawdown", "Drawdown", True),
    ):
        figure, axis = plt.subplots(figsize=(12.5, 6.8))
        for fund_name, group in selected.groupby("Fund", sort=False):
            axis.plot(
                group["date"],
                group[value_column],
                label=fund_name,
                color=REPRESENTATIVE_COLORS[fund_name],
                linewidth=2.1,
            )
        if percent:
            axis.yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
            axis.axhline(0, color=INK, linewidth=0.8)
        axis.xaxis.set_major_locator(mdates.YearLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        axis.set_xlabel("OOS date")
        axis.set_ylabel(y_label)
        _style_axis(axis)
        axis.legend(
            frameon=False, ncol=2, loc="lower left", bbox_to_anchor=(0, 1.005),
            borderaxespad=0,
        )
        figure.suptitle(title, x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
        figure.text(
            0.01, 0.91,
            "Risk Parity is held constant across Equity, Crypto, and Combined; the fixed sentiment overlay is shown separately.",
            fontsize=10.5, color=MUTED,
        )
        _finish_figure(
            figure,
            FIGURES / filename,
            source_note="Source: results/data/fund_returns.csv. Crypto uses its native seven-day OOS calendar; Equity, Combined, and the overlay use observed equity dates.",
            top=0.88,
        )


def _equity_weight_history(artifacts: app_utils.AppArtifacts) -> None:
    labels = app_utils.fund_label_map(artifacts.fund_catalog)
    frame = artifacts.fund_weights.loc[
        artifacts.fund_weights["fund_id"].isin(EQUITY_METHOD_FUNDS)
    ].copy()
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True, sharey=True)
    colours = [NAVY, BLUE, ORANGE, CYAN, PURPLE]
    for axis, fund_id in zip(axes.flat, EQUITY_METHOD_FUNDS, strict=True):
        subset = frame.loc[frame["fund_id"].eq(fund_id)]
        top_tickers = (
            subset.groupby("ticker")["target_weight"].mean()
            .sort_values(ascending=False).head(5).index.tolist()
        )
        for colour, ticker in zip(colours, top_tickers, strict=True):
            rows = subset.loc[subset["ticker"].eq(ticker)]
            axis.plot(
                rows["effective_date"], rows["target_weight"],
                label=ticker, color=colour, linewidth=1.55,
            )
        axis.set_title(labels[fund_id], loc="left", fontsize=11, fontweight="bold")
        axis.yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
        axis.xaxis.set_major_locator(mdates.YearLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        _style_axis(axis)
        axis.legend(frameon=False, fontsize=7.5, ncol=2, loc="upper right")
    axes[1, 0].set_xlabel("Target effective date")
    axes[1, 1].set_xlabel("Target effective date")
    axes[0, 0].set_ylabel("Target weight")
    axes[1, 0].set_ylabel("Target weight")
    figure.suptitle("Equity target weights through time", x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
    figure.text(
        0.01, 0.93,
        "Five highest average-weight stocks within each method; other holdings remain in each fully invested fund.",
        fontsize=10.5, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_equity_weights_over_time.png",
        source_note="Source: results/data/fund_weights.csv. Monthly targets become effective on the first observed date after each decision date.",
        top=0.89,
    )


def _sentiment_figures(artifacts: app_utils.AppArtifacts) -> None:
    index = artifacts.sector_sentiment_index.loc[
        artifacts.sector_sentiment_index["sector"].eq(SENTIMENT_SECTOR)
        & artifacts.sector_sentiment_index["model"].eq(SENTIMENT_MODEL)
    ].sort_values("date", kind="mergesort")

    figure, axis = plt.subplots(figsize=(12.5, 6.4))
    axis.plot(index["date"], index["index_0_100"], color=BLUE, linewidth=1.7)
    axis.axhline(50, color=INK, linestyle="--", linewidth=1.0, label="Neutral score (50)")
    axis.set_ylim(0, 100)
    axis.set_xlabel("Mapped equity date")
    axis.set_ylabel("Finance sentiment index (0–100)")
    axis.xaxis.set_major_locator(mdates.YearLocator())
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _style_axis(axis)
    axis.legend(frameon=False, loc="upper left")
    figure.suptitle("Materials sector sentiment index", x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
    figure.text(
        0.01, 0.91,
        "Finance-extended VADER; genuine no-news sector dates remain visible as line gaps rather than neutral values.",
        fontsize=10.5, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_materials_sentiment_index.png",
        source_note="Source: results/data/sector_sentiment_index.csv. Headline → ticker-day → equal-weight observed ticker-days within sector.",
        top=0.88,
    )

    signal = pd.read_csv(DATA / "sector_sentiment_signal.csv")
    signal["effective_date"] = pd.to_datetime(signal["effective_date"])
    signal = signal.loc[
        signal["sector"].eq(SENTIMENT_SECTOR)
        & signal["model"].eq(SENTIMENT_MODEL)
    ].sort_values("effective_date", kind="mergesort")
    carried = signal["is_carried"].astype(str).str.lower().eq("true") & signal["trading_z"].notna()

    figure, axis = plt.subplots(figsize=(12.5, 6.4))
    axis.plot(signal["effective_date"], signal["trading_z"], color=NAVY, linewidth=1.55, label="Tradable causal z-score")
    axis.scatter(
        signal.loc[carried, "effective_date"],
        signal.loc[carried, "trading_z"],
        color=ORANGE,
        marker="x",
        s=34,
        linewidth=1.4,
        label="Carried signal (age 1–5)",
        zorder=3,
    )
    axis.axhline(0, color=INK, linestyle="--", linewidth=0.9)
    axis.set_xlabel("Trading effective date")
    axis.set_ylabel("Causal trading z-score")
    axis.xaxis.set_major_locator(mdates.YearLocator())
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _style_axis(axis)
    axis.legend(frameon=False, loc="upper left")
    figure.suptitle("Materials sector tradable sentiment signal", x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
    figure.text(
        0.01, 0.91,
        "One observed-equity-day lag; wholly missing sector signals may carry for five days with coverage decay.",
        fontsize=10.5, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_materials_trading_signal.png",
        source_note="Source: results/data/sector_sentiment_signal.csv. Full-sample descriptive z-scores never enter this trading signal.",
        top=0.88,
    )

    figure, axis = plt.subplots(figsize=(12.5, 5.8))
    axis.fill_between(index["date"], 0, index["coverage"], color=ORANGE, alpha=0.22)
    axis.plot(index["date"], index["coverage"], color=ORANGE, linewidth=1.45)
    axis.set_ylim(0, 1)
    axis.yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
    axis.set_xlabel("Mapped equity date")
    axis.set_ylabel("Eligible-ticker news coverage")
    axis.xaxis.set_major_locator(mdates.YearLocator())
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _style_axis(axis)
    figure.suptitle("Materials sector headline coverage", x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
    figure.text(
        0.01, 0.90,
        "Observed eligible tickers with at least one mapped headline divided by eligible sector tickers.",
        fontsize=10.5, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_materials_coverage.png",
        source_note="Source: results/data/sector_sentiment_index.csv. No supplied headline is missing coverage, not neutral sentiment.",
        top=0.86,
    )

    all_sectors = _all_sector_sentiment_input(artifacts)
    sample_start = all_sectors["date"].min().date().isoformat()
    sample_end = all_sectors["date"].max().date().isoformat()
    figure, axes = plt.subplots(
        5, 2, figsize=(12, 10.6), sharex=True, sharey=True,
    )
    for axis, sector in zip(axes.flat, EXPECTED_EQUITY_SECTORS, strict=True):
        rows = all_sectors.loc[all_sectors["sector"].eq(sector)]
        axis.plot(
            rows["date"], rows["index_0_100"], color=BLUE, linewidth=1.0,
        )
        axis.axhline(50, color=INK, linestyle="--", linewidth=0.75, alpha=0.75)
        axis.set_title(sector, loc="left", fontsize=9.5, fontweight="bold")
        axis.set_ylim(0, 100)
        axis.set_yticks([0, 50, 100])
        axis.xaxis.set_major_locator(mdates.YearLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        _style_axis(axis)
        axis.tick_params(labelsize=7.5)
    for axis in axes[:, 0]:
        axis.set_ylabel("Index (0–100)", fontsize=8)
    for axis in axes[-1, :]:
        axis.set_xlabel("Mapped equity date", fontsize=8)
    figure.suptitle(
        "All equity-sector finance sentiment indices",
        x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK,
    )
    figure.text(
        0.01, 0.94,
        f"Finance-extended VADER only · {sample_start} to {sample_end} · common 0–100 scale; gaps are missing supplied news.",
        fontsize=10.2, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_all_sector_sentiment_small_multiples.png",
        source_note="Source: results/data/sector_sentiment_index.csv. Ten equity sectors; missing compound values remain gaps and are never replaced with neutral 50.",
        top=0.90,
    )


def _all_sector_sentiment_input(
    artifacts: app_utils.AppArtifacts,
) -> pd.DataFrame:
    frame = artifacts.sector_sentiment_index.loc[
        artifacts.sector_sentiment_index["model"].eq(SENTIMENT_MODEL)
    ].copy()
    observed_sectors = set(frame["sector"].unique())
    expected_sectors = set(EXPECTED_EQUITY_SECTORS)
    if observed_sectors != expected_sectors:
        raise AssertionError(
            "all-sector report input must contain the exact ten equity sectors: "
            f"observed={sorted(observed_sectors)}"
        )
    if frame.duplicated(["date", "sector", "model"]).any():
        raise AssertionError("all-sector report input has duplicate date-sector-model keys")
    missing_compound = frame["compound_mean"].isna()
    if not frame.loc[missing_compound, "index_0_100"].isna().all():
        raise AssertionError("missing sector sentiment must remain missing, not neutral 50")
    return frame.sort_values(["sector", "date"], kind="mergesort").reset_index(drop=True)


def _fusion_weight_changes(artifacts: app_utils.AppArtifacts) -> None:
    rows = artifacts.fusion_current_holdings.copy()
    rows = rows.reindex(rows["weight_change"].abs().sort_values(ascending=False).index).head(12)
    rows = rows.sort_values("weight_change", kind="mergesort")
    colours = np.where(rows["weight_change"].ge(0), BLUE, ORANGE)
    figure, axis = plt.subplots(figsize=(11, 6.8))
    bars = axis.barh(rows["ticker"], rows["weight_change"], color=colours, edgecolor=INK, linewidth=0.4)
    axis.axvline(0, color=INK, linewidth=0.9)
    axis.xaxis.set_major_formatter(lambda value, _position: f"{value:.1%}")
    axis.set_xlabel("Augmented minus base target weight")
    axis.set_ylabel("")
    _style_axis(axis, grid_axis="x")
    limit = max(abs(axis.get_xlim()[0]), abs(axis.get_xlim()[1]))
    padded_limit = limit * 1.28
    axis.set_xlim(-padded_limit, padded_limit)
    for bar, value in zip(bars, rows["weight_change"], strict=True):
        axis.text(
            value + (padded_limit * 0.025 if value >= 0 else -padded_limit * 0.025),
            bar.get_y() + bar.get_height() / 2,
            f"{value:+.2%}",
            va="center",
            ha="left" if value >= 0 else "right",
            fontsize=8,
            color=INK,
        )
    as_of = rows["as_of_date"].max().date().isoformat()
    figure.suptitle("Largest latest sentiment-overlay target changes", x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
    figure.text(
        0.01, 0.91,
        f"Base Equity Risk Parity versus fixed augmented target, effective {as_of}; target weights, not live holdings.",
        fontsize=10.5, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_fusion_latest_weight_changes.png",
        source_note="Source: results/tables/fusion_current_holdings.csv. Positive values increase and negative values reduce the base target.",
        top=0.88,
    )


def _allocation_example(artifacts: app_utils.AppArtifacts) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = app_utils.fund_label_map(artifacts.fund_catalog)
    allocations = {fund_id: 0.25 for fund_id in REPRESENTATIVE_FUNDS}
    simulation = app_utils.simulate_allocation(
        artifacts.fund_returns,
        allocations,
        method="buy_and_hold",
        periods_per_year=252,
    )
    metrics = app_utils.calculate_annualised_metrics(
        simulation.daily["portfolio_return"], periods_per_year=252
    )
    weights = pd.DataFrame([
        {
            "fund_id": fund_id,
            "display_name": labels[fund_id],
            "illustrative_weight": weight,
        }
        for fund_id, weight in allocations.items()
    ])
    summary = pd.DataFrame([{
        "simulation": "Illustrative equal-weight four-fund allocation",
        "method": "Buy & Hold",
        "common_first_date": simulation.common_first_date,
        "common_last_date": simulation.common_last_date,
        "observations": simulation.observations,
        "periods_per_year": simulation.periods_per_year,
        "excluded_nonfinite_dates": simulation.excluded_nonfinite_dates,
        "cumulative_return": metrics["cumulative_return"],
        "annualised_return": metrics["annualised_return"],
        "annualised_volatility": metrics["annualised_volatility"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
    }])

    figure, axes = plt.subplots(2, 1, figsize=(12.5, 7.8), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(simulation.daily["date"], simulation.daily["portfolio_value"], color=NAVY, linewidth=2.2)
    axes[0].set_ylabel("Growth of $1")
    _style_axis(axes[0])
    axes[1].fill_between(simulation.daily["date"], 0, simulation.daily["drawdown"], color=RED, alpha=0.20)
    axes[1].plot(simulation.daily["date"], simulation.daily["drawdown"], color=RED, linewidth=1.3)
    axes[1].axhline(0, color=INK, linewidth=0.8)
    axes[1].yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
    axes[1].set_ylabel("Drawdown")
    axes[1].set_xlabel("Common OOS date")
    axes[1].xaxis.set_major_locator(mdates.YearLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _style_axis(axes[1])
    figure.suptitle("Illustrative equal-weight fund allocation", x=0.01, ha="left", fontsize=18, fontweight="bold", color=INK)
    figure.text(
        0.01, 0.925,
        "25% each in Equity RP, Crypto RP, Combined RP, and Equity RP + Sentiment; Buy & Hold using committed fund net returns.",
        fontsize=10.5, color=MUTED,
    )
    _finish_figure(
        figure,
        FIGURES / "report_allocation_example.png",
        source_note="Source: results/data/fund_returns.csv via src/app_utils.py. Illustrative simulation only; no optimisation, recommendation, extra fee, tax, or cross-fund trading cost.",
        top=0.89,
    )
    return weights, summary


def _exhibit_catalog() -> pd.DataFrame:
    rows: Iterable[dict[str, str]] = [
        {"artifact": "results/figures/report_fund_return_volatility.png", "report_section": "Fund comparison", "question": "How do the 13 funds compare on net annualised return and volatility?", "chart_type": "Scatter", "source": "performance_metrics.csv; fund_catalog.csv", "supported_claim": "Risk and return differ materially across universes; no chart point establishes a universally best fund."},
        {"artifact": "results/figures/report_selected_growth.png", "report_section": "Fund comparison", "question": "How did representative Risk Parity funds compound?", "chart_type": "Multi-series line", "source": "fund_returns.csv", "supported_claim": "Representative funds followed materially different compounded paths."},
        {"artifact": "results/figures/report_selected_drawdown.png", "report_section": "Fund comparison", "question": "How severe were representative fund drawdowns?", "chart_type": "Multi-series line", "source": "fund_returns.csv", "supported_claim": "Crypto Risk Parity carried substantially deeper drawdown risk."},
        {"artifact": "results/figures/report_equity_weights_over_time.png", "report_section": "Portfolio construction", "question": "How did monthly Equity targets change across methods?", "chart_type": "Small-multiple line", "source": "fund_weights.csv", "supported_claim": "Methods produced distinct, time-varying target allocations."},
        {"artifact": "results/figures/report_materials_sentiment_index.png", "report_section": "Sentiment evidence", "question": "What does a coverage-aware sector sentiment history look like?", "chart_type": "Gap-preserving line", "source": "sector_sentiment_index.csv", "supported_claim": "Missing news remains visible rather than being replaced with a neutral score."},
        {"artifact": "results/figures/report_materials_trading_signal.png", "report_section": "Sentiment evidence", "question": "What signal is available for trading after lag and carry?", "chart_type": "Line with carry markers", "source": "sector_sentiment_signal.csv", "supported_claim": "The tradable signal is causal, lagged, and subject to bounded carry."},
        {"artifact": "results/figures/report_materials_coverage.png", "report_section": "Sentiment evidence", "question": "How complete is sector headline coverage?", "chart_type": "Area and line", "source": "sector_sentiment_index.csv", "supported_claim": "Coverage varies materially over time and qualifies the sentiment index."},
        {"artifact": "results/figures/report_all_sector_sentiment_small_multiples.png", "report_section": "Appendix — sentiment evidence", "question": "Does the standalone finance-sentiment index cover every equity sector?", "chart_type": "Gap-preserving line small multiples", "source": "sector_sentiment_index.csv", "supported_claim": "The finance-VADER index covers all ten equity sectors while genuine missing dates remain visible as gaps."},
        {"artifact": "results/figures/fusion_growth_of_one.png", "report_section": "Fusion evidence", "question": "Did the fixed overlay improve compounded performance?", "chart_type": "Multi-series line", "source": "fund_returns.csv; fusion_comparison.csv", "supported_claim": "The augmented fund ended below the base fund in this OOS sample."},
        {"artifact": "results/figures/fusion_drawdown.png", "report_section": "Fusion evidence", "question": "Did the fixed overlay improve drawdown?", "chart_type": "Multi-series line", "source": "fund_returns.csv; fusion_comparison.csv", "supported_claim": "The augmented net maximum drawdown was slightly deeper."},
        {"artifact": "results/figures/fusion_sector_multiplier_activity.png", "report_section": "Fusion evidence", "question": "When and where did the fixed overlay alter sector exposure?", "chart_type": "Time-series marker plot", "source": "fusion_sector_multipliers.csv", "supported_claim": "The bounded rule generated active and neutral multipliers without retuning."},
        {"artifact": "results/figures/report_fusion_latest_weight_changes.png", "report_section": "Fusion evidence", "question": "Which latest targets changed most?", "chart_type": "Diverging horizontal bar", "source": "fusion_current_holdings.csv", "supported_claim": "The latest overlay changes are modest stock-level reallocations."},
        {"artifact": "results/figures/report_allocation_example.png", "report_section": "Investor app", "question": "How does an illustrative fund allocation compound on a common OOS period?", "chart_type": "Growth and drawdown panels", "source": "fund_returns.csv via app_utils.py", "supported_claim": "The app can simulate, but does not optimise or recommend, a fund allocation."},
    ]
    return pd.DataFrame(rows)


def validate_report_outputs() -> None:
    missing = [
        str(path.relative_to(ROOT))
        for path in [
            *(FIGURES / name for name in REPORT_FIGURES),
            *(TABLES / name for name in REPORT_TABLES),
        ]
        if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise AssertionError(f"missing or empty report artifact(s): {missing}")
    summary = pd.read_csv(TABLES / "report_fund_summary.csv")
    if len(summary) != 13 or set(summary["fund_id"]) != app_utils.EXPECTED_FUND_IDS:
        raise AssertionError("report fund summary must contain the exact 13 funds")
    allocation = pd.read_csv(TABLES / "report_allocation_example_weights.csv")
    if not np.isclose(allocation["illustrative_weight"].sum(), 1.0, atol=1e-12):
        raise AssertionError("illustrative allocation weights must sum to one")


def main() -> None:
    artifacts = app_utils.load_app_artifacts(ROOT)
    summary = _build_fund_summary(artifacts)
    _write_csv(summary, TABLES / "report_fund_summary.csv")
    _fund_scatter(summary)
    _selected_return_figures(artifacts)
    _equity_weight_history(artifacts)
    _sentiment_figures(artifacts)
    _fusion_weight_changes(artifacts)
    allocation_weights, allocation_metrics = _allocation_example(artifacts)
    _write_csv(allocation_weights, TABLES / "report_allocation_example_weights.csv")
    _write_csv(allocation_metrics, TABLES / "report_allocation_example_metrics.csv")
    _write_csv(_exhibit_catalog(), TABLES / "report_exhibit_catalog.csv")
    validate_report_outputs()
    print(f"report figures: {len(REPORT_FIGURES)}")
    print(f"report tables: {len(REPORT_TABLES)}")
    print("representative funds: " + ", ".join(REPRESENTATIVE_FUNDS))
    print(f"sentiment example: sector={SENTIMENT_SECTOR}, model={SENTIMENT_MODEL}")


if __name__ == "__main__":
    main()
