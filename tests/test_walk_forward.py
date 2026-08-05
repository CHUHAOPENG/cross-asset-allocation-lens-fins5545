"""Synthetic schedule, no-look-ahead, schema, key, and ordering tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.portfolios import (
    FUND_RETURN_COLUMNS,
    FUND_WEIGHT_COLUMNS,
    METHODS,
    PERFORMANCE_COLUMNS,
    build_monthly_schedule,
    current_holdings,
    fund_identifier,
    run_all_funds,
    run_walk_forward,
)


def _panel(dates: pd.DatetimeIndex, tickers: list[str], seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    common = rng.normal(0.0003, 0.008, size=(len(dates), 1))
    values = common + rng.normal(0.0, 0.006, size=(len(dates), len(tickers)))
    values[0, :] = np.nan
    return pd.DataFrame(values, index=dates, columns=tickers)


def test_monthly_schedule_uses_last_observed_date_and_next_observation() -> None:
    dates = pd.bdate_range("2023-01-03", "2023-03-10")
    schedule = build_monthly_schedule(dates)
    january = schedule.iloc[0]
    assert january["decision_date"] == pd.Timestamp("2023-01-31")
    assert january["effective_date"] == pd.Timestamp("2023-02-01")
    assert schedule.iloc[-1]["decision_date"] == pd.Timestamp("2023-02-28")
    assert schedule.iloc[-1]["effective_date"] == pd.Timestamp("2023-03-01")
    assert pd.Timestamp("2023-03-10") not in set(schedule["decision_date"])


def test_future_return_perturbation_cannot_change_earlier_weights() -> None:
    dates = pd.bdate_range("2020-01-01", periods=230)
    panel = _panel(dates, ["AAA", "BBB", "CCC", "DDD"], 11)
    cutoff = dates[170]
    altered = panel.copy()
    altered.loc[altered.index > cutoff, "AAA"] += 0.40
    baseline = run_walk_forward(
        panel,
        universe="equity",
        method="minimum_variance",
        initial_window=60,
        periods_per_year=252,
    )
    perturbed = run_walk_forward(
        altered,
        universe="equity",
        method="minimum_variance",
        initial_window=60,
        periods_per_year=252,
    )
    left = baseline.weights.loc[baseline.weights["decision_date"] <= cutoff]
    right = perturbed.weights.loc[perturbed.weights["decision_date"] <= cutoff]
    pd.testing.assert_frame_equal(left.reset_index(drop=True), right.reset_index(drop=True))


def test_walk_forward_missing_held_return_is_not_imputed() -> None:
    dates = pd.bdate_range("2020-01-01", periods=180)
    panel = _panel(dates, ["AAA", "BBB", "CCC", "DDD"], 22)
    result = run_walk_forward(
        panel,
        universe="equity",
        method="equal_weight",
        initial_window=50,
        periods_per_year=252,
    )
    missing_date = result.returns["date"].iloc[10]
    altered = panel.copy()
    altered.loc[missing_date, "AAA"] = np.nan
    missing_result = run_walk_forward(
        altered,
        universe="equity",
        method="equal_weight",
        initial_window=50,
        periods_per_year=252,
    )
    row = missing_result.returns.loc[missing_result.returns["date"].eq(missing_date)].iloc[0]
    assert np.isnan(row["gross_return"])
    assert np.isnan(row["net_return"])
    assert (
        missing_result.data_audit["check_name"] == "missing_realised_held_asset_return"
    ).any()


def test_all_funds_have_exact_schemas_unique_keys_constraints_and_stable_order() -> None:
    equity_dates = pd.bdate_range("2020-01-01", periods=340)
    crypto_dates = pd.date_range("2020-01-01", periods=455, freq="D")
    panels = {
        "equity": _panel(equity_dates, ["E1", "E2", "E3", "E4"], 1),
        "crypto": _panel(crypto_dates, ["C1", "C2", "C3", "C4"], 2),
        "combined": _panel(equity_dates, ["E1", "E2", "E3", "E4", "C1", "C2"], 3),
    }
    result = run_all_funds(panels)
    expected_funds = {
        fund_identifier(universe, method)
        for universe in ("equity", "crypto", "combined")
        for method in METHODS
    }
    assert result.fund_returns.columns.tolist() == FUND_RETURN_COLUMNS
    assert result.fund_weights.columns.tolist() == FUND_WEIGHT_COLUMNS
    assert result.performance_metrics.columns.tolist() == PERFORMANCE_COLUMNS
    assert set(result.fund_returns["fund_id"]) == expected_funds
    assert set(result.performance_metrics["fund_id"]) == expected_funds
    assert not result.fund_returns.duplicated(["date", "fund_id"]).any()
    assert not result.fund_weights.duplicated(["effective_date", "fund_id", "ticker"]).any()
    grouped = result.fund_weights.groupby(["effective_date", "fund_id"])
    assert grouped["target_weight"].sum().to_numpy() == pytest.approx(
        np.ones(grouped.ngroups), abs=1e-8
    )
    assert (result.fund_weights["target_weight"] >= -1e-10).all()
    assert (
        result.fund_weights["target_weight"]
        <= result.fund_weights["asset_cap"] + 1e-8
    ).all()
    sorted_returns = result.fund_returns.sort_values(
        ["date", "fund_id"], kind="mergesort"
    ).reset_index(drop=True)
    pd.testing.assert_frame_equal(result.fund_returns, sorted_returns)
    assert set(result.performance_metrics.loc[
        result.performance_metrics["universe"].eq("crypto"), "periods_per_year"
    ]) == {365}
    assert set(result.performance_metrics.loc[
        ~result.performance_metrics["universe"].eq("crypto"), "periods_per_year"
    ]) == {252}
    holdings = current_holdings(result.fund_weights)
    assert set(holdings["fund_id"]) == expected_funds
    assert not holdings.duplicated(["fund_id", "ticker"]).any()
