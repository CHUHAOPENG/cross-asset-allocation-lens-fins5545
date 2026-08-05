"""Deterministic expanding walk-forward portfolio engine for Project B.

The engine forms weights through each observed month-end decision date and
first applies them on the next observed date.  It implements twelve funds only:
four methods for Equity, Crypto, and Combined return panels.  There is no
sentiment, fusion, figure, report, or application logic in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.etl import AUDIT_COLUMNS


METHODS = ("equal_weight", "minimum_variance", "risk_parity", "max_sharpe")
METHOD_ID_SUFFIX = {
    "equal_weight": "equal_weight",
    "minimum_variance": "min_variance",
    "risk_parity": "risk_parity",
    "max_sharpe": "max_sharpe",
}
UNIVERSE_CONFIG = {
    "equity": {"initial_window": 252, "periods_per_year": 252},
    "crypto": {"initial_window": 365, "periods_per_year": 365},
    "combined": {"initial_window": 252, "periods_per_year": 252},
}
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
SOLVER_AUDIT_COLUMNS = [
    "decision_date", "effective_date", "fund_id", "universe", "method",
    "eligible_asset_count", "complete_history_rows", "asset_cap", "solver",
    "solver_success", "fallback_used", "fallback_source", "status",
    "solver_status_code", "solver_message", "objective_value", "weight_sum",
    "minimum_weight", "maximum_weight",
]


@dataclass(frozen=True)
class WeightEstimate:
    weights: pd.Series
    solver_success: bool
    fallback_used: bool
    fallback_source: str
    solver_status_code: int
    solver_message: str
    objective_value: float


@dataclass(frozen=True)
class FundBacktest:
    returns: pd.DataFrame
    weights: pd.DataFrame
    solver_audit: pd.DataFrame
    data_audit: pd.DataFrame


@dataclass(frozen=True)
class FundEngineResults:
    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    performance_metrics: pd.DataFrame
    solver_audit: pd.DataFrame
    portfolio_data_audit: pd.DataFrame


def fund_identifier(universe: str, method: str) -> str:
    """Return one of the twelve predeclared stable lowercase fund IDs."""
    if universe not in UNIVERSE_CONFIG or method not in METHOD_ID_SUFFIX:
        raise ValueError("unknown universe or method")
    return f"{universe}_{METHOD_ID_SUFFIX[method]}"


def dynamic_asset_cap(asset_count: int) -> float:
    """Return the predeclared long-only maximum weight for an eligible set."""
    if asset_count <= 0:
        raise ValueError("asset_count must be positive")
    cap = min(0.35, 5.0 / float(asset_count))
    if asset_count * cap < 1.0 - 1e-12:
        raise ValueError("asset cap is infeasible for the eligible asset count")
    return float(cap)


def project_capped_simplex(
    vector: np.ndarray | pd.Series,
    cap: float,
    *,
    tolerance: float = 1e-13,
    max_iterations: int = 250,
) -> np.ndarray:
    """Euclidean projection onto ``sum(w)=1`` and ``0 <= w <= cap``.

    A deterministic bisection locates the common threshold in
    ``clip(vector - threshold, 0, cap)``.
    """
    values = np.asarray(vector, dtype=float).reshape(-1)
    if values.size == 0 or not np.isfinite(values).all():
        raise ValueError("projection vector must be non-empty and finite")
    if not np.isfinite(cap) or cap <= 0.0 or values.size * cap < 1.0 - tolerance:
        raise ValueError("cap is infeasible for a fully invested long-only vector")
    if abs(values.size * cap - 1.0) <= tolerance:
        return np.full(values.size, cap, dtype=float)

    lower = float(values.min() - cap)
    upper = float(values.max())
    projected = np.clip(values - (lower + upper) / 2.0, 0.0, cap)
    for _ in range(max_iterations):
        threshold = (lower + upper) / 2.0
        projected = np.clip(values - threshold, 0.0, cap)
        total = float(projected.sum())
        if abs(total - 1.0) <= tolerance:
            break
        if total > 1.0:
            lower = threshold
        else:
            upper = threshold
    if abs(float(projected.sum()) - 1.0) > 1e-10:
        raise RuntimeError("capped-simplex bisection did not converge")
    return projected


capped_simplex_projection = project_capped_simplex


def validate_weights(
    weights: np.ndarray | pd.Series,
    cap: float,
    *,
    sum_tolerance: float = 1e-8,
    lower_tolerance: float = 1e-10,
    cap_tolerance: float = 1e-8,
) -> tuple[bool, str]:
    """Validate the predeclared full-investment, finite, and bound tolerances."""
    values = np.asarray(weights, dtype=float).reshape(-1)
    if values.size == 0:
        return False, "empty weight vector"
    if not np.isfinite(values).all():
        return False, "non-finite weight"
    if abs(float(values.sum()) - 1.0) > sum_tolerance:
        return False, f"weight sum {values.sum():.16g} is not one"
    if float(values.min()) < -lower_tolerance:
        return False, f"minimum weight {values.min():.16g} violates long-only"
    if float(values.max()) > cap + cap_tolerance:
        return False, f"maximum weight {values.max():.16g} exceeds cap {cap:.16g}"
    return True, "ok"


def shrunk_covariance(history: pd.DataFrame) -> np.ndarray:
    """Sample covariance with fixed 10% diagonal shrinkage."""
    covariance = history.cov(ddof=1).to_numpy(dtype=float)
    covariance = 0.9 * covariance + 0.1 * np.diag(np.diag(covariance))
    covariance = (covariance + covariance.T) / 2.0
    if not np.isfinite(covariance).all():
        raise ValueError("covariance estimate is not finite")
    return covariance


def shrunk_expected_returns(history: pd.DataFrame) -> np.ndarray:
    """Expanding arithmetic means with 50% cross-sectional mean shrinkage."""
    means = history.mean(axis=0).to_numpy(dtype=float)
    cross_sectional_mean = float(means.mean())
    expected = 0.5 * means + 0.5 * cross_sectional_mean
    if not np.isfinite(expected).all():
        raise ValueError("expected-return estimate is not finite")
    return expected


def _objective_functions(
    method: str,
    covariance: np.ndarray,
    expected_returns: np.ndarray,
) -> tuple[Callable[[np.ndarray], float], Callable[[np.ndarray], np.ndarray]]:
    if method == "minimum_variance":
        def objective(weights: np.ndarray) -> float:
            return float(weights @ covariance @ weights)

        def gradient(weights: np.ndarray) -> np.ndarray:
            return 2.0 * covariance @ weights

        return objective, gradient

    if method == "max_sharpe":
        def objective(weights: np.ndarray) -> float:
            variance = float(weights @ covariance @ weights)
            if variance <= 1e-20:
                return 1e12
            return -float(expected_returns @ weights) / np.sqrt(variance)

        def gradient(weights: np.ndarray) -> np.ndarray:
            covariance_weights = covariance @ weights
            variance = float(weights @ covariance_weights)
            if variance <= 1e-20:
                return np.zeros_like(weights)
            mean = float(expected_returns @ weights)
            return -(
                expected_returns / np.sqrt(variance)
                - mean * covariance_weights / (variance ** 1.5)
            )

        return objective, gradient

    if method == "risk_parity":
        scale = 1e12

        def objective(weights: np.ndarray) -> float:
            covariance_weights = covariance @ weights
            variance = float(weights @ covariance_weights)
            contributions = weights * covariance_weights
            deviations = contributions - variance / float(len(weights))
            return float(scale * deviations @ deviations)

        def gradient(weights: np.ndarray) -> np.ndarray:
            covariance_weights = covariance @ weights
            variance = float(weights @ covariance_weights)
            contributions = weights * covariance_weights
            deviations = contributions - variance / float(len(weights))
            jacobian = (
                np.diag(covariance_weights)
                + np.diag(weights) @ covariance
                - np.ones((len(weights), 1))
                @ (2.0 * covariance_weights / float(len(weights))).reshape(1, -1)
            )
            return scale * 2.0 * jacobian.T @ deviations

        return objective, gradient
    raise ValueError(f"unknown optimisation method: {method}")


def _fallback_weights(
    tickers: pd.Index,
    cap: float,
    previous_target: pd.Series | None,
) -> tuple[pd.Series, str]:
    if previous_target is not None:
        previous = previous_target.astype(float)
        lost_positive_asset = any(
            ticker not in tickers and weight > 1e-10
            for ticker, weight in previous.items()
        )
        candidate = previous.reindex(tickers, fill_value=0.0)
        valid, _ = validate_weights(candidate, cap)
        if not lost_positive_asset and valid:
            return candidate, "previous_feasible_target"
    equal = project_capped_simplex(np.full(len(tickers), 1.0 / len(tickers)), cap)
    return pd.Series(equal, index=tickers, dtype=float), "capped_equal_weight"


def estimate_weights(
    history: pd.DataFrame,
    method: str,
    *,
    cap: float | None = None,
    previous_target: pd.Series | None = None,
    solver: Callable[..., Any] | None = None,
) -> WeightEstimate:
    """Estimate one target using only the supplied complete historical panel."""
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    if history.empty or history.shape[1] == 0:
        raise ValueError("history must contain observations and assets")
    if history.isna().any().any() or not np.isfinite(history.to_numpy(dtype=float)).all():
        raise ValueError("optimisation history must be complete and finite")
    tickers = pd.Index(history.columns.astype(str))
    cap_value = dynamic_asset_cap(len(tickers)) if cap is None else float(cap)
    equal = project_capped_simplex(np.full(len(tickers), 1.0 / len(tickers)), cap_value)
    if method == "equal_weight":
        return WeightEstimate(
            weights=pd.Series(equal, index=tickers, dtype=float),
            solver_success=True,
            fallback_used=False,
            fallback_source="none",
            solver_status_code=0,
            solver_message="direct capped equal weight",
            objective_value=np.nan,
        )

    covariance = shrunk_covariance(history)
    expected = shrunk_expected_returns(history)
    objective, gradient = _objective_functions(method, covariance, expected)
    solver_function = minimize if solver is None else solver
    try:
        result = solver_function(
            objective,
            equal,
            jac=gradient,
            method="SLSQP",
            bounds=[(0.0, cap_value)] * len(tickers),
            constraints={
                "type": "eq",
                "fun": lambda weights: float(np.sum(weights) - 1.0),
                "jac": lambda weights: np.ones_like(weights),
            },
            options={"maxiter": 1000, "ftol": 1e-10, "disp": False},
        )
        raw_weights = np.asarray(getattr(result, "x", np.full(len(tickers), np.nan)), dtype=float)
        valid, validation_message = validate_weights(raw_weights, cap_value)
        success = bool(getattr(result, "success", False)) and valid
        status_code = int(getattr(result, "status", -1))
        message = str(getattr(result, "message", "solver returned no message"))
        if not valid:
            message = f"{message}; invalid output: {validation_message}"
        if success:
            projected = project_capped_simplex(raw_weights, cap_value)
            return WeightEstimate(
                weights=pd.Series(projected, index=tickers, dtype=float),
                solver_success=True,
                fallback_used=False,
                fallback_source="none",
                solver_status_code=status_code,
                solver_message=message,
                objective_value=float(objective(projected)),
            )
    except Exception as exc:  # an exception is an explicit, audited solver failure
        status_code = -1
        message = f"solver exception: {type(exc).__name__}: {exc}"

    fallback, source = _fallback_weights(tickers, cap_value, previous_target)
    return WeightEstimate(
        weights=fallback,
        solver_success=False,
        fallback_used=True,
        fallback_source=source,
        solver_status_code=status_code,
        solver_message=message,
        objective_value=float(objective(fallback)),
    )


def build_monthly_schedule(dates: pd.DatetimeIndex | pd.Series) -> pd.DataFrame:
    """Pair each observed calendar-month end with the first following date."""
    index = pd.DatetimeIndex(pd.to_datetime(dates)).drop_duplicates().sort_values()
    if len(index) < 2:
        return pd.DataFrame(columns=["decision_date", "effective_date"])
    dated = pd.Series(index, index=index)
    decisions = dated.groupby(index.to_period("M"), sort=True).max().tolist()
    rows: list[dict[str, pd.Timestamp]] = []
    for decision in decisions:
        position = int(index.searchsorted(decision, side="right"))
        if position >= len(index):
            continue
        rows.append({"decision_date": decision, "effective_date": index[position]})
    return pd.DataFrame(rows, columns=["decision_date", "effective_date"])


def _eligible_history(
    panel: pd.DataFrame,
    decision_date: pd.Timestamp,
    initial_window: int,
) -> tuple[pd.DataFrame, list[str]]:
    history = panel.loc[:decision_date]
    decision_valid = history.iloc[-1].notna()
    valid_counts = history.notna().sum(axis=0)
    eligible = sorted(
        ticker for ticker in panel.columns
        if bool(decision_valid[ticker]) and int(valid_counts[ticker]) >= initial_window
    )
    if not eligible:
        return pd.DataFrame(index=history.index), []
    complete = history.loc[:, eligible].dropna(axis=0, how="any")
    return complete, eligible


def calculate_turnover(
    target_weights: pd.Series,
    pretrade_weights: pd.Series | None,
    *,
    initial: bool = False,
) -> float:
    """One-way turnover over the union of old and new asset labels."""
    if initial or pretrade_weights is None or pretrade_weights.empty:
        return 1.0
    union = target_weights.index.union(pretrade_weights.index)
    target = target_weights.reindex(union, fill_value=0.0)
    pretrade = pretrade_weights.reindex(union, fill_value=0.0)
    if target.isna().any() or pretrade.isna().any():
        return np.nan
    return float(0.5 * np.abs(target - pretrade).sum())


def drift_weights(weights: pd.Series, realised_returns: pd.Series) -> tuple[float, pd.Series]:
    """Return the holding-period return and drifted end-of-day weights."""
    aligned_returns = realised_returns.reindex(weights.index)
    if aligned_returns.isna().any() or not np.isfinite(aligned_returns.to_numpy(dtype=float)).all():
        raise ValueError("held-asset realised returns must be complete and finite")
    gross_return = float(weights @ aligned_returns)
    if gross_return <= -1.0:
        raise ValueError("portfolio gross return must be greater than -100%")
    drifted = weights * (1.0 + aligned_returns) / (1.0 + gross_return)
    return gross_return, drifted


def apply_trading_cost(
    gross_return: float,
    trading_cost: float,
    *,
    is_rebalance: bool,
) -> float:
    """Apply cost once on a rebalance date using the predeclared formula."""
    if not is_rebalance:
        return float(gross_return)
    return float((1.0 - trading_cost) * (1.0 + gross_return) - 1.0)


def _growth_and_drawdown(returns: pd.Series) -> tuple[pd.Series, pd.Series]:
    growth = (1.0 + returns.astype(float)).cumprod(skipna=False)
    drawdown = growth / growth.cummax() - 1.0
    return growth, drawdown


def _solver_audit_row(
    *,
    decision_date: pd.Timestamp,
    effective_date: pd.Timestamp,
    fund_id: str,
    universe: str,
    method: str,
    eligible_count: int,
    complete_rows: int,
    cap: float,
    estimate: WeightEstimate | None,
    status: str,
    message: str = "",
) -> dict[str, Any]:
    weights = estimate.weights.to_numpy(dtype=float) if estimate is not None else np.array([])
    return {
        "decision_date": decision_date,
        "effective_date": effective_date,
        "fund_id": fund_id,
        "universe": universe,
        "method": method,
        "eligible_asset_count": int(eligible_count),
        "complete_history_rows": int(complete_rows),
        "asset_cap": cap,
        "solver": "direct" if method == "equal_weight" else "SLSQP",
        "solver_success": bool(estimate.solver_success) if estimate is not None else False,
        "fallback_used": bool(estimate.fallback_used) if estimate is not None else False,
        "fallback_source": estimate.fallback_source if estimate is not None else "none",
        "status": status,
        "solver_status_code": estimate.solver_status_code if estimate is not None else -1,
        "solver_message": estimate.solver_message if estimate is not None else message,
        "objective_value": estimate.objective_value if estimate is not None else np.nan,
        "weight_sum": float(weights.sum()) if len(weights) else np.nan,
        "minimum_weight": float(weights.min()) if len(weights) else np.nan,
        "maximum_weight": float(weights.max()) if len(weights) else np.nan,
    }


def run_walk_forward(
    panel: pd.DataFrame,
    *,
    universe: str,
    method: str,
    initial_window: int | None = None,
    periods_per_year: int | None = None,
    transaction_cost_rate: float = 0.001,
    solver: Callable[..., Any] | None = None,
) -> FundBacktest:
    """Run one expanding monthly out-of-sample fund backtest."""
    if universe not in UNIVERSE_CONFIG:
        raise ValueError(f"unknown universe: {universe}")
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    if panel.empty or panel.shape[1] == 0:
        raise ValueError("return panel must not be empty")
    if panel.index.duplicated().any() or not panel.index.is_monotonic_increasing:
        raise ValueError("return panel dates must be unique and sorted")
    values = panel.to_numpy(dtype=float)
    if not (np.isfinite(values) | np.isnan(values)).all():
        raise ValueError("return panel has non-finite non-missing values")
    if transaction_cost_rate < 0.0:
        raise ValueError("transaction_cost_rate must be non-negative")

    initial = int(initial_window or UNIVERSE_CONFIG[universe]["initial_window"])
    annualisation = int(periods_per_year or UNIVERSE_CONFIG[universe]["periods_per_year"])
    fund_id = fund_identifier(universe, method)
    schedule = build_monthly_schedule(panel.index)
    events: list[dict[str, Any]] = []
    solver_rows: list[dict[str, Any]] = []
    previous_target: pd.Series | None = None

    for row in schedule.itertuples(index=False):
        complete_history, eligible = _eligible_history(panel, row.decision_date, initial)
        eligible_count = len(eligible)
        complete_rows = len(complete_history)
        if eligible_count == 0 or complete_rows < initial:
            solver_rows.append(_solver_audit_row(
                decision_date=row.decision_date,
                effective_date=row.effective_date,
                fund_id=fund_id,
                universe=universe,
                method=method,
                eligible_count=eligible_count,
                complete_rows=complete_rows,
                cap=np.nan,
                estimate=None,
                status="skipped_insufficient_complete_history",
                message="No eligible assets or fewer complete rows than the initial window.",
            ))
            continue
        cap = dynamic_asset_cap(eligible_count)
        estimate = estimate_weights(
            complete_history,
            method,
            cap=cap,
            previous_target=previous_target,
            solver=solver,
        )
        valid, reason = validate_weights(estimate.weights, cap)
        if not valid:
            raise RuntimeError(f"{fund_id} final target failed validation: {reason}")
        status = "fallback" if estimate.fallback_used else "ok"
        solver_rows.append(_solver_audit_row(
            decision_date=row.decision_date,
            effective_date=row.effective_date,
            fund_id=fund_id,
            universe=universe,
            method=method,
            eligible_count=eligible_count,
            complete_rows=complete_rows,
            cap=cap,
            estimate=estimate,
            status=status,
        ))
        target = estimate.weights.copy()
        events.append({
            "decision_date": row.decision_date,
            "effective_date": row.effective_date,
            "target": target,
            "cap": cap,
            "eligible_count": eligible_count,
            "estimate": estimate,
        })
        previous_target = target

    if not events:
        raise ValueError(f"{fund_id} produced no live rebalance after its initial window")

    event_by_date = {event["effective_date"]: event for event in events}
    first_live_date = min(event_by_date)
    current_weights: pd.Series | None = None
    drift_known = True
    return_rows: list[dict[str, Any]] = []
    weight_rows: list[dict[str, Any]] = []
    data_rows: list[dict[str, Any]] = []
    missing_realised_events = 0

    for date, realised in panel.loc[first_live_date:].iterrows():
        event = event_by_date.get(date)
        is_rebalance = event is not None
        turnover = 0.0
        trading_cost = 0.0
        if event is not None:
            target = event["target"]
            is_initial = current_weights is None
            pretrade = None if is_initial else current_weights.copy()
            if not drift_known and not is_initial:
                pretrade = pd.Series(np.nan, index=current_weights.index, dtype=float)
            turnover = calculate_turnover(target, pretrade, initial=is_initial)
            trading_cost = transaction_cost_rate * turnover
            union = target.index if pretrade is None else target.index.union(pretrade.index)
            for ticker in sorted(union):
                weight_rows.append({
                    "decision_date": event["decision_date"],
                    "effective_date": date,
                    "fund_id": fund_id,
                    "universe": universe,
                    "method": method,
                    "ticker": ticker,
                    "target_weight": float(target.get(ticker, 0.0)),
                    "pretrade_weight": 0.0 if pretrade is None else float(pretrade.get(ticker, 0.0)),
                    "asset_cap": event["cap"],
                    "eligible_asset_count": event["eligible_count"],
                    "solver_success": event["estimate"].solver_success,
                    "fallback_used": event["estimate"].fallback_used,
                })
            current_weights = target.copy()
            drift_known = True

        if current_weights is None:
            continue
        held_returns = realised.reindex(current_weights.index)
        missing_tickers = held_returns.index[
            held_returns.isna() | ~np.isfinite(held_returns.to_numpy(dtype=float))
        ].tolist()
        if not drift_known and not is_rebalance:
            gross_return = np.nan
            net_return = np.nan
        elif missing_tickers:
            missing_realised_events += 1
            gross_return = np.nan
            net_return = np.nan
            drift_known = False
            data_rows.append({
                "stage": "portfolio",
                "universe": universe,
                "date": date,
                "fund_id": fund_id,
                "ticker": "|".join(map(str, missing_tickers)),
                "check_name": "missing_realised_held_asset_return",
                "observed_value": len(missing_tickers),
                "status": "warning",
                "message": "Fund return is missing; no return was imputed and drift is unknown until the next target reset.",
            })
        else:
            gross_return, current_weights = drift_weights(current_weights, held_returns)
            net_return = apply_trading_cost(
                gross_return,
                trading_cost,
                is_rebalance=is_rebalance,
            )
        return_rows.append({
            "date": date,
            "fund_id": fund_id,
            "universe": universe,
            "method": method,
            "periods_per_year": annualisation,
            "gross_return": gross_return,
            "turnover": turnover,
            "trading_cost": trading_cost,
            "net_return": net_return,
            "is_rebalance": is_rebalance,
        })

    returns = pd.DataFrame(return_rows)
    gross_growth, gross_drawdown = _growth_and_drawdown(returns["gross_return"])
    net_growth, net_drawdown = _growth_and_drawdown(returns["net_return"])
    returns["growth_gross"] = gross_growth
    returns["growth_net"] = net_growth
    returns["drawdown_gross"] = gross_drawdown
    returns["drawdown_net"] = net_drawdown
    returns = returns[FUND_RETURN_COLUMNS]

    data_rows.append({
        "stage": "portfolio",
        "universe": universe,
        "date": pd.NaT,
        "fund_id": fund_id,
        "ticker": "",
        "check_name": "missing_realised_return_events",
        "observed_value": missing_realised_events,
        "status": "pass" if missing_realised_events == 0 else "warning",
        "message": "Count of live dates with at least one unavailable held-asset return.",
    })
    return FundBacktest(
        returns=returns,
        weights=pd.DataFrame(weight_rows, columns=FUND_WEIGHT_COLUMNS),
        solver_audit=pd.DataFrame(solver_rows, columns=SOLVER_AUDIT_COLUMNS),
        data_audit=pd.DataFrame(data_rows, columns=AUDIT_COLUMNS),
    )


def performance_metrics(
    daily_returns: pd.Series,
    periods_per_year: int = 252,
) -> dict[str, float | int]:
    """Compute predeclared arithmetic annualisation and compounded drawdown."""
    series = pd.Series(daily_returns, dtype=float)
    valid = series.dropna()
    observations = int(len(valid))
    if observations == 0 or series.isna().any():
        return {
            "observations": observations,
            "cumulative_return": np.nan,
            "annualised_return": np.nan,
            "annualised_volatility": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
        }
    cumulative_return = float((1.0 + valid).prod() - 1.0)
    annualised_return = float(valid.mean() * periods_per_year)
    annualised_volatility = float(valid.std(ddof=1) * np.sqrt(periods_per_year))
    sharpe = (
        annualised_return / annualised_volatility
        if np.isfinite(annualised_volatility) and annualised_volatility > 0.0
        else np.nan
    )
    growth = (1.0 + valid).cumprod()
    max_drawdown = float((growth / growth.cummax() - 1.0).min())
    return {
        "observations": observations,
        "cumulative_return": cumulative_return,
        "annualised_return": annualised_return,
        "annualised_volatility": annualised_volatility,
        "sharpe": float(sharpe),
        "max_drawdown": max_drawdown,
    }


def _performance_row(
    returns: pd.DataFrame,
    solver_audit: pd.DataFrame,
) -> dict[str, Any]:
    first = returns.iloc[0]
    periods = int(first["periods_per_year"])
    gross = performance_metrics(returns["gross_return"], periods)
    net = performance_metrics(returns["net_return"], periods)
    rebalance = returns.loc[returns["is_rebalance"]]
    live_solver_rows = solver_audit.loc[solver_audit["status"].isin(["ok", "fallback"])]
    return {
        "fund_id": first["fund_id"],
        "universe": first["universe"],
        "method": first["method"],
        "first_live_date": returns["date"].min(),
        "last_date": returns["date"].max(),
        "observations": gross["observations"],
        "periods_per_year": periods,
        "cumulative_return_gross": gross["cumulative_return"],
        "annualised_return_gross": gross["annualised_return"],
        "annualised_volatility_gross": gross["annualised_volatility"],
        "sharpe_gross": gross["sharpe"],
        "max_drawdown_gross": gross["max_drawdown"],
        "cumulative_return_net": net["cumulative_return"],
        "annualised_return_net": net["annualised_return"],
        "annualised_volatility_net": net["annualised_volatility"],
        "sharpe_net": net["sharpe"],
        "max_drawdown_net": net["max_drawdown"],
        "total_turnover": float(returns["turnover"].sum(min_count=1)),
        "average_rebalance_turnover": float(rebalance["turnover"].mean()),
        "total_trading_cost": float(returns["trading_cost"].sum(min_count=1)),
        "rebalance_count": int(len(rebalance)),
        "fallback_count": int(live_solver_rows["fallback_used"].sum()),
    }


def run_all_funds(
    panels: dict[str, pd.DataFrame],
    *,
    transaction_cost_rate: float = 0.001,
) -> FundEngineResults:
    """Run the exact 12 predeclared universe-method fund identifiers."""
    missing = sorted(set(UNIVERSE_CONFIG).difference(panels))
    if missing:
        raise ValueError(f"missing return panels: {missing}")
    backtests: list[FundBacktest] = []
    for universe in ("equity", "crypto", "combined"):
        config = UNIVERSE_CONFIG[universe]
        for method in METHODS:
            backtests.append(run_walk_forward(
                panels[universe],
                universe=universe,
                method=method,
                initial_window=config["initial_window"],
                periods_per_year=config["periods_per_year"],
                transaction_cost_rate=transaction_cost_rate,
            ))

    fund_returns = pd.concat([result.returns for result in backtests], ignore_index=True)
    fund_returns = fund_returns.sort_values(["date", "fund_id"], kind="mergesort").reset_index(drop=True)
    fund_weights = pd.concat([result.weights for result in backtests], ignore_index=True)
    fund_weights = fund_weights.sort_values(
        ["effective_date", "fund_id", "ticker"], kind="mergesort"
    ).reset_index(drop=True)
    solver_audit = pd.concat([result.solver_audit for result in backtests], ignore_index=True)
    solver_audit = solver_audit.sort_values(
        ["decision_date", "fund_id"], kind="mergesort"
    ).reset_index(drop=True)
    data_audit = pd.concat([result.data_audit for result in backtests], ignore_index=True)
    data_audit = data_audit.sort_values(
        ["stage", "universe", "date", "fund_id", "ticker"],
        kind="mergesort",
        na_position="last",
    ).reset_index(drop=True)
    metric_rows = [
        _performance_row(result.returns, result.solver_audit)
        for result in backtests
    ]
    metrics = pd.DataFrame(metric_rows, columns=PERFORMANCE_COLUMNS).sort_values(
        "fund_id", kind="mergesort"
    ).reset_index(drop=True)
    return FundEngineResults(
        fund_returns=fund_returns[FUND_RETURN_COLUMNS],
        fund_weights=fund_weights[FUND_WEIGHT_COLUMNS],
        performance_metrics=metrics[PERFORMANCE_COLUMNS],
        solver_audit=solver_audit[SOLVER_AUDIT_COLUMNS],
        portfolio_data_audit=data_audit[AUDIT_COLUMNS],
    )


def current_holdings(fund_weights: pd.DataFrame) -> pd.DataFrame:
    """Return the latest generated target holdings for every available fund."""
    missing = sorted(set(FUND_WEIGHT_COLUMNS).difference(fund_weights.columns))
    if missing:
        raise ValueError(f"fund weights missing required columns: {missing}")
    if fund_weights.empty:
        return fund_weights[FUND_WEIGHT_COLUMNS].copy()
    latest = fund_weights.groupby("fund_id", sort=True)["effective_date"].transform("max")
    holdings = fund_weights.loc[
        fund_weights["effective_date"].eq(latest) & fund_weights["target_weight"].gt(1e-10),
        FUND_WEIGHT_COLUMNS,
    ]
    return holdings.sort_values(["fund_id", "ticker"], kind="mergesort").reset_index(drop=True)


oos_backtest = run_walk_forward
