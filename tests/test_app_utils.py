"""Synthetic tests for app artifact builders and allocation utilities."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import app_utils


def _performance_metrics() -> pd.DataFrame:
    rows = []
    for fund_id in sorted(app_utils.EXPECTED_FUND_IDS):
        universe = fund_id.split("_", 1)[0]
        if fund_id.endswith("risk_parity_sentiment"):
            method = "risk_parity_sentiment"
        elif fund_id.endswith("equal_weight"):
            method = "equal_weight"
        elif fund_id.endswith("min_variance"):
            method = "minimum_variance"
        elif fund_id.endswith("max_sharpe"):
            method = "max_sharpe"
        else:
            method = "risk_parity"
        row = {column: 0 for column in app_utils.PERFORMANCE_COLUMNS}
        row.update({
            "fund_id": fund_id,
            "universe": universe,
            "method": method,
            "first_live_date": pd.Timestamp("2021-01-01"),
            "last_date": pd.Timestamp("2023-12-29"),
            "observations": 10,
            "periods_per_year": 365 if universe == "crypto" else 252,
        })
        rows.append(row)
    return pd.DataFrame(rows, columns=app_utils.PERFORMANCE_COLUMNS)


def _fund_returns(*, missing: bool = False) -> pd.DataFrame:
    dates = pd.to_datetime(["2023-01-31", "2023-02-01", "2023-02-02", "2023-03-01"])
    values = {
        "fund_a": [0.10, 0.00, 0.02, 0.01],
        "fund_b": [0.00, 0.10, -0.01, 0.02],
    }
    if missing:
        values["fund_b"][1] = np.nan
    rows = []
    for fund_id, returns in values.items():
        for date, value in zip(dates, returns, strict=True):
            rows.append({"date": date, "fund_id": fund_id, "net_return": value, "gross_return": value})
    return pd.DataFrame(rows)


def _fusion_comparison(*, mismatched_dates: bool = False) -> pd.DataFrame:
    rows = []
    for role, fund_id in (
        ("base", "equity_risk_parity"),
        ("augmented", "equity_risk_parity_sentiment"),
    ):
        row = {column: 0.0 for column in app_utils.FUSION_COMPARISON_COLUMNS}
        row.update({
            "fund_id": fund_id,
            "role": role,
            "common_first_date": pd.Timestamp("2021-01-04"),
            "common_last_date": pd.Timestamp("2023-12-29"),
            "observations": 753,
            "cumulative_return_net": 0.33 if role == "base" else 0.31,
            "total_turnover": 1.9 if role == "base" else 2.4,
            "tracking_error_versus_base": 0.0 if role == "base" else 0.003,
            "correlation_with_base": 1.0 if role == "base" else 0.999,
        })
        if mismatched_dates and role == "augmented":
            row["common_last_date"] = pd.Timestamp("2023-12-28")
        rows.append(row)
    return pd.DataFrame(rows, columns=app_utils.FUSION_COMPARISON_COLUMNS)


def test_exact_schema_validation_rejects_wrong_order_and_duplicate_key() -> None:
    correct = pd.DataFrame({"a": [1], "b": [2]})
    app_utils.validate_schema(correct, ["a", "b"], label="test", unique_key=["a"])
    with pytest.raises(app_utils.ArtifactError, match="wrong schema"):
        app_utils.validate_schema(correct[["b", "a"]], ["a", "b"], label="test")
    duplicate = pd.DataFrame({"a": [1, 1], "b": [2, 3]})
    with pytest.raises(app_utils.ArtifactError, match="duplicate"):
        app_utils.validate_schema(duplicate, ["a", "b"], label="test", unique_key=["a"])


def test_catalogue_contains_exact_13_ids_names_and_augmented_base() -> None:
    catalog = app_utils.build_fund_catalog(_performance_metrics())
    assert catalog.columns.tolist() == app_utils.FUND_CATALOG_COLUMNS
    assert set(catalog["fund_id"]) == app_utils.EXPECTED_FUND_IDS
    assert catalog["display_name"].nunique() == 13
    augmented = catalog.loc[catalog["is_sentiment_augmented"]].iloc[0]
    assert augmented["fund_id"] == "equity_risk_parity_sentiment"
    assert augmented["base_fund_id"] == "equity_risk_parity"


def test_filtered_comparison_preserves_catalogue_oos_dates() -> None:
    metrics = _performance_metrics()
    catalog = app_utils.build_fund_catalog(metrics)
    comparison = app_utils.filter_fund_comparison(
        catalog, metrics, categories=["Equity"], basis="net"
    )
    assert {"first_live_date", "last_date"}.issubset(comparison.columns)
    assert set(comparison["universe"]) == {"equity"}
    assert len(comparison) == 5


def test_current_holding_builder_sums_to_one_and_labels_combined_assets() -> None:
    catalog = app_utils.build_fund_catalog(_performance_metrics())
    rows = []
    for fund_id in sorted(app_utils.EXPECTED_FUND_IDS):
        universe = catalog.set_index("fund_id").loc[fund_id, "universe"]
        tickers = ["AAA", "BTC-USD"] if universe == "combined" else ["AAA", "BBB"]
        for ticker in tickers:
            rows.append({
                "decision_date": pd.Timestamp("2023-11-30"),
                "effective_date": pd.Timestamp("2023-12-01"),
                "fund_id": fund_id,
                "universe": universe,
                "method": catalog.set_index("fund_id").loc[fund_id, "method"],
                "ticker": ticker,
                "target_weight": 0.5,
                "pretrade_weight": 0.5,
                "asset_cap": 0.6,
                "eligible_asset_count": 2,
                "solver_success": True,
                "fallback_used": False,
            })
    weights = pd.DataFrame(rows, columns=app_utils.FUND_WEIGHT_COLUMNS)
    holdings = app_utils.build_fund_current_holdings(weights, catalog)
    sums = holdings.groupby("fund_id")["target_weight"].sum()
    assert sums.to_numpy() == pytest.approx(np.ones(13))
    combined = holdings.loc[holdings["fund_id"].eq("combined_equal_weight")]
    assert set(combined["asset_class"]) == {"equity", "crypto"}
    assert holdings.equals(holdings.sort_values(
        ["fund_id", "target_weight", "ticker"], ascending=[True, False, True],
        kind="mergesort",
    ).reset_index(drop=True))


def test_common_period_uses_only_intersection_and_never_fills_missing() -> None:
    full = app_utils.common_return_panel(_fund_returns(), ["fund_a", "fund_b"])
    assert full.index.min() == pd.Timestamp("2023-01-31")
    assert full.index.max() == pd.Timestamp("2023-03-01")
    assert len(full) == 4
    missing = app_utils.common_return_panel(
        _fund_returns(missing=True), ["fund_a", "fund_b"]
    )
    assert pd.Timestamp("2023-02-01") not in missing.index
    assert missing.attrs["excluded_nonfinite_dates"] == 1
    assert not missing.isna().any().any()

    absent_row = _fund_returns().loc[
        ~(
            _fund_returns()["fund_id"].eq("fund_b")
            & _fund_returns()["date"].eq(pd.Timestamp("2023-03-01"))
        )
    ]
    intersection = app_utils.common_return_panel(absent_row, ["fund_a", "fund_b"])
    assert pd.Timestamp("2023-03-01") not in intersection.index
    assert intersection.attrs["excluded_nonfinite_dates"] == 0


def test_buy_and_hold_compounds_sleeves_without_reset() -> None:
    result = app_utils.simulate_allocation(
        _fund_returns(), {"fund_a": 0.5, "fund_b": 0.5},
        method="buy_and_hold", periods_per_year=252,
    )
    assert result.daily["portfolio_value"].iloc[0] == pytest.approx(1.05)
    assert result.daily["portfolio_value"].iloc[1] == pytest.approx(1.10)
    assert result.rebalance_dates == ()
    assert not result.daily["is_rebalance"].any()


def test_monthly_reset_uses_previous_total_and_first_common_month_date() -> None:
    result = app_utils.simulate_allocation(
        _fund_returns(), {"fund_a": 0.5, "fund_b": 0.5},
        method="monthly_reset", periods_per_year=252,
    )
    assert result.daily["portfolio_value"].iloc[0] == pytest.approx(1.05)
    assert result.daily["portfolio_value"].iloc[1] == pytest.approx(1.1025)
    assert result.rebalance_dates == (
        pd.Timestamp("2023-01-31"),
        pd.Timestamp("2023-02-01"),
        pd.Timestamp("2023-03-01"),
    )


@pytest.mark.parametrize("weights", [
    {"fund_a": -0.1, "fund_b": 1.1},
    {"fund_a": 0.4, "fund_b": 0.5},
])
def test_allocation_rejects_negative_or_non_100_percent(weights: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        app_utils.validate_allocations(weights)


def test_metrics_and_drawdown_use_compounded_simple_returns() -> None:
    returns = pd.Series([0.10, -0.20, 0.05])
    derived = app_utils.calculate_growth_drawdown(returns)
    assert derived["growth"].tolist() == pytest.approx([1.10, 0.88, 0.924])
    assert derived["drawdown"].iloc[1] == pytest.approx(-0.20)
    metrics = app_utils.calculate_annualised_metrics(returns, periods_per_year=252)
    assert metrics["cumulative_return"] == pytest.approx(-0.076)
    assert metrics["annualised_return"] == pytest.approx(returns.mean() * 252)
    with pytest.raises(ValueError, match="missing"):
        app_utils.calculate_growth_drawdown(pd.Series([0.1, np.nan]))


def test_sentiment_filter_and_latest_snapshot_preserve_missing_gaps() -> None:
    dates = pd.to_datetime(["2023-01-02", "2023-01-03"])
    frame = pd.DataFrame({
        "date": list(dates) * 2,
        "sector": ["Tech", "Tech", "Energy", "Energy"],
        "model": "finance_vader",
        "headline_count": [1, 0, 2, 0],
        "observed_ticker_count": [1, 0, 2, 0],
        "eligible_ticker_count": [2, 2, 2, 2],
        "coverage": [0.5, 0.0, 1.0, 0.0],
        "compound_mean": [0.2, np.nan, 0.1, np.nan],
        "index_0_100": [60.0, np.nan, 55.0, np.nan],
        "causal_expanding_mean": np.nan,
        "causal_expanding_std": np.nan,
        "causal_z": np.nan,
        "descriptive_full_sample_z": np.nan,
    })[app_utils.SECTOR_SENTIMENT_COLUMNS]
    filtered = app_utils.filter_sentiment_time_series(
        frame, sector="Tech", model="finance_vader"
    )
    assert np.isnan(filtered["index_0_100"].iloc[-1])
    snapshot = app_utils.latest_sector_sentiment_snapshot(frame, model="finance_vader")
    assert set(snapshot["sector"]) == {"Tech", "Energy"}
    assert snapshot["index_0_100"].isna().all()


def test_fusion_summary_requires_identical_dates_and_keeps_negative_result() -> None:
    summary = app_utils.base_vs_augmented_fusion_summary(_fusion_comparison())
    assert summary["net_cumulative_return_delta"] == pytest.approx(-0.02)
    assert summary["turnover_delta"] == pytest.approx(0.5)
    assert "underperformed" in summary["summary_text"]
    assert "not retuned" in summary["summary_text"]
    with pytest.raises(app_utils.ArtifactError, match="identical dates"):
        app_utils.base_vs_augmented_fusion_summary(
            _fusion_comparison(mismatched_dates=True)
        )
