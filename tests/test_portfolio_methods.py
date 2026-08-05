"""Unit tests for projection, optimisation, drift, turnover, costs, and metrics."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.portfolios import (
    METHODS,
    apply_trading_cost,
    calculate_turnover,
    drift_weights,
    dynamic_asset_cap,
    estimate_weights,
    performance_metrics,
    project_capped_simplex,
    validate_weights,
)


def _history(rows: int = 320) -> pd.DataFrame:
    rng = np.random.default_rng(5545)
    factor = rng.normal(0.0004, 0.009, size=(rows, 1))
    noise = rng.normal(0.0, 0.006, size=(rows, 4))
    returns = factor + noise + np.array([0.0003, 0.0001, -0.0001, 0.0002])
    return pd.DataFrame(returns, columns=["AAA", "BBB", "CCC", "DDD"])


def test_capped_simplex_projection_is_feasible_and_deterministic() -> None:
    vector = np.array([2.0, -1.0, 0.4, 0.1])
    first = project_capped_simplex(vector, 0.35)
    second = project_capped_simplex(vector, 0.35)
    assert first == pytest.approx(second, abs=0.0)
    assert first.sum() == pytest.approx(1.0, abs=1e-10)
    assert first.min() >= 0.0
    assert first.max() <= 0.35 + 1e-12


@pytest.mark.parametrize("method", METHODS)
def test_all_four_methods_return_valid_long_only_capped_weights(method: str) -> None:
    history = _history()
    cap = dynamic_asset_cap(history.shape[1])
    estimate = estimate_weights(history, method, cap=cap)
    valid, reason = validate_weights(estimate.weights, cap)
    assert valid, reason
    assert estimate.weights.index.tolist() == history.columns.tolist()


def test_solver_failure_uses_explicit_previous_or_equal_weight_fallback() -> None:
    def failed_solver(*args, **kwargs):
        return SimpleNamespace(
            success=False,
            status=9,
            message="forced test failure",
            x=np.full(4, np.nan),
        )

    history = _history()
    previous = pd.Series([0.30, 0.30, 0.20, 0.20], index=history.columns)
    reused = estimate_weights(
        history,
        "minimum_variance",
        previous_target=previous,
        solver=failed_solver,
    )
    assert not reused.solver_success
    assert reused.fallback_used
    assert reused.fallback_source == "previous_feasible_target"
    assert reused.weights.to_numpy() == pytest.approx(previous.to_numpy())

    equal = estimate_weights(
        history,
        "minimum_variance",
        previous_target=None,
        solver=failed_solver,
    )
    assert equal.fallback_source == "capped_equal_weight"
    assert equal.weights.to_numpy() == pytest.approx(np.full(4, 0.25))


def test_drift_recursion_matches_exact_two_asset_calculation() -> None:
    weights = pd.Series({"AAA": 0.5, "BBB": 0.5})
    gross, drifted = drift_weights(weights, pd.Series({"AAA": 0.10, "BBB": 0.0}))
    assert gross == pytest.approx(0.05)
    assert drifted["AAA"] == pytest.approx(0.55 / 1.05)
    assert drifted["BBB"] == pytest.approx(0.50 / 1.05)


def test_turnover_uses_union_and_initial_turnover_is_one() -> None:
    target = pd.Series({"AAA": 0.25, "CCC": 0.75})
    pretrade = pd.Series({"AAA": 0.60, "BBB": 0.40})
    expected = 0.5 * (abs(0.25 - 0.60) + abs(0.0 - 0.40) + abs(0.75 - 0.0))
    assert calculate_turnover(target, pretrade) == pytest.approx(expected)
    assert calculate_turnover(target, None, initial=True) == 1.0


def test_trading_cost_formula_applies_only_on_rebalance_date() -> None:
    gross = 0.02
    cost = 0.001
    assert apply_trading_cost(gross, cost, is_rebalance=True) == pytest.approx(
        (1.0 - cost) * (1.0 + gross) - 1.0
    )
    assert apply_trading_cost(gross, cost, is_rebalance=False) == gross


def test_performance_metrics_use_requested_252_or_365_annualisation() -> None:
    returns = pd.Series([0.01, -0.005, 0.002, 0.004])
    metrics_252 = performance_metrics(returns, 252)
    metrics_365 = performance_metrics(returns, 365)
    assert metrics_252["annualised_return"] == pytest.approx(returns.mean() * 252)
    assert metrics_365["annualised_return"] == pytest.approx(returns.mean() * 365)
    assert metrics_365["annualised_volatility"] / metrics_252["annualised_volatility"] == pytest.approx(
        np.sqrt(365 / 252)
    )
