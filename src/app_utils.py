"""Pure loading, validation, filtering, and allocation utilities for the app.

This module reads committed artifacts only.  It has no Streamlit dependency and
does not import or execute the analytical data, portfolio, sentiment, or fusion
engines.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd


FUND_RETURN_COLUMNS = [
    "date", "fund_id", "universe", "method", "periods_per_year",
    "gross_return", "turnover", "trading_cost", "net_return",
    "growth_gross", "growth_net", "drawdown_gross", "drawdown_net",
    "is_rebalance",
]
FUND_WEIGHT_COLUMNS = [
    "decision_date", "effective_date", "fund_id", "universe", "method",
    "ticker", "target_weight", "pretrade_weight", "asset_cap",
    "eligible_asset_count", "solver_success", "fallback_used",
]
PERFORMANCE_COLUMNS = [
    "fund_id", "universe", "method", "first_live_date", "last_date",
    "observations", "periods_per_year", "cumulative_return_gross",
    "annualised_return_gross", "annualised_volatility_gross", "sharpe_gross",
    "max_drawdown_gross", "cumulative_return_net", "annualised_return_net",
    "annualised_volatility_net", "sharpe_net", "max_drawdown_net",
    "total_turnover", "average_rebalance_turnover", "total_trading_cost",
    "rebalance_count", "fallback_count",
]
FUND_CATALOG_COLUMNS = [
    "fund_id", "display_name", "universe", "method", "short_description",
    "first_live_date", "last_date", "periods_per_year",
    "is_sentiment_augmented", "base_fund_id",
]
FUND_CURRENT_HOLDINGS_COLUMNS = [
    "fund_id", "as_of_date", "ticker", "asset_class", "target_weight",
    "holding_rank",
]
SECTOR_SENTIMENT_COLUMNS = [
    "date", "sector", "model", "headline_count", "observed_ticker_count",
    "eligible_ticker_count", "coverage", "compound_mean", "index_0_100",
    "causal_expanding_mean", "causal_expanding_std", "causal_z",
    "descriptive_full_sample_z",
]
FUSION_COMPARISON_COLUMNS = [
    "fund_id", "role", "common_first_date", "common_last_date", "observations",
    "cumulative_return_gross", "cumulative_return_net",
    "annualised_return_gross", "annualised_return_net",
    "annualised_volatility_gross", "annualised_volatility_net",
    "sharpe_gross", "sharpe_net", "max_drawdown_gross", "max_drawdown_net",
    "total_turnover", "average_rebalance_turnover", "total_trading_cost",
    "rebalance_count", "tracking_error_versus_base", "correlation_with_base",
    "delta_observations", "delta_cumulative_return_gross",
    "delta_cumulative_return_net", "delta_annualised_return_gross",
    "delta_annualised_return_net", "delta_annualised_volatility_gross",
    "delta_annualised_volatility_net", "delta_sharpe_gross",
    "delta_sharpe_net", "delta_max_drawdown_gross",
    "delta_max_drawdown_net", "delta_total_turnover",
    "delta_average_rebalance_turnover", "delta_total_trading_cost",
    "delta_rebalance_count",
]
FUSION_CURRENT_HOLDINGS_COLUMNS = [
    "as_of_date", "ticker", "sector", "base_weight", "augmented_weight",
    "weight_change", "latest_signal_source_date", "latest_signal_age",
    "latest_trading_z", "latest_effective_coverage", "latest_multiplier",
]
FUSION_MULTIPLIER_COLUMNS = [
    "decision_date", "effective_date", "sector", "model", "source_date",
    "signal_age", "trading_z", "effective_coverage", "z_bounded",
    "multiplier", "has_active_signal",
]

EXPECTED_FUND_IDS = {
    "combined_equal_weight", "combined_max_sharpe", "combined_min_variance",
    "combined_risk_parity", "crypto_equal_weight", "crypto_max_sharpe",
    "crypto_min_variance", "crypto_risk_parity", "equity_equal_weight",
    "equity_max_sharpe", "equity_min_variance", "equity_risk_parity",
    "equity_risk_parity_sentiment",
}

DISPLAY_NAMES = {
    "combined_equal_weight": "Combined — Equal Weight",
    "combined_max_sharpe": "Combined — Maximum Sharpe",
    "combined_min_variance": "Combined — Minimum Variance",
    "combined_risk_parity": "Combined — Risk Parity",
    "crypto_equal_weight": "Crypto — Equal Weight",
    "crypto_max_sharpe": "Crypto — Maximum Sharpe",
    "crypto_min_variance": "Crypto — Minimum Variance",
    "crypto_risk_parity": "Crypto — Risk Parity",
    "equity_equal_weight": "Equity — Equal Weight",
    "equity_max_sharpe": "Equity — Maximum Sharpe",
    "equity_min_variance": "Equity — Minimum Variance",
    "equity_risk_parity": "Equity — Risk Parity",
    "equity_risk_parity_sentiment": "Equity — Risk Parity + Sentiment",
}

SHORT_DESCRIPTIONS = {
    "equal_weight": "Capped benchmark that distributes capital evenly across eligible assets.",
    "max_sharpe": "Walk-forward long-only target that maximises estimated return per unit of risk.",
    "minimum_variance": "Walk-forward long-only target that minimises estimated portfolio variance.",
    "risk_parity": "Walk-forward long-only target that balances percentage risk contributions.",
    "risk_parity_sentiment": "Fixed coverage-aware finance-sentiment overlay on Equity Risk Parity.",
}


class ArtifactError(ValueError):
    """Actionable error for missing, malformed, or inconsistent app artifacts."""


@dataclass(frozen=True)
class AppArtifacts:
    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    performance_metrics: pd.DataFrame
    fund_catalog: pd.DataFrame
    fund_current_holdings: pd.DataFrame
    sector_sentiment_index: pd.DataFrame
    fusion_comparison: pd.DataFrame
    fusion_current_holdings: pd.DataFrame
    fusion_sector_multipliers: pd.DataFrame


@dataclass(frozen=True)
class AllocationResult:
    daily: pd.DataFrame
    common_first_date: pd.Timestamp
    common_last_date: pd.Timestamp
    observations: int
    periods_per_year: int
    excluded_nonfinite_dates: int
    rebalance_dates: tuple[pd.Timestamp, ...]


def validate_schema(
    frame: pd.DataFrame,
    expected_columns: Iterable[str],
    *,
    label: str,
    unique_key: Iterable[str] | None = None,
) -> None:
    """Validate exact column order and, when supplied, a unique non-missing key."""
    expected = list(expected_columns)
    if frame.columns.tolist() != expected:
        raise ArtifactError(
            f"{label} has the wrong schema. Expected {expected}; "
            f"found {frame.columns.tolist()}. Re-run scripts/run_part_b.py."
        )
    if unique_key is not None:
        key = list(unique_key)
        if frame[key].isna().any().any():
            raise ArtifactError(f"{label} has a missing value in unique key {key}.")
        if frame.duplicated(key).any():
            raise ArtifactError(f"{label} has duplicate rows for unique key {key}.")


def _results_root(root: str | Path) -> Path:
    supplied = Path(root).expanduser().resolve()
    return supplied if supplied.name == "results" else supplied / "results"


def _read_csv(
    results_root: Path,
    relative_path: str,
    columns: list[str],
    *,
    unique_key: list[str],
    date_columns: Iterable[str] = (),
) -> pd.DataFrame:
    path = results_root / relative_path
    if not path.is_file():
        raise ArtifactError(
            f"Missing app artifact: {path}. Run `python scripts/run_part_b.py` "
            "and commit the generated results before opening the app."
        )
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise ArtifactError(f"Could not read {path}: {exc}") from exc
    validate_schema(frame, columns, label=relative_path, unique_key=unique_key)
    for column in date_columns:
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return frame


def load_app_artifacts(root: str | Path) -> AppArtifacts:
    """Load and validate every committed artifact used by the Streamlit app."""
    results = _results_root(root)
    artifacts = AppArtifacts(
        fund_returns=_read_csv(
            results, "data/fund_returns.csv", FUND_RETURN_COLUMNS,
            unique_key=["date", "fund_id"], date_columns=["date"],
        ),
        fund_weights=_read_csv(
            results, "data/fund_weights.csv", FUND_WEIGHT_COLUMNS,
            unique_key=["effective_date", "fund_id", "ticker"],
            date_columns=["decision_date", "effective_date"],
        ),
        performance_metrics=_read_csv(
            results, "tables/performance_metrics.csv", PERFORMANCE_COLUMNS,
            unique_key=["fund_id"], date_columns=["first_live_date", "last_date"],
        ),
        fund_catalog=_read_csv(
            results, "data/fund_catalog.csv", FUND_CATALOG_COLUMNS,
            unique_key=["fund_id"], date_columns=["first_live_date", "last_date"],
        ),
        fund_current_holdings=_read_csv(
            results, "data/fund_current_holdings.csv", FUND_CURRENT_HOLDINGS_COLUMNS,
            unique_key=["fund_id", "ticker"], date_columns=["as_of_date"],
        ),
        sector_sentiment_index=_read_csv(
            results, "data/sector_sentiment_index.csv", SECTOR_SENTIMENT_COLUMNS,
            unique_key=["date", "sector", "model"], date_columns=["date"],
        ),
        fusion_comparison=_read_csv(
            results, "tables/fusion_comparison.csv", FUSION_COMPARISON_COLUMNS,
            unique_key=["fund_id"],
            date_columns=["common_first_date", "common_last_date"],
        ),
        fusion_current_holdings=_read_csv(
            results, "tables/fusion_current_holdings.csv",
            FUSION_CURRENT_HOLDINGS_COLUMNS, unique_key=["ticker"],
            date_columns=["as_of_date", "latest_signal_source_date"],
        ),
        fusion_sector_multipliers=_read_csv(
            results, "data/fusion_sector_multipliers.csv", FUSION_MULTIPLIER_COLUMNS,
            unique_key=["effective_date", "sector"],
            date_columns=["decision_date", "effective_date", "source_date"],
        ),
    )
    if set(artifacts.fund_catalog["fund_id"]) != EXPECTED_FUND_IDS:
        raise ArtifactError("fund_catalog.csv must contain the exact 13 approved fund IDs.")
    for label, frame in (
        ("fund_returns.csv", artifacts.fund_returns),
        ("performance_metrics.csv", artifacts.performance_metrics),
        ("fund_current_holdings.csv", artifacts.fund_current_holdings),
    ):
        if set(frame["fund_id"]) != EXPECTED_FUND_IDS:
            raise ArtifactError(f"{label} does not contain the exact 13 approved fund IDs.")
    sums = artifacts.fund_current_holdings.groupby("fund_id")["target_weight"].sum()
    if not np.allclose(sums.to_numpy(), 1.0, atol=1e-8, rtol=0.0):
        raise ArtifactError("latest target holdings do not sum to one for every fund.")
    return artifacts


def build_fund_catalog(performance_metrics: pd.DataFrame) -> pd.DataFrame:
    """Build the deterministic 13-fund investor-facing catalogue."""
    validate_schema(performance_metrics, PERFORMANCE_COLUMNS, label="performance metrics", unique_key=["fund_id"])
    if set(performance_metrics["fund_id"]) != EXPECTED_FUND_IDS:
        raise ArtifactError("performance metrics must contain the exact 13 approved fund IDs.")
    rows = []
    for row in performance_metrics.sort_values("fund_id", kind="mergesort").itertuples(index=False):
        augmented = row.fund_id == "equity_risk_parity_sentiment"
        rows.append({
            "fund_id": row.fund_id,
            "display_name": DISPLAY_NAMES[row.fund_id],
            "universe": row.universe,
            "method": row.method,
            "short_description": SHORT_DESCRIPTIONS[row.method],
            "first_live_date": pd.Timestamp(row.first_live_date),
            "last_date": pd.Timestamp(row.last_date),
            "periods_per_year": int(row.periods_per_year),
            "is_sentiment_augmented": augmented,
            "base_fund_id": "equity_risk_parity" if augmented else "",
        })
    return pd.DataFrame(rows, columns=FUND_CATALOG_COLUMNS)


def build_fund_current_holdings(
    fund_weights: pd.DataFrame,
    fund_catalog: pd.DataFrame,
) -> pd.DataFrame:
    """Build one latest target-weight snapshot for each approved fund."""
    validate_schema(fund_weights, FUND_WEIGHT_COLUMNS, label="fund weights", unique_key=["effective_date", "fund_id", "ticker"])
    validate_schema(fund_catalog, FUND_CATALOG_COLUMNS, label="fund catalog", unique_key=["fund_id"])
    weights = fund_weights.copy()
    weights["effective_date"] = pd.to_datetime(weights["effective_date"])
    latest_date = weights.groupby("fund_id")["effective_date"].transform("max")
    latest = weights.loc[
        weights["effective_date"].eq(latest_date),
        ["fund_id", "effective_date", "ticker", "target_weight"],
    ].copy()
    universes = fund_catalog.set_index("fund_id")["universe"]
    latest["asset_class"] = latest["fund_id"].map(universes)
    combined = latest["asset_class"].eq("combined")
    latest.loc[combined, "asset_class"] = np.where(
        latest.loc[combined, "ticker"].str.endswith("-USD"), "crypto", "equity"
    )
    latest = latest.rename(columns={"effective_date": "as_of_date"})
    latest = latest.sort_values(
        ["fund_id", "target_weight", "ticker"],
        ascending=[True, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    latest["holding_rank"] = latest.groupby("fund_id").cumcount() + 1
    output = latest[FUND_CURRENT_HOLDINGS_COLUMNS]
    if set(output["fund_id"]) != EXPECTED_FUND_IDS:
        raise ArtifactError("latest holdings do not contain the exact 13 approved fund IDs.")
    sums = output.groupby("fund_id")["target_weight"].sum()
    if not np.allclose(sums.to_numpy(), 1.0, atol=1e-8, rtol=0.0):
        raise ArtifactError("latest target weights do not sum to one for every fund.")
    return output


def fund_label_map(fund_catalog: pd.DataFrame) -> dict[str, str]:
    validate_schema(fund_catalog, FUND_CATALOG_COLUMNS, label="fund catalog", unique_key=["fund_id"])
    return dict(zip(fund_catalog["fund_id"], fund_catalog["display_name"], strict=True))


def filter_fund_comparison(
    fund_catalog: pd.DataFrame,
    performance_metrics: pd.DataFrame,
    *,
    categories: Iterable[str] | None = None,
    basis: str = "net",
) -> pd.DataFrame:
    """Return a labelled, filterable fund comparison table for net or gross results."""
    if basis not in {"net", "gross"}:
        raise ValueError("basis must be 'net' or 'gross'")
    catalog = fund_catalog.copy()
    metrics = performance_metrics.copy()
    validate_schema(catalog, FUND_CATALOG_COLUMNS, label="fund catalog", unique_key=["fund_id"])
    validate_schema(metrics, PERFORMANCE_COLUMNS, label="performance metrics", unique_key=["fund_id"])
    metric_values = metrics.drop(columns=["first_live_date", "last_date"])
    merged = catalog.merge(
        metric_values,
        on=["fund_id", "universe", "method", "periods_per_year"],
        validate="one_to_one",
    )
    chosen = set(categories or [])
    if chosen:
        mask = merged["universe"].str.title().isin(chosen)
        if "Sentiment-Augmented" in chosen:
            mask |= merged["is_sentiment_augmented"]
        merged = merged.loc[mask]
    columns = [
        "fund_id", "display_name", "universe", "method", "first_live_date",
        "last_date", "periods_per_year", f"cumulative_return_{basis}",
        f"annualised_return_{basis}", f"annualised_volatility_{basis}",
        f"sharpe_{basis}", f"max_drawdown_{basis}", "total_turnover",
        "total_trading_cost", "rebalance_count", "fallback_count",
    ]
    return merged[columns].sort_values("display_name", kind="mergesort").reset_index(drop=True)


def common_return_panel(
    fund_returns: pd.DataFrame,
    fund_ids: Iterable[str],
    *,
    return_column: str = "net_return",
) -> pd.DataFrame:
    """Return only intersecting dates with finite selected-fund returns; never fill."""
    if return_column not in {"net_return", "gross_return"}:
        raise ValueError("return_column must be net_return or gross_return")
    selected = list(dict.fromkeys(fund_ids))
    if not selected:
        raise ValueError("select at least one fund")
    available = set(fund_returns["fund_id"])
    missing = sorted(set(selected).difference(available))
    if missing:
        raise ValueError(f"unknown selected fund IDs: {missing}")
    subset = fund_returns.loc[
        fund_returns["fund_id"].isin(selected), ["date", "fund_id", return_column]
    ].copy()
    subset["date"] = pd.to_datetime(subset["date"])
    if subset.duplicated(["date", "fund_id"]).any():
        raise ArtifactError("selected fund returns contain duplicate date-fund rows")
    date_sets = [
        set(group["date"])
        for _fund_id, group in subset.groupby("fund_id", sort=False)
    ]
    common_dates = set.intersection(*date_sets)
    subset = subset.loc[subset["date"].isin(common_dates)]
    panel = subset.pivot(index="date", columns="fund_id", values=return_column)
    panel = panel.reindex(columns=selected).sort_index()
    finite = pd.DataFrame(np.isfinite(panel.to_numpy(dtype=float)), index=panel.index, columns=panel.columns)
    valid_rows = panel.notna().all(axis=1) & finite.all(axis=1)
    output = panel.loc[valid_rows].copy()
    output.attrs["excluded_nonfinite_dates"] = int((~valid_rows).sum())
    if output.empty:
        raise ValueError("selected funds have no common finite OOS return dates")
    return output


def common_oos_period(fund_returns: pd.DataFrame, fund_ids: Iterable[str]) -> dict[str, object]:
    panel = common_return_panel(fund_returns, fund_ids, return_column="net_return")
    return {
        "first_date": pd.Timestamp(panel.index.min()),
        "last_date": pd.Timestamp(panel.index.max()),
        "observations": int(len(panel)),
        "excluded_nonfinite_dates": int(panel.attrs["excluded_nonfinite_dates"]),
    }


def validate_allocations(
    allocations: Mapping[str, float] | pd.Series,
    *,
    minimum_funds: int = 2,
    maximum_funds: int = 6,
) -> pd.Series:
    """Return deterministic decimal weights after non-negative and sum checks."""
    weights = pd.Series(dict(allocations), dtype=float)
    if not minimum_funds <= len(weights) <= maximum_funds:
        raise ValueError(f"select between {minimum_funds} and {maximum_funds} funds")
    if weights.index.duplicated().any() or not np.isfinite(weights.to_numpy()).all():
        raise ValueError("allocations must have unique funds and finite values")
    if (weights < 0.0).any():
        raise ValueError("allocations must be non-negative")
    if not np.isclose(float(weights.sum()), 1.0, atol=1e-8, rtol=0.0):
        raise ValueError(f"allocations must sum to 100%; current total is {weights.sum() * 100:.4f}%")
    return weights


def calculate_growth_drawdown(returns: pd.Series) -> pd.DataFrame:
    """Calculate uncompensated growth of one and drawdown without filling gaps."""
    series = pd.Series(returns, dtype=float)
    if series.isna().any() or not np.isfinite(series.to_numpy()).all():
        raise ValueError("portfolio returns must be finite; missing values are not filled")
    growth = (1.0 + series).cumprod()
    return pd.DataFrame({"growth": growth, "drawdown": growth / growth.cummax() - 1.0})


def calculate_annualised_metrics(
    returns: pd.Series,
    *,
    periods_per_year: int,
) -> dict[str, float | int]:
    """Use the project's arithmetic annualisation and compounded return conventions."""
    series = pd.Series(returns, dtype=float)
    if series.empty or series.isna().any() or not np.isfinite(series.to_numpy()).all():
        raise ValueError("metric returns must be non-empty and finite")
    growth = calculate_growth_drawdown(series)
    annualised_return = float(series.mean() * periods_per_year)
    annualised_volatility = float(series.std(ddof=1) * np.sqrt(periods_per_year))
    sharpe = annualised_return / annualised_volatility if annualised_volatility > 0 else np.nan
    return {
        "observations": int(len(series)),
        "cumulative_return": float(growth["growth"].iloc[-1] - 1.0),
        "annualised_return": annualised_return,
        "annualised_volatility": annualised_volatility,
        "sharpe": float(sharpe),
        "max_drawdown": float(growth["drawdown"].min()),
    }


def allocation_periods_per_year(fund_catalog: pd.DataFrame, fund_ids: Iterable[str]) -> int:
    """Use 365 only for an all-crypto selection; otherwise the common calendar is 252."""
    selected = fund_catalog.loc[fund_catalog["fund_id"].isin(fund_ids)]
    if len(selected) != len(set(fund_ids)):
        raise ValueError("selected allocation contains an unknown fund")
    return 365 if selected["periods_per_year"].eq(365).all() else 252


def simulate_allocation(
    fund_returns: pd.DataFrame,
    allocations: Mapping[str, float] | pd.Series,
    *,
    method: str,
    periods_per_year: int,
) -> AllocationResult:
    """Simulate buy-and-hold sleeves or monthly target resets using net returns only."""
    weights = validate_allocations(allocations)
    panel = common_return_panel(fund_returns, weights.index, return_column="net_return")
    if method not in {"buy_and_hold", "monthly_reset"}:
        raise ValueError("method must be buy_and_hold or monthly_reset")
    sleeve_values = weights.copy()
    previous_total = 1.0
    rows = []
    rebalance_dates: list[pd.Timestamp] = []
    previous_month = None
    for position, (date, daily_returns) in enumerate(panel.iterrows()):
        month = pd.Timestamp(date).to_period("M")
        reset = method == "monthly_reset" and (position == 0 or month != previous_month)
        if reset:
            sleeve_values = weights * previous_total
            rebalance_dates.append(pd.Timestamp(date))
        sleeve_values = sleeve_values * (1.0 + daily_returns.reindex(weights.index))
        total = float(sleeve_values.sum())
        portfolio_return = total / previous_total - 1.0
        rows.append({
            "date": pd.Timestamp(date),
            "portfolio_return": portfolio_return,
            "portfolio_value": total,
            "is_rebalance": reset,
        })
        previous_total = total
        previous_month = month
    daily = pd.DataFrame(rows)
    derived = calculate_growth_drawdown(daily["portfolio_return"])
    if not np.allclose(daily["portfolio_value"], derived["growth"], atol=1e-12, rtol=0.0):
        raise AssertionError("allocation sleeve values do not reconcile to compounded returns")
    daily["drawdown"] = derived["drawdown"].to_numpy()
    return AllocationResult(
        daily=daily,
        common_first_date=pd.Timestamp(panel.index.min()),
        common_last_date=pd.Timestamp(panel.index.max()),
        observations=int(len(panel)),
        periods_per_year=int(periods_per_year),
        excluded_nonfinite_dates=int(panel.attrs["excluded_nonfinite_dates"]),
        rebalance_dates=tuple(rebalance_dates),
    )


def latest_target_holdings(current_holdings: pd.DataFrame, fund_id: str) -> pd.DataFrame:
    output = current_holdings.loc[current_holdings["fund_id"].eq(fund_id)].copy()
    if output.empty:
        raise ValueError(f"no latest target holdings for {fund_id}")
    return output.sort_values(["holding_rank", "ticker"], kind="mergesort").reset_index(drop=True)


def selected_fund_weight_history(
    fund_weights: pd.DataFrame,
    fund_id: str,
    *,
    tickers: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Return selected target-weight history at rebalance dates without filling."""
    subset = fund_weights.loc[fund_weights["fund_id"].eq(fund_id)].copy()
    if tickers is not None:
        subset = subset.loc[subset["ticker"].isin(list(tickers))]
    if subset.empty:
        raise ValueError(f"no target-weight history for {fund_id}")
    return subset[["effective_date", "ticker", "target_weight"]].sort_values(
        ["effective_date", "ticker"], kind="mergesort"
    ).reset_index(drop=True)


def filter_sentiment_time_series(
    sector_sentiment: pd.DataFrame,
    *,
    sector: str,
    model: str,
) -> pd.DataFrame:
    """Filter a sector/model history while preserving genuine missing rows."""
    subset = sector_sentiment.loc[
        sector_sentiment["sector"].eq(sector) & sector_sentiment["model"].eq(model)
    ].copy()
    if subset.empty:
        raise ValueError(f"no sentiment series for sector={sector}, model={model}")
    return subset.sort_values("date", kind="mergesort").reset_index(drop=True)


def latest_sector_sentiment_snapshot(
    sector_sentiment: pd.DataFrame,
    *,
    model: str,
) -> pd.DataFrame:
    """Return every sector on the latest supplied index date without carrying values."""
    subset = sector_sentiment.loc[sector_sentiment["model"].eq(model)].copy()
    if subset.empty:
        raise ValueError(f"no sentiment rows for model={model}")
    latest = pd.to_datetime(subset["date"]).max()
    output = subset.loc[pd.to_datetime(subset["date"]).eq(latest), [
        "date", "sector", "headline_count", "observed_ticker_count",
        "eligible_ticker_count", "coverage", "index_0_100", "causal_z",
    ]]
    return output.sort_values("sector", kind="mergesort").reset_index(drop=True)


def base_vs_augmented_fusion_summary(fusion_comparison: pd.DataFrame) -> dict[str, object]:
    """Validate the common comparison and derive a neutral sample-specific summary."""
    validate_schema(
        fusion_comparison, FUSION_COMPARISON_COLUMNS,
        label="fusion comparison", unique_key=["fund_id"],
    )
    if set(fusion_comparison["role"]) != {"base", "augmented"}:
        raise ArtifactError("fusion comparison must contain one base and one augmented row")
    if fusion_comparison["common_first_date"].nunique() != 1 or fusion_comparison["common_last_date"].nunique() != 1:
        raise ArtifactError("fusion comparison does not use identical dates")
    if fusion_comparison["observations"].nunique() != 1:
        raise ArtifactError("fusion comparison does not use identical observation counts")
    base = fusion_comparison.loc[fusion_comparison["role"].eq("base")].iloc[0]
    augmented = fusion_comparison.loc[fusion_comparison["role"].eq("augmented")].iloc[0]
    net_delta = float(augmented["cumulative_return_net"] - base["cumulative_return_net"])
    turnover_delta = float(augmented["total_turnover"] - base["total_turnover"])
    if net_delta < 0.0 and turnover_delta > 0.0:
        text = (
            "The fixed sentiment overlay underperformed base Equity Risk Parity "
            "in this OOS sample and had higher turnover. It was not retuned."
        )
    else:
        text = (
            "The fixed overlay and base are shown as descriptive OOS evidence. "
            "The overlay was not retuned after observing the result."
        )
    return {
        "common_first_date": pd.Timestamp(base["common_first_date"]),
        "common_last_date": pd.Timestamp(base["common_last_date"]),
        "observations": int(base["observations"]),
        "net_cumulative_return_delta": net_delta,
        "turnover_delta": turnover_delta,
        "tracking_error_versus_base": float(augmented["tracking_error_versus_base"]),
        "correlation_with_base": float(augmented["correlation_with_base"]),
        "summary_text": text,
    }
