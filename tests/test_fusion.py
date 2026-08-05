"""Synthetic causality, projection, drift, accounting, and output tests for fusion."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.run_part_b import ORIGINAL_12_SUBSET_HASHES, _original_fund_subset_sha256
from src import fusion, portfolios


ROOT = Path(__file__).resolve().parents[1]


def _mapping() -> pd.DataFrame:
    return pd.DataFrame({
        "ticker": ["AAA", "BBB", "CCC", "DDD"],
        "sector": ["Alpha", "Alpha", "Beta", "Beta"],
    })


def _base_weights() -> pd.DataFrame:
    rows = []
    events = [
        (pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")),
        (pd.Timestamp("2023-01-05"), pd.Timestamp("2023-01-06")),
    ]
    targets = ([0.25, 0.25, 0.25, 0.25], [0.30, 0.20, 0.25, 0.25])
    for (decision, effective), values in zip(events, targets, strict=True):
        for ticker, weight in zip(_mapping()["ticker"], values, strict=True):
            rows.append({
                "decision_date": decision,
                "effective_date": effective,
                "fund_id": fusion.BASE_FUND_ID,
                "universe": "equity",
                "method": "risk_parity",
                "ticker": ticker,
                "target_weight": weight,
                "pretrade_weight": 0.0,
                "asset_cap": 0.35,
                "eligible_asset_count": 4,
                "solver_success": True,
                "fallback_used": False,
            })
    return pd.DataFrame(rows, columns=portfolios.FUND_WEIGHT_COLUMNS)


def _signals() -> pd.DataFrame:
    rows = []
    specs = [
        ("2023-01-03", "2023-01-02", "Alpha", 0, 2.0, 1.0),
        ("2023-01-03", None, "Beta", None, np.nan, np.nan),
        ("2023-01-06", "2023-01-05", "Alpha", 0, -1.0, 0.6),
        ("2023-01-06", "2023-01-03", "Beta", 1, 1.5, 0.4),
    ]
    for effective, source, sector, age, z_score, coverage in specs:
        rows.append({
            "effective_date": pd.Timestamp(effective),
            "source_date": pd.Timestamp(source) if source else pd.NaT,
            "sector": sector,
            "model": fusion.SENTIMENT_MODEL,
            "source_compound_mean": z_score,
            "source_causal_z": z_score,
            "signal_age": age,
            "is_carried": age not in (None, 0),
            "source_coverage": coverage,
            "effective_coverage": coverage,
            "trading_z": z_score,
            "descriptive_full_sample_z": 99999.0,
        })
        plain = rows[-1].copy()
        plain["model"] = "plain_vader"
        plain["trading_z"] = -99999.0
        plain["descriptive_full_sample_z"] = -99999.0
        rows.append(plain)
    return pd.DataFrame(rows)


def _equity_returns() -> pd.DataFrame:
    dates = pd.bdate_range("2023-01-03", "2023-01-10")
    return pd.DataFrame({
        "AAA": [0.10, 0.01, 0.00, -0.02, 0.01, 0.00],
        "BBB": [0.00, 0.02, 0.01, 0.00, -0.01, 0.01],
        "CCC": [-0.04, 0.00, 0.02, 0.01, 0.00, -0.01],
        "DDD": [0.00, -0.01, 0.00, 0.02, 0.01, 0.00],
    }, index=dates)


def test_multiplier_formula_clipping_and_missing_signal() -> None:
    bounded, multiplier = fusion.calculate_sector_multiplier(9.0, 1.0)
    assert bounded == 2.0
    assert multiplier == pytest.approx(1.20)
    bounded, multiplier = fusion.calculate_sector_multiplier(-9.0, 1.0)
    assert bounded == -2.0
    assert multiplier == pytest.approx(0.80)
    bounded, multiplier = fusion.calculate_sector_multiplier(1.5, 0.4)
    assert bounded == 1.5
    assert multiplier == pytest.approx(1.06)
    bounded, multiplier = fusion.calculate_sector_multiplier(np.nan, 0.5)
    assert np.isnan(bounded) and multiplier == 1.0
    bounded, multiplier = fusion.calculate_sector_multiplier(1.0, np.nan)
    assert np.isnan(bounded) and multiplier == 1.0


def test_signal_selection_enforces_age_timing_and_ignores_plain_and_descriptive() -> None:
    first = fusion.select_finance_signals(
        _signals(),
        decision_date=pd.Timestamp("2023-01-02"),
        effective_date=pd.Timestamp("2023-01-03"),
        sectors=["Alpha", "Beta"],
    )
    alpha = first.set_index("sector").loc["Alpha"]
    assert alpha["source_date"] == pd.Timestamp("2023-01-02")
    assert int(alpha["signal_age"]) == 0
    assert alpha["trading_z"] == 2.0

    second = fusion.select_finance_signals(
        _signals(),
        decision_date=pd.Timestamp("2023-01-05"),
        effective_date=pd.Timestamp("2023-01-06"),
        sectors=["Alpha", "Beta"],
    )
    carried = second.set_index("sector").loc["Beta"]
    assert carried["source_date"] < pd.Timestamp("2023-01-05")
    assert int(carried["signal_age"]) == 1

    altered = _signals().copy()
    altered.loc[altered["model"].eq("plain_vader"), "trading_z"] = 1e12
    altered["descriptive_full_sample_z"] = -1e12
    unchanged = fusion.select_finance_signals(
        altered,
        decision_date=pd.Timestamp("2023-01-05"),
        effective_date=pd.Timestamp("2023-01-06"),
        sectors=["Alpha", "Beta"],
    )
    pd.testing.assert_frame_equal(second, unchanged)


def test_signal_selection_rejects_future_source_date() -> None:
    future = _signals().copy()
    mask = future["model"].eq(fusion.SENTIMENT_MODEL) & future["sector"].eq("Alpha")
    future.loc[mask & future["effective_date"].eq(pd.Timestamp("2023-01-03")), "source_date"] = pd.Timestamp("2023-01-03")
    with pytest.raises(ValueError, match="after the portfolio decision"):
        fusion.select_finance_signals(
            future,
            decision_date=pd.Timestamp("2023-01-02"),
            effective_date=pd.Timestamp("2023-01-03"),
            sectors=["Alpha", "Beta"],
        )


def test_mapping_validation_and_no_signal_target_identity() -> None:
    conflict = pd.concat([
        _mapping(), pd.DataFrame({"ticker": ["AAA"], "sector": ["Beta"]}),
    ], ignore_index=True)
    with pytest.raises(ValueError, match="more than one sector"):
        fusion.validate_ticker_sector_mapping(conflict)

    base = pd.Series(0.25, index=_mapping()["ticker"])
    neutral = pd.DataFrame({"sector": ["Alpha", "Beta"], "multiplier": [1.0, 1.0]})
    target, distance = fusion.apply_sector_multipliers(
        base, _mapping(), neutral, cap=0.35
    )
    pd.testing.assert_series_equal(base, target)
    assert distance == 0.0


def test_projected_targets_are_feasible_deterministic_and_causal() -> None:
    first_targets, first_multipliers, _audit = fusion.construct_augmented_targets(
        _base_weights(), _signals(), _mapping()
    )
    second_targets, second_multipliers, _audit = fusion.construct_augmented_targets(
        _base_weights(), _signals(), _mapping()
    )
    pd.testing.assert_frame_equal(first_targets, second_targets)
    pd.testing.assert_frame_equal(first_multipliers, second_multipliers)
    groups = first_targets.groupby("effective_date")
    assert groups["augmented_target_weight"].sum().to_numpy() == pytest.approx(
        np.ones(groups.ngroups), abs=1e-10
    )
    assert (
        first_targets["augmented_target_weight"]
        <= first_targets["asset_cap"] + 1e-10
    ).all()

    perturbed = _signals().copy()
    future = perturbed["effective_date"].eq(pd.Timestamp("2023-01-06"))
    perturbed.loc[future & perturbed["model"].eq(fusion.SENTIMENT_MODEL), "trading_z"] *= -100.0
    altered_targets, _multipliers, _audit = fusion.construct_augmented_targets(
        _base_weights(), perturbed, _mapping()
    )
    baseline_early = first_targets.loc[
        first_targets["effective_date"].eq(pd.Timestamp("2023-01-03"))
    ].reset_index(drop=True)
    altered_early = altered_targets.loc[
        altered_targets["effective_date"].eq(pd.Timestamp("2023-01-03"))
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(baseline_early, altered_early)


def test_augmented_return_independent_drift_turnover_and_cost_reconcile() -> None:
    targets, _multipliers, audit = fusion.construct_augmented_targets(
        _base_weights(), _signals(), _mapping()
    )
    returns, weights, _metrics, audit = fusion.run_augmented_backtest(
        _equity_returns(), targets, audit
    )
    first_date = pd.Timestamp("2023-01-03")
    first_target = weights.loc[
        weights["effective_date"].eq(first_date)
    ].set_index("ticker")["target_weight"]
    realised = _equity_returns().loc[first_date]
    expected_augmented = float(first_target @ realised)
    base_target = _base_weights().loc[
        _base_weights()["effective_date"].eq(first_date)
    ].set_index("ticker")["target_weight"]
    base_return = float(base_target @ realised)
    first_return = returns.loc[returns["date"].eq(first_date)].iloc[0]
    assert first_return["gross_return"] == pytest.approx(expected_augmented)
    assert first_return["gross_return"] != pytest.approx(base_return)
    assert first_return["turnover"] == 1.0
    assert first_return["trading_cost"] == pytest.approx(0.001)
    assert first_return["net_return"] == pytest.approx(
        (1.0 - 0.001) * (1.0 + expected_augmented) - 1.0
    )

    drifted = first_target.copy()
    for date in pd.bdate_range("2023-01-03", "2023-01-05"):
        _gross, drifted = portfolios.drift_weights(drifted, _equity_returns().loc[date])
    second_date = pd.Timestamp("2023-01-06")
    second = weights.loc[weights["effective_date"].eq(second_date)].set_index("ticker")
    assert second["pretrade_weight"].sort_index().to_numpy() == pytest.approx(
        drifted.sort_index().to_numpy()
    )
    expected_turnover = portfolios.calculate_turnover(
        second["target_weight"], second["pretrade_weight"]
    )
    second_return = returns.loc[returns["date"].eq(second_date)].iloc[0]
    assert second_return["turnover"] == pytest.approx(expected_turnover)
    assert second_return["trading_cost"] == pytest.approx(0.001 * expected_turnover)
    assert audit.loc[audit["effective_date"].eq(second_date), "turnover"].iloc[0] == pytest.approx(
        expected_turnover
    )


def test_comparison_requires_identical_dates_and_has_locked_schemas() -> None:
    targets, multipliers, audit = fusion.construct_augmented_targets(
        _base_weights(), _signals(), _mapping()
    )
    augmented, weights, _metrics, audit = fusion.run_augmented_backtest(
        _equity_returns(), targets, audit
    )
    base = augmented.copy()
    base["fund_id"] = fusion.BASE_FUND_ID
    comparison = fusion.build_fusion_comparison(base, augmented)
    yearly = fusion.build_fusion_yearly_comparison(base, augmented)
    holdings = fusion.build_fusion_current_holdings(
        _base_weights(), weights, _mapping(), multipliers
    )
    assert comparison.columns.tolist() == fusion.FUSION_COMPARISON_COLUMNS
    assert yearly.columns.tolist() == fusion.FUSION_YEARLY_COLUMNS
    assert holdings.columns.tolist() == fusion.FUSION_CURRENT_HOLDINGS_COLUMNS
    assert comparison["common_first_date"].nunique() == 1
    assert comparison["common_last_date"].nunique() == 1
    with pytest.raises(ValueError, match="dates are not identical"):
        fusion.build_fusion_comparison(base.iloc[:-1], augmented)


def test_generated_outputs_have_exactly_13_funds_and_preserve_original_text() -> None:
    paths = {
        "fund_returns": ROOT / "results/data/fund_returns.csv",
        "fund_weights": ROOT / "results/data/fund_weights.csv",
        "performance_metrics": ROOT / "results/tables/performance_metrics.csv",
    }
    returns = pd.read_csv(paths["fund_returns"])
    weights = pd.read_csv(paths["fund_weights"])
    metrics = pd.read_csv(paths["performance_metrics"])
    expected = {
        portfolios.fund_identifier(universe, method)
        for universe in ("equity", "crypto", "combined")
        for method in portfolios.METHODS
    } | {fusion.AUGMENTED_FUND_ID}
    assert returns.columns.tolist() == portfolios.FUND_RETURN_COLUMNS
    assert weights.columns.tolist() == portfolios.FUND_WEIGHT_COLUMNS
    assert metrics.columns.tolist() == portfolios.PERFORMANCE_COLUMNS
    assert set(returns["fund_id"]) == expected
    assert set(weights["fund_id"]) == expected
    assert set(metrics["fund_id"]) == expected
    for name, expected_hash in ORIGINAL_12_SUBSET_HASHES.items():
        assert _original_fund_subset_sha256(paths[name]) == expected_hash
