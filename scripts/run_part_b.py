"""Reproduce the 13 OOS funds, causal sentiment, fusion outputs, and figures.

Run from the project root:

    python scripts/run_part_b.py

This runner does not implement report prose or Streamlit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import csv
import os
import pathlib
import platform
import subprocess
import sys
from typing import Any, Iterable

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import app_utils, data_access, etl, features, fusion, portfolios, sentiment  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent.parent
LEXICON_PATH = ROOT / "resources/finance_vader_lexicon.csv"
OUTPUTS = {
    "fund_returns": ROOT / "results/data/fund_returns.csv",
    "fund_weights": ROOT / "results/data/fund_weights.csv",
    "sector_sentiment_index": ROOT / "results/data/sector_sentiment_index.csv",
    "ticker_day_sentiment": ROOT / "results/data/ticker_day_sentiment.csv",
    "sector_sentiment_signal": ROOT / "results/data/sector_sentiment_signal.csv",
    "fusion_sector_multipliers": ROOT / "results/data/fusion_sector_multipliers.csv",
    "fund_catalog": ROOT / "results/data/fund_catalog.csv",
    "fund_current_holdings": ROOT / "results/data/fund_current_holdings.csv",
    "performance_metrics": ROOT / "results/tables/performance_metrics.csv",
    "solver_audit": ROOT / "results/tables/solver_audit.csv",
    "portfolio_data_audit": ROOT / "results/tables/portfolio_data_audit.csv",
    "news_mapping_audit": ROOT / "results/tables/news_mapping_audit.csv",
    "sentiment_data_audit": ROOT / "results/tables/sentiment_data_audit.csv",
    "sentiment_model_comparison": ROOT / "results/tables/sentiment_model_comparison.csv",
    "finance_lexicon_audit": ROOT / "results/tables/finance_lexicon_audit.csv",
    "fusion_rebalance_audit": ROOT / "results/tables/fusion_rebalance_audit.csv",
    "fusion_comparison": ROOT / "results/tables/fusion_comparison.csv",
    "fusion_yearly_comparison": ROOT / "results/tables/fusion_yearly_comparison.csv",
    "fusion_current_holdings": ROOT / "results/tables/fusion_current_holdings.csv",
    "fusion_growth_of_one": ROOT / "results/figures/fusion_growth_of_one.png",
    "fusion_drawdown": ROOT / "results/figures/fusion_drawdown.png",
    "fusion_sector_multiplier_activity": ROOT / "results/figures/fusion_sector_multiplier_activity.png",
    "run_manifest": ROOT / "results/tables/run_manifest.csv",
}
FROZEN_ANALYTIC_HASHES_PATH = ROOT / "resources/interaction_004_analytic_hashes.csv"
ORIGINAL_12_SUBSET_HASHES = {
    "fund_returns": "709322f5158707667a220dccb30c1713032264d4378d0c8de412693a3d432756",
    "fund_weights": "8f9c45fb2e20bea0f3353d0a830100c60b15c2c1a746790be39a63c395f872b7",
    "performance_metrics": "a1687e1de010ffb8b4349c46dbbc9b8aa94c110bf98e08817d03ef20f2aa7945",
}
ORIGINAL_FUND_IDS = {
    portfolios.fund_identifier(universe, method)
    for universe in ("equity", "crypto", "combined")
    for method in portfolios.METHODS
}
FIGURE_OUTPUT_NAMES = (
    "fusion_growth_of_one",
    "fusion_drawdown",
    "fusion_sector_multiplier_activity",
)


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", float_format="%.16g")


def _file_sha256(path: pathlib.Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _original_fund_subset_sha256(path: pathlib.Path) -> str:
    """Hash header plus original-fund rows while preserving their exact CSV text."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines:
        raise AssertionError(f"empty fund output: {path}")
    header = next(csv.reader([lines[0]]))
    try:
        fund_index = header.index("fund_id")
    except ValueError as exc:
        raise AssertionError(f"fund_id is missing from {path}") from exc
    retained = [lines[0]]
    for line in lines[1:]:
        fields = next(csv.reader([line]))
        if fields[fund_index] in ORIGINAL_FUND_IDS:
            retained.append(line)
    return sha256("".join(retained).encode("utf-8")).hexdigest()


def verify_frozen_interaction_004_analytics() -> int:
    """Require every frozen Interaction 004 CSV/PNG to remain byte-identical."""
    if not FROZEN_ANALYTIC_HASHES_PATH.is_file():
        raise AssertionError(f"missing frozen analytical hash file: {FROZEN_ANALYTIC_HASHES_PATH}")
    frozen = pd.read_csv(FROZEN_ANALYTIC_HASHES_PATH, dtype=str)
    if frozen.columns.tolist() != ["path", "sha256"]:
        raise AssertionError("frozen analytical hash schema must be path,sha256")
    if len(frozen) != 20 or frozen["path"].duplicated().any():
        raise AssertionError("frozen analytical hash file must contain 20 unique paths")
    for row in frozen.itertuples(index=False):
        path = ROOT / row.path
        if not path.is_file():
            raise AssertionError(f"frozen analytical artifact is missing: {row.path}")
        actual = _file_sha256(path)
        if actual != row.sha256:
            raise AssertionError(
                f"frozen Interaction 004 artifact changed: {row.path}; "
                f"expected {row.sha256}, got {actual}"
            )
    return len(frozen)


def _track_official_loader_source() -> tuple[list[dict[str, str]], Any]:
    """Wrap the frozen fetch function to record official source and bytes hash."""
    attempts: list[dict[str, str]] = []
    original_fetch = data_access._fetch

    def tracked_fetch(url: str) -> bytes:
        try:
            payload = original_fetch(url)
        except Exception as exc:
            attempts.append({
                "source": url,
                "status": f"failed: {type(exc).__name__}",
                "sha256": "",
            })
            raise
        attempts.append({
            "source": url,
            "status": "success",
            "sha256": sha256(payload).hexdigest(),
        })
        return payload

    data_access._fetch = tracked_fetch
    return attempts, original_fetch


def _actual_source(attempts: list[dict[str, str]]) -> str:
    successes = [item["source"] for item in attempts if item["status"] == "success"]
    if successes:
        return successes[-1]
    configured = os.environ.get("FINS_DATA_ZIP", data_access.DATA_ZIP_URL)
    return f"{configured} (official loader cache; fetch not repeated in this process)"


def _actual_source_zip_sha256(attempts: list[dict[str, str]]) -> str:
    hashes = [item["sha256"] for item in attempts if item["status"] == "success"]
    return hashes[-1] if hashes else "unavailable; source ZIP bytes were not exposed in this run"


def _source_audit(source: str, attempts: list[dict[str, str]]) -> pd.DataFrame:
    messages = "; ".join(f"{item['source']} [{item['status']}]" for item in attempts)
    return pd.DataFrame([{
        "stage": "source",
        "universe": "all",
        "date": pd.NaT,
        "fund_id": "",
        "ticker": "",
        "check_name": "official_data_source",
        "observed_value": source,
        "status": "pass",
        "message": messages or "Loaded through the frozen official helper cache.",
    }], columns=etl.AUDIT_COLUMNS)


def validate_portfolio_outputs(
    engine: portfolios.FundEngineResults,
    panels: dict[str, pd.DataFrame],
) -> dict[str, int]:
    """Run independent schema, key, calendar, constraint, and accounting checks."""
    returns = engine.fund_returns
    weights = engine.fund_weights
    metrics = engine.performance_metrics
    solver = engine.solver_audit
    expected_funds = {
        portfolios.fund_identifier(universe, method)
        for universe in ("equity", "crypto", "combined")
        for method in portfolios.METHODS
    }
    if returns.columns.tolist() != portfolios.FUND_RETURN_COLUMNS:
        raise AssertionError("fund_returns schema mismatch")
    if weights.columns.tolist() != portfolios.FUND_WEIGHT_COLUMNS:
        raise AssertionError("fund_weights schema mismatch")
    if metrics.columns.tolist() != portfolios.PERFORMANCE_COLUMNS:
        raise AssertionError("performance_metrics schema mismatch")
    if set(returns["fund_id"]) != expected_funds or set(metrics["fund_id"]) != expected_funds:
        raise AssertionError("the exact twelve fund identifiers were not produced")
    if returns.duplicated(["date", "fund_id"]).any():
        raise AssertionError("duplicate date-fund return row")
    if weights.duplicated(["effective_date", "fund_id", "ticker"]).any():
        raise AssertionError("duplicate effective-date-fund-ticker weight row")

    groups = weights.groupby(["effective_date", "fund_id"], sort=False)
    target_sums = groups["target_weight"].sum()
    if not np.allclose(target_sums.to_numpy(), 1.0, atol=1e-8, rtol=0.0):
        raise AssertionError("target weights do not sum to one")
    if (weights["target_weight"] < -1e-10).any():
        raise AssertionError("target weight violates the lower bound")
    if (weights["target_weight"] > weights["asset_cap"] + 1e-8).any():
        raise AssertionError("target weight violates the dynamic cap")
    if (weights["effective_date"] <= weights["decision_date"]).any():
        raise AssertionError("a target is effective on or before its decision date")

    for universe in ("equity", "combined"):
        observed = set(returns.loc[returns["universe"].eq(universe), "date"])
        if not observed.issubset(set(panels["equity"].index)):
            raise AssertionError(f"{universe} output is not on the equity calendar")
    crypto_dates = returns.loc[returns["universe"].eq("crypto"), "date"]
    if not set(crypto_dates).issubset(set(panels["crypto"].index)):
        raise AssertionError("crypto output is not on the native crypto calendar")
    if not crypto_dates.dt.weekday.ge(5).any():
        raise AssertionError("crypto output unexpectedly omits every weekend")

    first_live = metrics.set_index("fund_id")["first_live_date"]
    first_decision = weights.groupby("fund_id")["decision_date"].min()
    if not (first_live > first_decision).all():
        raise AssertionError("a fund starts on or before its first decision date")
    live_solver = solver.loc[solver["status"].isin(["ok", "fallback"])]
    required_windows = live_solver["universe"].map(
        {key: value["initial_window"] for key, value in portfolios.UNIVERSE_CONFIG.items()}
    )
    if (live_solver["complete_history_rows"] < required_windows).any():
        raise AssertionError("a live target uses fewer rows than its initial window")
    if (live_solver["fallback_used"] & live_solver["solver_success"]).any():
        raise AssertionError("fallback use is inconsistent with solver success")

    non_rebalance = returns.loc[~returns["is_rebalance"]]
    if not np.allclose(
        non_rebalance["net_return"], non_rebalance["gross_return"],
        atol=1e-14, rtol=0.0, equal_nan=True,
    ):
        raise AssertionError("non-rebalance net return differs from gross return")
    rebalance = returns.loc[returns["is_rebalance"]]
    expected_net = (1.0 - rebalance["trading_cost"]) * (1.0 + rebalance["gross_return"]) - 1.0
    if not np.allclose(
        rebalance["net_return"], expected_net,
        atol=1e-14, rtol=0.0, equal_nan=True,
    ):
        raise AssertionError("rebalance-date net accounting mismatch")
    if returns["date"].max() > pd.Timestamp("2023-12-31"):
        raise AssertionError("output exceeds the approved sample end")
    return {
        "funds": len(expected_funds),
        "return_rows": len(returns),
        "weight_rows": len(weights),
        "fallbacks": int(live_solver["fallback_used"].sum()),
        "constraint_violations": 0,
    }


def validate_integrated_fund_outputs(
    engine: portfolios.FundEngineResults,
    fund_returns: pd.DataFrame,
    fund_weights: pd.DataFrame,
    performance_metrics: pd.DataFrame,
) -> dict[str, int]:
    """Verify the intentional append while preserving every original fund row."""
    expected = ORIGINAL_FUND_IDS | {fusion.AUGMENTED_FUND_ID}
    if fund_returns.columns.tolist() != portfolios.FUND_RETURN_COLUMNS:
        raise AssertionError("integrated fund_returns schema mismatch")
    if fund_weights.columns.tolist() != portfolios.FUND_WEIGHT_COLUMNS:
        raise AssertionError("integrated fund_weights schema mismatch")
    if performance_metrics.columns.tolist() != portfolios.PERFORMANCE_COLUMNS:
        raise AssertionError("integrated performance_metrics schema mismatch")
    if set(fund_returns["fund_id"]) != expected:
        raise AssertionError("fund_returns does not contain exactly 13 fund identifiers")
    if set(fund_weights["fund_id"]) != expected:
        raise AssertionError("fund_weights does not contain exactly 13 fund identifiers")
    if set(performance_metrics["fund_id"]) != expected:
        raise AssertionError("performance_metrics does not contain exactly 13 fund identifiers")
    if fund_returns.duplicated(["date", "fund_id"]).any():
        raise AssertionError("duplicate integrated date-fund return row")
    if fund_weights.duplicated(["effective_date", "fund_id", "ticker"]).any():
        raise AssertionError("duplicate integrated weight key")

    original_returns = fund_returns.loc[
        fund_returns["fund_id"].isin(ORIGINAL_FUND_IDS)
    ].reset_index(drop=True)
    original_weights = fund_weights.loc[
        fund_weights["fund_id"].isin(ORIGINAL_FUND_IDS)
    ].reset_index(drop=True)
    original_metrics = performance_metrics.loc[
        performance_metrics["fund_id"].isin(ORIGINAL_FUND_IDS)
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(engine.fund_returns, original_returns)
    pd.testing.assert_frame_equal(engine.fund_weights, original_weights)
    pd.testing.assert_frame_equal(engine.performance_metrics, original_metrics)

    augmented_returns = fund_returns.loc[
        fund_returns["fund_id"].eq(fusion.AUGMENTED_FUND_ID)
    ]
    augmented_weights = fund_weights.loc[
        fund_weights["fund_id"].eq(fusion.AUGMENTED_FUND_ID)
    ]
    groups = augmented_weights.groupby("effective_date", sort=False)
    if not np.allclose(groups["target_weight"].sum(), 1.0, atol=1e-8, rtol=0.0):
        raise AssertionError("augmented target weights do not sum to one")
    if (augmented_weights["target_weight"] < -1e-10).any():
        raise AssertionError("augmented target violates long-only")
    if (
        augmented_weights["target_weight"]
        > augmented_weights["asset_cap"] + 1e-8
    ).any():
        raise AssertionError("augmented target violates its recorded cap")
    if not augmented_weights["solver_success"].all():
        raise AssertionError("a deterministic fusion projection is not marked successful")
    if augmented_weights["fallback_used"].any():
        raise AssertionError("an unrecorded fusion projection fallback was used")
    metric = performance_metrics.loc[
        performance_metrics["fund_id"].eq(fusion.AUGMENTED_FUND_ID)
    ].iloc[0]
    if int(metric["periods_per_year"]) != 252 or int(metric["fallback_count"]) != 0:
        raise AssertionError("augmented metrics use incorrect annualisation or fallback count")
    return {
        "funds": len(expected),
        "return_rows": len(fund_returns),
        "weight_rows": len(fund_weights),
        "augmented_return_rows": len(augmented_returns),
        "augmented_rebalances": augmented_weights["effective_date"].nunique(),
    }


def validate_fusion_outputs(
    result: fusion.FusionResults,
    base_returns: pd.DataFrame,
) -> dict[str, int | float]:
    """Independently validate timing, bounds, periods, accounting, and schemas."""
    if result.sector_multipliers.columns.tolist() != fusion.FUSION_SECTOR_MULTIPLIER_COLUMNS:
        raise AssertionError("fusion multiplier schema mismatch")
    if result.rebalance_audit.columns.tolist() != fusion.FUSION_REBALANCE_AUDIT_COLUMNS:
        raise AssertionError("fusion rebalance audit schema mismatch")
    if result.comparison.columns.tolist() != fusion.FUSION_COMPARISON_COLUMNS:
        raise AssertionError("fusion comparison schema mismatch")
    if result.yearly_comparison.columns.tolist() != fusion.FUSION_YEARLY_COLUMNS:
        raise AssertionError("fusion yearly schema mismatch")
    if result.current_holdings.columns.tolist() != fusion.FUSION_CURRENT_HOLDINGS_COLUMNS:
        raise AssertionError("fusion current holdings schema mismatch")

    multiplier = result.sector_multipliers
    if set(multiplier["model"]) != {fusion.SENTIMENT_MODEL}:
        raise AssertionError("fusion used a non-finance sentiment model")
    if not multiplier["multiplier"].between(
        fusion.MULTIPLIER_LOWER, fusion.MULTIPLIER_UPPER
    ).all():
        raise AssertionError("fusion multiplier lies outside locked bounds")
    inactive = multiplier.loc[~multiplier["has_active_signal"]]
    if not inactive["multiplier"].eq(1.0).all():
        raise AssertionError("missing signal did not produce multiplier one")
    active = multiplier.loc[multiplier["has_active_signal"]]
    if (active["source_date"] > active["decision_date"]).any():
        raise AssertionError("future sentiment entered a target")
    age_zero = active.loc[active["signal_age"].eq(0)]
    if not age_zero["source_date"].eq(age_zero["decision_date"]).all():
        raise AssertionError("age-zero signal source is not the decision date")
    carried = active.loc[active["signal_age"].gt(0)]
    if not (carried["source_date"] < carried["decision_date"]).all():
        raise AssertionError("carried signal is not earlier than the decision date")
    if not result.rebalance_audit["timing_valid"].all():
        raise AssertionError("fusion timing audit contains a failure")
    if not result.rebalance_audit["constraints_valid"].all():
        raise AssertionError("fusion constraint audit contains a failure")

    base = base_returns.loc[base_returns["fund_id"].eq(fusion.BASE_FUND_ID)].copy()
    augmented = result.fund_returns
    if not base["date"].reset_index(drop=True).equals(
        augmented["date"].reset_index(drop=True)
    ):
        raise AssertionError("base and augmented OOS dates differ")
    non_rebalance = augmented.loc[~augmented["is_rebalance"]]
    if not np.allclose(
        non_rebalance["gross_return"], non_rebalance["net_return"],
        atol=1e-14, rtol=0.0, equal_nan=True,
    ):
        raise AssertionError("augmented non-rebalance net accounting mismatch")
    rebalance = augmented.loc[augmented["is_rebalance"]]
    expected_net = (
        (1.0 - rebalance["trading_cost"])
        * (1.0 + rebalance["gross_return"])
        - 1.0
    )
    if not np.allclose(
        rebalance["net_return"], expected_net,
        atol=1e-14, rtol=0.0, equal_nan=True,
    ):
        raise AssertionError("augmented rebalance net accounting mismatch")
    return {
        "multiplier_rows": len(multiplier),
        "active_signal_rows": int(multiplier["has_active_signal"].sum()),
        "carried_signal_rows": int((
            multiplier["has_active_signal"] & multiplier["signal_age"].fillna(0).gt(0)
        ).sum()),
        "minimum_multiplier": float(multiplier["multiplier"].min()),
        "maximum_multiplier": float(multiplier["multiplier"].max()),
    }


def validate_sentiment_outputs(
    clean_news: pd.DataFrame,
    mapped: pd.DataFrame,
    scored_headlines: pd.DataFrame,
    ticker_day: pd.DataFrame,
    sector_index: pd.DataFrame,
    signals: pd.DataFrame,
    sentiment_audit: pd.DataFrame,
    equity_dates: pd.DatetimeIndex,
) -> dict[str, int]:
    """Validate Rule A reconciliation, missingness, causality, schemas, and keys."""
    if sector_index.columns.tolist() != sentiment.SECTOR_INDEX_COLUMNS:
        raise AssertionError("sector_sentiment_index schema mismatch")
    if ticker_day.columns.tolist() != sentiment.TICKER_DAY_COLUMNS:
        raise AssertionError("ticker_day_sentiment schema mismatch")
    if signals.columns.tolist() != sentiment.SIGNAL_COLUMNS:
        raise AssertionError("sector_sentiment_signal schema mismatch")
    if set(sector_index["model"]) != set(sentiment.MODELS):
        raise AssertionError("sector index model values are not exact")
    if set(ticker_day["model"]) != set(sentiment.MODELS):
        raise AssertionError("ticker-day model values are not exact")
    if len(mapped) != 146836:
        raise AssertionError("Rule A clean headline count differs from approved Part A")
    status_counts = mapped["mapping_status"].value_counts()
    if int(status_counts.get("unmapped_final_sample_boundary", 0)) != 6:
        raise AssertionError("Rule A final-boundary count differs from approved Part A")
    valid_mapped = int(mapped["mapped_equity_trading_date"].notna().sum())
    if len(scored_headlines) != valid_mapped * len(sentiment.MODELS):
        raise AssertionError("final-boundary rows entered scoring or a valid row was lost")

    original = clean_news[["ticker", "title", "date"]].copy()
    original["date"] = pd.to_datetime(original["date"], utc=True)
    original = original.sort_values(["ticker", "title", "date"], kind="mergesort").reset_index(drop=True)
    preserved = mapped[["ticker", "title", "original_utc_timestamp"]].rename(
        columns={"original_utc_timestamp": "date"}
    )
    preserved = preserved.sort_values(["ticker", "title", "date"], kind="mergesort").reset_index(drop=True)
    pd.testing.assert_frame_equal(original, preserved)

    if ticker_day.duplicated(["date", "ticker", "model"]).any():
        raise AssertionError("duplicate ticker-day sentiment key")
    if sector_index.duplicated(["date", "sector", "model"]).any():
        raise AssertionError("duplicate sector-index key")
    if signals.duplicated(["effective_date", "sector", "model"]).any():
        raise AssertionError("duplicate trading-signal key")
    coverage = sector_index["coverage"].dropna()
    if ((coverage < 0.0) | (coverage > 1.0)).any():
        raise AssertionError("sector coverage lies outside [0, 1]")
    missing_compound = sector_index["compound_mean"].isna()
    if sector_index.loc[missing_compound, "index_0_100"].notna().any():
        raise AssertionError("missing sector news was converted to neutral 50")
    ages = signals["signal_age"].dropna().astype(int)
    if not ages.between(0, 5).all():
        raise AssertionError("signal age outside zero through five")
    active = signals.loc[signals["trading_z"].notna()].copy()
    if not np.allclose(
        active["trading_z"], active["source_causal_z"], atol=0.0, rtol=0.0
    ):
        raise AssertionError("trading_z is not the causal source-day z-score")
    date_position = {date: position for position, date in enumerate(equity_dates)}
    for row in active.itertuples(index=False):
        expected_age = date_position[row.effective_date] - date_position[row.source_date] - 1
        if int(row.signal_age) != expected_age:
            raise AssertionError("signal lag/carry age is inconsistent with equity dates")
    if sentiment_audit["status"].eq("fail").any():
        raise AssertionError("sentiment data audit contains a failure")
    return {
        "mapping_rows": len(mapped),
        "mapped_rows": valid_mapped,
        "unmapped_rows": int(status_counts.get("unmapped_final_sample_boundary", 0)),
        "ticker_day_rows": len(ticker_day),
        "sector_index_rows": len(sector_index),
        "missing_sector_rows": int(missing_compound.sum()),
        "active_signal_rows": len(active),
    }


def _package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def _locked_parameter_manifest_rows() -> list[tuple[str, str]]:
    return [
        ("portfolio.initial_window.equity", "252"),
        ("portfolio.initial_window.crypto", "365"),
        ("portfolio.initial_window.combined", "252"),
        ("portfolio.rebalance", "last observed calendar-month date; effective next observed date"),
        ("portfolio.asset_cap", "min(0.35, 5 / eligible_asset_count)"),
        ("portfolio.covariance", "sample covariance; 10% diagonal shrinkage"),
        ("portfolio.maximum_sharpe_mean", "expanding arithmetic mean; 50% cross-sectional shrinkage"),
        ("portfolio.solver", "SciPy SLSQP; maxiter=1000; ftol=1e-10"),
        ("portfolio.weight_tolerances", "sum=1e-8; lower=1e-10; cap=1e-8"),
        ("portfolio.risk_free_rate", "0"),
        ("portfolio.cost_rate", "0.001 times one-way turnover"),
        ("portfolio.annualisation", "Equity=252; Crypto=365; Combined=252"),
        ("portfolio.methods", ",".join(portfolios.METHODS)),
        ("portfolio.fallback", "previous feasible target else capped equal weight; always logged"),
        ("sentiment.models", ",".join(sentiment.MODELS)),
        ("sentiment.rule_a", features.RULE_A_LABEL),
        ("sentiment.raw_text", "original title unchanged"),
        ("sentiment.finance_lexicon_sha256", sentiment.FINANCE_LEXICON_SHA256),
        ("sentiment.finance_terms", "29 approved; 20 words; 9 phrases; 10 rejected"),
        ("sentiment.aggregation", "headline mean to ticker-day; equal-weight ticker-day mean to sector-day"),
        ("sentiment.coverage", "observed eligible ticker-days / eligible tickers; no-news remains missing"),
        ("sentiment.index_0_100", "50 * (compound + 1)"),
        ("sentiment.causal_z", "expanding by sector/model; min_periods=252; sample std; through source day"),
        ("sentiment.trading_lag", "exactly one observed equity day"),
        ("sentiment.carry", "ages 1-5; age 6 expires"),
        ("sentiment.coverage_decay", "source_coverage * (6 - age) / 6"),
        ("sentiment.full_sample_z", "descriptive only; prohibited from trading_z"),
        ("fusion.fund_id", fusion.AUGMENTED_FUND_ID),
        ("fusion.universe", "equity"),
        ("fusion.method", fusion.AUGMENTED_METHOD),
        ("fusion.base_fund", fusion.BASE_FUND_ID),
        ("fusion.sentiment_model", fusion.SENTIMENT_MODEL),
        ("fusion.signal_join", "signal effective_date equals target effective_date"),
        ("fusion.timing", "source_date <= decision_date; age 0 equals decision_date"),
        ("fusion.tilt_strength", f"{fusion.TILT_STRENGTH:.2f}"),
        ("fusion.z_clip", f"[-{fusion.Z_CLIP:.0f}, {fusion.Z_CLIP:.0f}]"),
        (
            "fusion.multiplier_bounds",
            f"[{fusion.MULTIPLIER_LOWER:.2f}, {fusion.MULTIPLIER_UPPER:.2f}]",
        ),
        ("fusion.missing_signal_multiplier", "1.0"),
        ("fusion.projection", "existing deterministic capped-simplex projection"),
        ("fusion.parameter_selection", "predeclared; not tuned on realised fusion performance"),
        ("app.data_boundary", "committed precomputed results only; no analytical engines or downloads"),
        ("app.performance_default", "net returns"),
        ("app.allocation.buy_and_hold", "initial fund sleeves compound independently without reset"),
        ("app.allocation.monthly_reset", "reset sleeves on first common date of each calendar month"),
        ("app.allocation.extra_cross_fund_cost", "0; disclosed limitation"),
        ("app.allocation.constraints", "2-6 funds; non-negative; sum to 100%; no optimisation"),
    ]


def build_run_manifest(
    *,
    run_timestamp: str,
    git_head_before_run: str,
    official_source: str,
    source_zip_sha256: str,
    output_frames: dict[str, pd.DataFrame],
    figure_names: Iterable[str] = (),
) -> pd.DataFrame:
    """Build the two-column environment, parameter, and output provenance manifest."""
    rows: list[tuple[str, str]] = [
        ("run_timestamp_utc", run_timestamp),
        ("project_name", "Cross-Asset Allocation Lens"),
        ("git_head_before_run", git_head_before_run),
        ("python_version", platform.python_version()),
        ("package.pandas.version", _package_version("pandas")),
        ("package.numpy.version", _package_version("numpy")),
        ("package.scipy.version", _package_version("scipy")),
        ("package.vaderSentiment.version", _package_version("vaderSentiment")),
        ("package.matplotlib.version", _package_version("matplotlib")),
        ("package.plotly.version", _package_version("plotly")),
        ("official_data_source", official_source),
        ("official_source_zip_sha256", source_zip_sha256),
        ("sample_end_date", "2023-12-31"),
    ]
    rows.extend(_locked_parameter_manifest_rows())
    for name, frame in output_frames.items():
        relative_path = OUTPUTS[name].relative_to(ROOT).as_posix()
        rows.append((f"output.{relative_path}.rows", str(len(frame))))
        rows.append((f"output.{relative_path}.sha256", _file_sha256(OUTPUTS[name])))
    for name in figure_names:
        relative_path = OUTPUTS[name].relative_to(ROOT).as_posix()
        rows.append((f"output.{relative_path}.bytes", str(OUTPUTS[name].stat().st_size)))
        rows.append((f"output.{relative_path}.sha256", _file_sha256(OUTPUTS[name])))
    return pd.DataFrame(rows, columns=["key", "value"])


def main() -> None:
    run_timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    git_head_before_run = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    frozen_analytic_count = verify_frozen_interaction_004_analytics()
    attempts, original_fetch = _track_official_loader_source()
    try:
        equities, equity_audit = etl.load_clean_equities(return_audit=True)
        crypto, crypto_audit = etl.load_clean_crypto(return_audit=True)
        clean_news, news_audit = etl.load_clean_news(return_audit=True)
    finally:
        data_access._fetch = original_fetch

    source = _actual_source(attempts)
    source_zip_hash = _actual_source_zip_sha256(attempts)
    panels, feature_audit = features.build_return_panels(equities, crypto)
    engine = portfolios.run_all_funds(panels)
    portfolio_summary = validate_portfolio_outputs(engine, panels)
    portfolio_audit = pd.concat(
        [
            _source_audit(source, attempts),
            equity_audit,
            crypto_audit,
            news_audit,
            feature_audit,
            engine.portfolio_data_audit,
        ],
        ignore_index=True,
    ).sort_values(
        ["stage", "universe", "date", "fund_id", "ticker", "check_name"],
        kind="mergesort",
        na_position="last",
    ).reset_index(drop=True)

    equity_dates = pd.DatetimeIndex(panels["equity"].index)
    equity_returns = features.daily_returns(equities)
    mapped = features.map_news_rule_a(clean_news, equity_dates)
    finance_lexicon = sentiment.load_finance_lexicon(LEXICON_PATH)
    plain_analyzer = sentiment.build_plain_vader_analyzer()
    finance_analyzer = sentiment.build_finance_vader_analyzer(finance_lexicon)
    valid_titles = mapped.loc[mapped["mapped_equity_trading_date"].notna(), "title"]
    title_scores = sentiment.score_distinct_titles(
        valid_titles,
        analyzers={
            "plain_vader": plain_analyzer,
            "finance_vader": finance_analyzer,
        },
    )
    scored_headlines = sentiment.score_mapped_headlines(mapped, title_scores)
    ticker_day = sentiment.aggregate_ticker_day(scored_headlines)
    membership = sentiment.derive_sector_membership(equities)
    sector_index = sentiment.build_sector_sentiment_index(
        ticker_day,
        equity_returns,
        membership,
        equity_dates,
        min_periods=252,
    )
    signals = sentiment.build_lagged_trading_signal(sector_index, max_carry_age=5)
    finance_audit = sentiment.build_finance_lexicon_audit(
        finance_lexicon, finance_analyzer, LEXICON_PATH
    )
    comparison = sentiment.build_model_comparison(title_scores, sector_index)
    sentiment_audit = sentiment.build_sentiment_data_audit(
        mapped, title_scores, ticker_day, sector_index, signals
    )
    sentiment_summary = validate_sentiment_outputs(
        clean_news,
        mapped,
        scored_headlines,
        ticker_day,
        sector_index,
        signals,
        sentiment_audit,
        equity_dates,
    )

    fusion_result = fusion.run_coverage_aware_fusion(
        equity_returns=panels["equity"],
        base_fund_returns=engine.fund_returns,
        base_fund_weights=engine.fund_weights,
        signals=signals,
        mapping=membership,
        transaction_cost_rate=fusion.TRANSACTION_COST_RATE,
    )
    fusion_summary = validate_fusion_outputs(fusion_result, engine.fund_returns)
    fund_returns = pd.concat(
        [engine.fund_returns, fusion_result.fund_returns], ignore_index=True
    ).sort_values(["date", "fund_id"], kind="mergesort").reset_index(drop=True)
    fund_weights = pd.concat(
        [engine.fund_weights, fusion_result.fund_weights], ignore_index=True
    ).sort_values(
        ["effective_date", "fund_id", "ticker"], kind="mergesort"
    ).reset_index(drop=True)
    performance_metrics = pd.concat(
        [engine.performance_metrics, fusion_result.performance_metrics], ignore_index=True
    ).sort_values("fund_id", kind="mergesort").reset_index(drop=True)
    integrated_summary = validate_integrated_fund_outputs(
        engine, fund_returns, fund_weights, performance_metrics
    )
    fusion.generate_fusion_figures(
        engine.fund_returns,
        fusion_result.fund_returns,
        fusion_result.sector_multipliers,
        growth_path=OUTPUTS["fusion_growth_of_one"],
        drawdown_path=OUTPUTS["fusion_drawdown"],
        activity_path=OUTPUTS["fusion_sector_multiplier_activity"],
    )
    fund_catalog = app_utils.build_fund_catalog(performance_metrics)
    fund_current_holdings = app_utils.build_fund_current_holdings(
        fund_weights, fund_catalog
    )

    mapping_output = mapped.copy()
    mapping_output["original_utc_timestamp"] = mapping_output[
        "original_utc_timestamp"
    ].map(lambda value: value.isoformat() if pd.notna(value) else "")
    output_frames = {
        "fund_returns": fund_returns,
        "fund_weights": fund_weights,
        "sector_sentiment_index": sector_index,
        "ticker_day_sentiment": ticker_day,
        "sector_sentiment_signal": signals,
        "fusion_sector_multipliers": fusion_result.sector_multipliers,
        "fund_catalog": fund_catalog,
        "fund_current_holdings": fund_current_holdings,
        "performance_metrics": performance_metrics,
        "solver_audit": engine.solver_audit,
        "portfolio_data_audit": portfolio_audit[etl.AUDIT_COLUMNS],
        "news_mapping_audit": mapping_output,
        "sentiment_data_audit": sentiment_audit,
        "sentiment_model_comparison": comparison,
        "finance_lexicon_audit": finance_audit,
        "fusion_rebalance_audit": fusion_result.rebalance_audit,
        "fusion_comparison": fusion_result.comparison,
        "fusion_yearly_comparison": fusion_result.yearly_comparison,
        "fusion_current_holdings": fusion_result.current_holdings,
    }
    for name, frame in output_frames.items():
        _write_csv(frame, OUTPUTS[name])

    verified_frozen_count = verify_frozen_interaction_004_analytics()
    if verified_frozen_count != frozen_analytic_count:
        raise AssertionError("frozen analytical artifact count changed during the run")

    for name, expected_hash in ORIGINAL_12_SUBSET_HASHES.items():
        actual_hash = _original_fund_subset_sha256(OUTPUTS[name])
        if actual_hash != expected_hash:
            raise AssertionError(
                f"Interaction 002 original-12 {name} subset changed: "
                f"expected {expected_hash}, got {actual_hash}"
            )

    manifest = build_run_manifest(
        run_timestamp=run_timestamp,
        git_head_before_run=git_head_before_run,
        official_source=source,
        source_zip_sha256=source_zip_hash,
        output_frames=output_frames,
        figure_names=FIGURE_OUTPUT_NAMES,
    )
    _write_csv(manifest, OUTPUTS["run_manifest"])

    print(f"official data source: {source}")
    print(f"official source ZIP SHA-256: {source_zip_hash}")
    print(
        "portfolios: "
        f"base_funds={portfolio_summary['funds']} total_funds={integrated_summary['funds']} "
        f"return_rows={integrated_summary['return_rows']} "
        f"weight_rows={integrated_summary['weight_rows']} "
        f"fallbacks={portfolio_summary['fallbacks']} "
        f"constraint_violations={portfolio_summary['constraint_violations']}"
    )
    mapping_counts = mapped["mapping_status"].value_counts().to_dict()
    print(
        "Rule A: "
        f"rows={sentiment_summary['mapping_rows']} mapped={sentiment_summary['mapped_rows']} "
        f"unmapped={sentiment_summary['unmapped_rows']} statuses={mapping_counts}"
    )
    changed_titles = comparison.loc[
        comparison["metric"].eq("titles_with_changed_compound"), "value"
    ].iloc[0]
    print(
        "sentiment: "
        f"distinct_titles={len(title_scores)} ticker_day_rows={sentiment_summary['ticker_day_rows']} "
        f"sector_index_rows={sentiment_summary['sector_index_rows']} "
        f"missing_sector_rows={sentiment_summary['missing_sector_rows']} "
        f"active_signal_rows={sentiment_summary['active_signal_rows']} "
        f"changed_title_scores={changed_titles}"
    )
    print(
        "fusion: "
        f"multiplier_rows={fusion_summary['multiplier_rows']} "
        f"active_signal_rows={fusion_summary['active_signal_rows']} "
        f"carried_signal_rows={fusion_summary['carried_signal_rows']} "
        f"multiplier_range=[{fusion_summary['minimum_multiplier']:.6f}, "
        f"{fusion_summary['maximum_multiplier']:.6f}] "
        f"augmented_return_rows={integrated_summary['augmented_return_rows']} "
        f"rebalances={integrated_summary['augmented_rebalances']}"
    )
    print(
        "app artifacts: "
        f"catalog_rows={len(fund_catalog)} holding_rows={len(fund_current_holdings)} "
        f"frozen_analytics_verified={verified_frozen_count}"
    )
    print(f"manifest: rows={len(manifest)} path={OUTPUTS['run_manifest'].relative_to(ROOT)}")


if __name__ == "__main__":
    main()
