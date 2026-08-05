"""Fixed, coverage-aware finance-sentiment overlay for Equity Risk Parity."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import portfolios


BASE_FUND_ID = "equity_risk_parity"
AUGMENTED_FUND_ID = "equity_risk_parity_sentiment"
AUGMENTED_METHOD = "risk_parity_sentiment"
SENTIMENT_MODEL = "finance_vader"
TILT_STRENGTH = 0.10
Z_CLIP = 2.0
MULTIPLIER_LOWER = 0.80
MULTIPLIER_UPPER = 1.20
TRANSACTION_COST_RATE = 0.001

FUSION_SECTOR_MULTIPLIER_COLUMNS = [
    "decision_date", "effective_date", "sector", "model", "source_date",
    "signal_age", "trading_z", "effective_coverage", "z_bounded",
    "multiplier", "has_active_signal",
]
FUSION_REBALANCE_AUDIT_COLUMNS = [
    "decision_date", "effective_date", "fund_id", "eligible_asset_count",
    "asset_cap", "active_signal_sector_count", "carried_signal_sector_count",
    "base_weight_sum", "augmented_weight_sum", "maximum_base_weight",
    "maximum_augmented_weight", "l1_target_change", "projection_distance",
    "turnover", "trading_cost", "timing_valid", "constraints_valid",
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
FUSION_YEARLY_COLUMNS = [
    "year", "fund_id", "observations", "cumulative_return_gross",
    "cumulative_return_net", "annualised_volatility_gross",
    "annualised_volatility_net", "total_turnover", "total_trading_cost",
]
FUSION_CURRENT_HOLDINGS_COLUMNS = [
    "as_of_date", "ticker", "sector", "base_weight", "augmented_weight",
    "weight_change", "latest_signal_source_date", "latest_signal_age",
    "latest_trading_z", "latest_effective_coverage", "latest_multiplier",
]


@dataclass(frozen=True)
class FusionResults:
    """All augmented-fund rows and focused comparison artifacts."""

    fund_returns: pd.DataFrame
    fund_weights: pd.DataFrame
    performance_metrics: pd.DataFrame
    sector_multipliers: pd.DataFrame
    rebalance_audit: pd.DataFrame
    comparison: pd.DataFrame
    yearly_comparison: pd.DataFrame
    current_holdings: pd.DataFrame


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def validate_ticker_sector_mapping(
    mapping: pd.DataFrame,
    *,
    required_tickers: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Return a deterministic one-to-one, non-missing ticker-sector mapping."""
    _require_columns(mapping, ["ticker", "sector"], "ticker-sector mapping")
    clean = mapping[["ticker", "sector"]].copy()
    if clean.isna().any().any():
        raise ValueError("ticker-sector mapping contains missing values")
    clean["ticker"] = clean["ticker"].astype(str)
    clean["sector"] = clean["sector"].astype(str)
    clean = clean.drop_duplicates().sort_values(["ticker", "sector"], kind="mergesort")
    conflicts = clean.groupby("ticker", sort=False)["sector"].nunique().gt(1)
    if conflicts.any():
        raise ValueError("a ticker maps to more than one sector")
    clean = clean.drop_duplicates("ticker", keep="first").reset_index(drop=True)
    if required_tickers is not None:
        required = {str(ticker) for ticker in required_tickers}
        absent = sorted(required.difference(clean["ticker"]))
        if absent:
            raise ValueError(f"ticker-sector mapping is missing tickers: {absent}")
    return clean


def select_finance_signals(
    signals: pd.DataFrame,
    *,
    decision_date: pd.Timestamp,
    effective_date: pd.Timestamp,
    sectors: Iterable[str],
) -> pd.DataFrame:
    """Select only causal finance-VADER signals usable for one target date."""
    _require_columns(
        signals,
        [
            "effective_date", "source_date", "sector", "model", "signal_age",
            "effective_coverage", "trading_z",
        ],
        "sector sentiment signal",
    )
    decision = pd.Timestamp(decision_date)
    effective = pd.Timestamp(effective_date)
    if effective <= decision:
        raise ValueError("effective_date must be after decision_date")
    sector_frame = pd.DataFrame({"sector": sorted({str(value) for value in sectors})})
    prepared = signals.copy()
    prepared["effective_date"] = pd.to_datetime(prepared["effective_date"])
    prepared["source_date"] = pd.to_datetime(prepared["source_date"])
    selected = prepared.loc[
        prepared["model"].eq(SENTIMENT_MODEL)
        & prepared["effective_date"].eq(effective)
        & prepared["sector"].astype(str).isin(sector_frame["sector"])
    ].copy()
    if selected.duplicated(["sector"]).any():
        raise ValueError("duplicate finance signal for effective date and sector")
    selected = sector_frame.merge(
        selected[
            [
                "sector", "source_date", "signal_age", "effective_coverage",
                "trading_z",
            ]
        ],
        on="sector",
        how="left",
        validate="one_to_one",
    )
    selected.insert(0, "model", SENTIMENT_MODEL)
    selected["effective_date"] = effective
    selected["decision_date"] = decision

    z_values = pd.to_numeric(selected["trading_z"], errors="coerce")
    coverage_values = pd.to_numeric(selected["effective_coverage"], errors="coerce")
    has_z = z_values.notna() & np.isfinite(z_values.astype(float))
    has_coverage = coverage_values.notna() & np.isfinite(coverage_values.astype(float))
    selected["has_active_signal"] = has_z & has_coverage
    active = selected.loc[selected["has_active_signal"]]
    if active["source_date"].isna().any() or active["signal_age"].isna().any():
        raise ValueError("an active signal is missing its source date or age")
    if (active["source_date"] > decision).any():
        raise ValueError("a signal source date is after the portfolio decision date")
    ages = active["signal_age"].astype(int)
    age_zero = active.loc[ages.eq(0)]
    carried = active.loc[ages.gt(0)]
    if not age_zero["source_date"].eq(decision).all():
        raise ValueError("an age-zero signal does not use the decision date")
    if not (carried["source_date"] < decision).all():
        raise ValueError("a carried signal is not strictly earlier than the decision date")
    if (ages < 0).any():
        raise ValueError("signal age cannot be negative")
    coverage = active["effective_coverage"].astype(float)
    if ((coverage < 0.0) | (coverage > 1.0)).any():
        raise ValueError("effective coverage lies outside [0, 1]")
    return selected.sort_values("sector", kind="mergesort").reset_index(drop=True)


def calculate_sector_multiplier(
    trading_z: float | int | None,
    effective_coverage: float | int | None,
    *,
    tilt_strength: float = TILT_STRENGTH,
    z_clip: float = Z_CLIP,
    lower: float = MULTIPLIER_LOWER,
    upper: float = MULTIPLIER_UPPER,
) -> tuple[float, float]:
    """Return ``(z_bounded, multiplier)`` under the fixed coverage-aware rule."""
    z = float(trading_z) if trading_z is not None else np.nan
    coverage = float(effective_coverage) if effective_coverage is not None else np.nan
    if not np.isfinite(z) or not np.isfinite(coverage):
        return np.nan, 1.0
    bounded = float(np.clip(z, -z_clip, z_clip))
    multiplier = float(np.clip(1.0 + tilt_strength * coverage * bounded, lower, upper))
    return bounded, multiplier


def build_sector_multipliers(
    signals: pd.DataFrame,
    events: pd.DataFrame,
    mapping: pd.DataFrame,
) -> pd.DataFrame:
    """Build the complete sector multiplier grid for target events."""
    _require_columns(events, ["decision_date", "effective_date", "ticker"], "base events")
    validated_mapping = validate_ticker_sector_mapping(
        mapping, required_tickers=events["ticker"].astype(str).unique()
    )
    joined = events[["decision_date", "effective_date", "ticker"]].merge(
        validated_mapping, on="ticker", how="left", validate="many_to_one"
    )
    rows: list[dict[str, Any]] = []
    for (decision, effective), group in joined.groupby(
        ["decision_date", "effective_date"], sort=True
    ):
        selected = select_finance_signals(
            signals,
            decision_date=pd.Timestamp(decision),
            effective_date=pd.Timestamp(effective),
            sectors=group["sector"].unique(),
        )
        for row in selected.itertuples(index=False):
            z_bounded, multiplier = calculate_sector_multiplier(
                row.trading_z, row.effective_coverage
            )
            rows.append({
                "decision_date": pd.Timestamp(decision),
                "effective_date": pd.Timestamp(effective),
                "sector": row.sector,
                "model": SENTIMENT_MODEL,
                "source_date": row.source_date,
                "signal_age": row.signal_age,
                "trading_z": row.trading_z,
                "effective_coverage": row.effective_coverage,
                "z_bounded": z_bounded,
                "multiplier": multiplier,
                "has_active_signal": bool(row.has_active_signal),
            })
    output = pd.DataFrame(rows, columns=FUSION_SECTOR_MULTIPLIER_COLUMNS)
    output["signal_age"] = output["signal_age"].astype("Int64")
    return output.sort_values(
        ["effective_date", "sector"], kind="mergesort"
    ).reset_index(drop=True)


def apply_sector_multipliers(
    base_weights: pd.Series,
    mapping: pd.DataFrame,
    sector_multipliers: pd.DataFrame,
    *,
    cap: float,
) -> tuple[pd.Series, float]:
    """Tilt, renormalise, and project one base target onto its capped simplex."""
    base = pd.Series(base_weights, dtype=float).copy()
    if base.index.duplicated().any():
        raise ValueError("base target contains duplicate tickers")
    valid, reason = portfolios.validate_weights(base, cap)
    if not valid:
        raise ValueError(f"base target is infeasible: {reason}")
    mapped = validate_ticker_sector_mapping(mapping, required_tickers=base.index)
    multiplier_frame = sector_multipliers[["sector", "multiplier"]].copy()
    if multiplier_frame["sector"].duplicated().any():
        raise ValueError("sector multiplier table contains duplicate sectors")
    ticker_frame = pd.DataFrame({"ticker": base.index, "base_weight": base.to_numpy()})
    joined = ticker_frame.merge(mapped, on="ticker", how="left", validate="one_to_one")
    joined = joined.merge(multiplier_frame, on="sector", how="left", validate="many_to_one")
    if joined["multiplier"].isna().any():
        raise ValueError("a base target sector has no multiplier")
    multipliers = joined.set_index("ticker")["multiplier"].reindex(base.index).astype(float)
    if np.array_equal(multipliers.to_numpy(), np.ones(len(multipliers))):
        return base.copy(), 0.0
    tilted = base * multipliers
    if not np.isfinite(tilted.to_numpy()).all() or float(tilted.sum()) <= 0.0:
        raise ValueError("tilted target cannot be normalised")
    normalised = tilted / float(tilted.sum())
    projected_values = portfolios.project_capped_simplex(normalised.to_numpy(), cap)
    projected = pd.Series(projected_values, index=base.index, dtype=float)
    valid, reason = portfolios.validate_weights(projected, cap)
    if not valid:
        raise RuntimeError(f"projected augmented target is infeasible: {reason}")
    projection_distance = float(np.linalg.norm(projected.to_numpy() - normalised.to_numpy()))
    return projected, projection_distance


def construct_augmented_targets(
    base_fund_weights: pd.DataFrame,
    signals: pd.DataFrame,
    mapping: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Construct every monthly augmented target and its pre-return audit fields."""
    _require_columns(base_fund_weights, portfolios.FUND_WEIGHT_COLUMNS, "fund weights")
    base = base_fund_weights.loc[base_fund_weights["fund_id"].eq(BASE_FUND_ID)].copy()
    if base.empty:
        raise ValueError(f"base fund {BASE_FUND_ID} is unavailable")
    base["decision_date"] = pd.to_datetime(base["decision_date"])
    base["effective_date"] = pd.to_datetime(base["effective_date"])
    if base.duplicated(["effective_date", "ticker"]).any():
        raise ValueError("base target key is not unique")
    validated_mapping = validate_ticker_sector_mapping(
        mapping, required_tickers=base["ticker"].unique()
    )
    multiplier_rows = build_sector_multipliers(signals, base, validated_mapping)
    target_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for (decision, effective), group in base.groupby(
        ["decision_date", "effective_date"], sort=True
    ):
        if group["asset_cap"].nunique() != 1 or group["eligible_asset_count"].nunique() != 1:
            raise ValueError("base target has inconsistent cap or eligible count")
        cap = float(group["asset_cap"].iloc[0])
        base_target = group.set_index("ticker")["target_weight"].astype(float).sort_index()
        event_multipliers = multiplier_rows.loc[
            multiplier_rows["effective_date"].eq(effective)
        ]
        augmented, projection_distance = apply_sector_multipliers(
            base_target, validated_mapping, event_multipliers, cap=cap
        )
        active_count = int(event_multipliers["has_active_signal"].sum())
        carried_count = int((
            event_multipliers["has_active_signal"]
            & event_multipliers["signal_age"].fillna(0).astype(int).gt(0)
        ).sum())
        valid, _reason = portfolios.validate_weights(augmented, cap)
        if active_count == 0 and not np.allclose(
            augmented.to_numpy(), base_target.to_numpy(), atol=1e-14, rtol=0.0
        ):
            raise AssertionError("no-signal augmented target differs from base target")
        ticker_sector = validated_mapping.set_index("ticker")["sector"]
        for ticker in base_target.index:
            target_rows.append({
                "decision_date": pd.Timestamp(decision),
                "effective_date": pd.Timestamp(effective),
                "ticker": ticker,
                "sector": ticker_sector.loc[ticker],
                "base_target_weight": float(base_target.loc[ticker]),
                "augmented_target_weight": float(augmented.loc[ticker]),
                "asset_cap": cap,
                "eligible_asset_count": int(group["eligible_asset_count"].iloc[0]),
            })
        audit_rows.append({
            "decision_date": pd.Timestamp(decision),
            "effective_date": pd.Timestamp(effective),
            "fund_id": AUGMENTED_FUND_ID,
            "eligible_asset_count": int(group["eligible_asset_count"].iloc[0]),
            "asset_cap": cap,
            "active_signal_sector_count": active_count,
            "carried_signal_sector_count": carried_count,
            "base_weight_sum": float(base_target.sum()),
            "augmented_weight_sum": float(augmented.sum()),
            "maximum_base_weight": float(base_target.max()),
            "maximum_augmented_weight": float(augmented.max()),
            "l1_target_change": float(np.abs(augmented - base_target).sum()),
            "projection_distance": projection_distance,
            "turnover": np.nan,
            "trading_cost": np.nan,
            "timing_valid": True,
            "constraints_valid": bool(valid),
        })
    targets = pd.DataFrame(target_rows).sort_values(
        ["effective_date", "ticker"], kind="mergesort"
    ).reset_index(drop=True)
    audit = pd.DataFrame(audit_rows, columns=FUSION_REBALANCE_AUDIT_COLUMNS)
    return targets, multiplier_rows, audit


def _growth_and_drawdown(returns: pd.Series) -> tuple[pd.Series, pd.Series]:
    growth = (1.0 + returns.astype(float)).cumprod(skipna=False)
    return growth, growth / growth.cummax() - 1.0


def _augmented_performance_row(returns: pd.DataFrame) -> pd.DataFrame:
    gross = portfolios.performance_metrics(returns["gross_return"], 252)
    net = portfolios.performance_metrics(returns["net_return"], 252)
    rebalance = returns.loc[returns["is_rebalance"]]
    row = {
        "fund_id": AUGMENTED_FUND_ID,
        "universe": "equity",
        "method": AUGMENTED_METHOD,
        "first_live_date": returns["date"].min(),
        "last_date": returns["date"].max(),
        "observations": gross["observations"],
        "periods_per_year": 252,
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
        "fallback_count": 0,
    }
    return pd.DataFrame([row], columns=portfolios.PERFORMANCE_COLUMNS)


def run_augmented_backtest(
    equity_returns: pd.DataFrame,
    targets: pd.DataFrame,
    rebalance_audit: pd.DataFrame,
    *,
    transaction_cost_rate: float = TRANSACTION_COST_RATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Drift and account for the augmented holdings independently of the base."""
    if equity_returns.empty or not equity_returns.index.is_monotonic_increasing:
        raise ValueError("equity return panel must be non-empty and date-sorted")
    if targets.empty:
        raise ValueError("augmented targets must not be empty")
    events = {
        effective: group.copy()
        for effective, group in targets.groupby("effective_date", sort=True)
    }
    first_live_date = min(events)
    current_weights: pd.Series | None = None
    drift_known = True
    return_rows: list[dict[str, Any]] = []
    weight_rows: list[dict[str, Any]] = []
    audit = rebalance_audit.set_index("effective_date").copy()

    for date, realised in equity_returns.loc[first_live_date:].iterrows():
        event = events.get(pd.Timestamp(date))
        is_rebalance = event is not None
        turnover = 0.0
        trading_cost = 0.0
        if event is not None:
            target = event.set_index("ticker")["augmented_target_weight"].astype(float).sort_index()
            is_initial = current_weights is None
            pretrade = None if is_initial else current_weights.copy()
            if not drift_known and not is_initial:
                pretrade = pd.Series(np.nan, index=current_weights.index, dtype=float)
            turnover = portfolios.calculate_turnover(target, pretrade, initial=is_initial)
            trading_cost = transaction_cost_rate * turnover
            union = target.index if pretrade is None else target.index.union(pretrade.index)
            metadata = event.iloc[0]
            for ticker in sorted(union):
                weight_rows.append({
                    "decision_date": metadata["decision_date"],
                    "effective_date": pd.Timestamp(date),
                    "fund_id": AUGMENTED_FUND_ID,
                    "universe": "equity",
                    "method": AUGMENTED_METHOD,
                    "ticker": ticker,
                    "target_weight": float(target.get(ticker, 0.0)),
                    "pretrade_weight": 0.0 if pretrade is None else float(pretrade.get(ticker, 0.0)),
                    "asset_cap": float(metadata["asset_cap"]),
                    "eligible_asset_count": int(metadata["eligible_asset_count"]),
                    "solver_success": True,
                    "fallback_used": False,
                })
            current_weights = target.copy()
            drift_known = True
            audit.loc[pd.Timestamp(date), "turnover"] = turnover
            audit.loc[pd.Timestamp(date), "trading_cost"] = trading_cost

        if current_weights is None:
            continue
        held_returns = realised.reindex(current_weights.index)
        missing = held_returns.isna() | ~np.isfinite(held_returns.to_numpy(dtype=float))
        if not drift_known and not is_rebalance:
            gross_return = np.nan
            net_return = np.nan
        elif missing.any():
            gross_return = np.nan
            net_return = np.nan
            drift_known = False
        else:
            gross_return, current_weights = portfolios.drift_weights(current_weights, held_returns)
            net_return = portfolios.apply_trading_cost(
                gross_return, trading_cost, is_rebalance=is_rebalance
            )
        return_rows.append({
            "date": pd.Timestamp(date),
            "fund_id": AUGMENTED_FUND_ID,
            "universe": "equity",
            "method": AUGMENTED_METHOD,
            "periods_per_year": 252,
            "gross_return": gross_return,
            "turnover": turnover,
            "trading_cost": trading_cost,
            "net_return": net_return,
            "is_rebalance": is_rebalance,
        })

    returns = pd.DataFrame(return_rows)
    returns["growth_gross"], returns["drawdown_gross"] = _growth_and_drawdown(
        returns["gross_return"]
    )
    returns["growth_net"], returns["drawdown_net"] = _growth_and_drawdown(
        returns["net_return"]
    )
    returns = returns[portfolios.FUND_RETURN_COLUMNS]
    weights = pd.DataFrame(weight_rows, columns=portfolios.FUND_WEIGHT_COLUMNS)
    weights = weights.sort_values(
        ["effective_date", "ticker"], kind="mergesort"
    ).reset_index(drop=True)
    audit = audit.reset_index()[FUSION_REBALANCE_AUDIT_COLUMNS].sort_values(
        "effective_date", kind="mergesort"
    ).reset_index(drop=True)
    if audit[["turnover", "trading_cost"]].isna().any().any():
        raise AssertionError("a fusion rebalance was not reached by the return panel")
    return returns, weights, _augmented_performance_row(returns), audit


def build_fusion_comparison(
    base_returns: pd.DataFrame,
    augmented_returns: pd.DataFrame,
) -> pd.DataFrame:
    """Compare base and augmented funds over an exact common date sequence."""
    base = base_returns.loc[base_returns["fund_id"].eq(BASE_FUND_ID)].copy()
    augmented = augmented_returns.loc[
        augmented_returns["fund_id"].eq(AUGMENTED_FUND_ID)
    ].copy()
    base = base.sort_values("date", kind="mergesort").reset_index(drop=True)
    augmented = augmented.sort_values("date", kind="mergesort").reset_index(drop=True)
    if not base["date"].equals(augmented["date"]):
        raise ValueError("base and augmented comparison dates are not identical")
    common_first = base["date"].min()
    common_last = base["date"].max()
    base_net = base["net_return"].astype(float)
    augmented_net = augmented["net_return"].astype(float)
    rows: list[dict[str, Any]] = []
    for role, frame in (("base", base), ("augmented", augmented)):
        gross = portfolios.performance_metrics(frame["gross_return"], 252)
        net = portfolios.performance_metrics(frame["net_return"], 252)
        rebalances = frame.loc[frame["is_rebalance"]]
        differences = frame["net_return"].astype(float) - base_net
        tracking_error = float(differences.std(ddof=1) * np.sqrt(252))
        correlation = float(frame["net_return"].astype(float).corr(base_net))
        rows.append({
            "fund_id": frame["fund_id"].iloc[0],
            "role": role,
            "common_first_date": common_first,
            "common_last_date": common_last,
            "observations": gross["observations"],
            "cumulative_return_gross": gross["cumulative_return"],
            "cumulative_return_net": net["cumulative_return"],
            "annualised_return_gross": gross["annualised_return"],
            "annualised_return_net": net["annualised_return"],
            "annualised_volatility_gross": gross["annualised_volatility"],
            "annualised_volatility_net": net["annualised_volatility"],
            "sharpe_gross": gross["sharpe"],
            "sharpe_net": net["sharpe"],
            "max_drawdown_gross": gross["max_drawdown"],
            "max_drawdown_net": net["max_drawdown"],
            "total_turnover": float(frame["turnover"].sum(min_count=1)),
            "average_rebalance_turnover": float(rebalances["turnover"].mean()),
            "total_trading_cost": float(frame["trading_cost"].sum(min_count=1)),
            "rebalance_count": int(len(rebalances)),
            "tracking_error_versus_base": tracking_error,
            "correlation_with_base": correlation,
        })
    comparison = pd.DataFrame(rows)
    base_row = comparison.loc[comparison["role"].eq("base")].iloc[0]
    delta_metrics = [
        "observations", "cumulative_return_gross", "cumulative_return_net",
        "annualised_return_gross", "annualised_return_net",
        "annualised_volatility_gross", "annualised_volatility_net",
        "sharpe_gross", "sharpe_net", "max_drawdown_gross", "max_drawdown_net",
        "total_turnover", "average_rebalance_turnover", "total_trading_cost",
        "rebalance_count",
    ]
    for metric in delta_metrics:
        comparison[f"delta_{metric}"] = comparison[metric] - base_row[metric]
    return comparison[FUSION_COMPARISON_COLUMNS]


def build_fusion_yearly_comparison(
    base_returns: pd.DataFrame,
    augmented_returns: pd.DataFrame,
) -> pd.DataFrame:
    """Build calendar-year gross, net, volatility, turnover, and cost rows."""
    combined = pd.concat(
        [base_returns.loc[base_returns["fund_id"].eq(BASE_FUND_ID)], augmented_returns],
        ignore_index=True,
    )
    combined["year"] = pd.to_datetime(combined["date"]).dt.year
    rows: list[dict[str, Any]] = []
    for (year, fund_id), group in combined.groupby(["year", "fund_id"], sort=True):
        gross = portfolios.performance_metrics(group["gross_return"], 252)
        net = portfolios.performance_metrics(group["net_return"], 252)
        rows.append({
            "year": int(year),
            "fund_id": fund_id,
            "observations": gross["observations"],
            "cumulative_return_gross": gross["cumulative_return"],
            "cumulative_return_net": net["cumulative_return"],
            "annualised_volatility_gross": gross["annualised_volatility"],
            "annualised_volatility_net": net["annualised_volatility"],
            "total_turnover": float(group["turnover"].sum(min_count=1)),
            "total_trading_cost": float(group["trading_cost"].sum(min_count=1)),
        })
    return pd.DataFrame(rows, columns=FUSION_YEARLY_COLUMNS)


def build_fusion_current_holdings(
    base_fund_weights: pd.DataFrame,
    augmented_weights: pd.DataFrame,
    mapping: pd.DataFrame,
    multipliers: pd.DataFrame,
) -> pd.DataFrame:
    """Return latest base/augmented targets with their contemporaneous sector signal."""
    base = base_fund_weights.loc[base_fund_weights["fund_id"].eq(BASE_FUND_ID)].copy()
    latest = pd.to_datetime(base["effective_date"]).max()
    base = base.loc[pd.to_datetime(base["effective_date"]).eq(latest), ["ticker", "target_weight"]]
    base = base.rename(columns={"target_weight": "base_weight"})
    augmented = augmented_weights.loc[
        pd.to_datetime(augmented_weights["effective_date"]).eq(latest),
        ["ticker", "target_weight"],
    ].rename(columns={"target_weight": "augmented_weight"})
    mapped = validate_ticker_sector_mapping(
        mapping, required_tickers=base["ticker"].unique()
    )
    signal = multipliers.loc[
        pd.to_datetime(multipliers["effective_date"]).eq(latest),
        [
            "sector", "source_date", "signal_age", "trading_z",
            "effective_coverage", "multiplier",
        ],
    ].rename(columns={
        "source_date": "latest_signal_source_date",
        "signal_age": "latest_signal_age",
        "trading_z": "latest_trading_z",
        "effective_coverage": "latest_effective_coverage",
        "multiplier": "latest_multiplier",
    })
    holdings = base.merge(augmented, on="ticker", how="outer", validate="one_to_one")
    holdings = holdings.merge(mapped, on="ticker", how="left", validate="one_to_one")
    holdings = holdings.merge(signal, on="sector", how="left", validate="many_to_one")
    holdings.insert(0, "as_of_date", latest)
    holdings["base_weight"] = holdings["base_weight"].fillna(0.0)
    holdings["augmented_weight"] = holdings["augmented_weight"].fillna(0.0)
    holdings["weight_change"] = holdings["augmented_weight"] - holdings["base_weight"]
    return holdings[FUSION_CURRENT_HOLDINGS_COLUMNS].sort_values(
        "ticker", kind="mergesort"
    ).reset_index(drop=True)


def run_coverage_aware_fusion(
    *,
    equity_returns: pd.DataFrame,
    base_fund_returns: pd.DataFrame,
    base_fund_weights: pd.DataFrame,
    signals: pd.DataFrame,
    mapping: pd.DataFrame,
    transaction_cost_rate: float = TRANSACTION_COST_RATE,
) -> FusionResults:
    """Run the fixed primary overlay and build all non-figure artifacts."""
    targets, multipliers, audit = construct_augmented_targets(
        base_fund_weights, signals, mapping
    )
    returns, weights, metrics, audit = run_augmented_backtest(
        equity_returns,
        targets,
        audit,
        transaction_cost_rate=transaction_cost_rate,
    )
    comparison = build_fusion_comparison(base_fund_returns, returns)
    yearly = build_fusion_yearly_comparison(base_fund_returns, returns)
    holdings = build_fusion_current_holdings(
        base_fund_weights, weights, mapping, multipliers
    )
    return FusionResults(
        fund_returns=returns,
        fund_weights=weights,
        performance_metrics=metrics,
        sector_multipliers=multipliers,
        rebalance_audit=audit,
        comparison=comparison,
        yearly_comparison=yearly,
        current_holdings=holdings,
    )


def generate_fusion_figures(
    base_fund_returns: pd.DataFrame,
    augmented_returns: pd.DataFrame,
    multipliers: pd.DataFrame,
    *,
    growth_path: str | Path,
    drawdown_path: str | Path,
    activity_path: str | Path,
) -> None:
    """Generate the three fixed, source-labelled fusion figures with matplotlib."""
    base = base_fund_returns.loc[base_fund_returns["fund_id"].eq(BASE_FUND_ID)].copy()
    augmented = augmented_returns.copy()
    base = base.sort_values("date", kind="mergesort").reset_index(drop=True)
    augmented = augmented.sort_values("date", kind="mergesort").reset_index(drop=True)
    if not base["date"].equals(augmented["date"]):
        raise ValueError("figure inputs do not share identical dates")
    first = pd.Timestamp(base["date"].min()).date().isoformat()
    last = pd.Timestamp(base["date"].max()).date().isoformat()
    source_note = "Source: official Project B data; precomputed walk-forward outputs."

    growth_path = Path(growth_path)
    drawdown_path = Path(drawdown_path)
    activity_path = Path(activity_path)
    for path in (growth_path, drawdown_path, activity_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.plot(base["date"], base["growth_gross"], label="Base gross", color="#2455A4", lw=1.8)
    ax.plot(base["date"], base["growth_net"], label="Base net", color="#2455A4", lw=1.4, ls="--")
    ax.plot(augmented["date"], augmented["growth_gross"], label="Augmented gross", color="#D05A35", lw=1.8)
    ax.plot(augmented["date"], augmented["growth_net"], label="Augmented net", color="#D05A35", lw=1.4, ls="--")
    ax.set_title(f"Growth of $1: Equity Risk Parity Fusion\nOOS {first} to {last}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of $1")
    ax.grid(alpha=0.25)
    ax.legend(ncol=2, frameon=False)
    fig.text(0.01, 0.01, source_note, fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(growth_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(base["date"], base["drawdown_net"], label="Base net", color="#2455A4", lw=1.7)
    ax.plot(augmented["date"], augmented["drawdown_net"], label="Augmented net", color="#D05A35", lw=1.7)
    ax.axhline(0.0, color="#333333", lw=0.8)
    ax.set_title(f"Net Drawdown: Equity Risk Parity Fusion\nOOS {first} to {last}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.text(0.01, 0.01, source_note, fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(drawdown_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    activity = multipliers.sort_values(["sector", "effective_date"], kind="mergesort")
    sectors = sorted(activity["sector"].unique())
    positions = {sector: position for position, sector in enumerate(sectors)}
    active = activity.loc[activity["has_active_signal"]]
    inactive = activity.loc[~activity["has_active_signal"]]
    fig, ax = plt.subplots(figsize=(12, max(6.2, 0.48 * len(sectors))))
    ax.scatter(
        inactive["effective_date"], inactive["sector"].map(positions),
        marker="x", s=20, linewidths=0.8, color="#B5B5B5",
        label="Missing signal / multiplier 1.0",
    )
    points = ax.scatter(
        active["effective_date"], active["sector"].map(positions),
        c=active["multiplier"], cmap="RdBu", vmin=MULTIPLIER_LOWER,
        vmax=MULTIPLIER_UPPER, s=36, edgecolor="#333333", linewidth=0.25,
        label="Active signal",
    )
    ax.set_yticks(range(len(sectors)), labels=sectors)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("Coverage-Aware Sector Multipliers at Rebalance Dates")
    ax.set_xlabel("Target effective date")
    ax.set_ylabel("Sector")
    ax.grid(axis="x", alpha=0.2)
    ax.legend(loc="upper left", frameon=False)
    colorbar = fig.colorbar(points, ax=ax, pad=0.02)
    colorbar.set_label("Multiplier (active signals)")
    fig.text(0.01, 0.01, source_note, fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(activity_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
