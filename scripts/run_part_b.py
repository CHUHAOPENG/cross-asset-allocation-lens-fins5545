"""Reproduce the Project B data foundation and twelve OOS portfolio funds.

Run from the project root:

    python scripts/run_part_b.py

This interaction deliberately produces no sentiment, fusion, figure, report,
or Streamlit artifact.
"""
from __future__ import annotations

import os
import pathlib
import sys
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import data_access, etl, features, portfolios  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUTS = {
    "fund_returns": ROOT / "results/data/fund_returns.csv",
    "fund_weights": ROOT / "results/data/fund_weights.csv",
    "performance_metrics": ROOT / "results/tables/performance_metrics.csv",
    "solver_audit": ROOT / "results/tables/solver_audit.csv",
    "portfolio_data_audit": ROOT / "results/tables/portfolio_data_audit.csv",
}


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", float_format="%.16g")


def _track_official_loader_source() -> tuple[list[dict[str, str]], Any]:
    """Wrap the frozen fetch function only to record which official path worked."""
    attempts: list[dict[str, str]] = []
    original_fetch = data_access._fetch

    def tracked_fetch(url: str) -> bytes:
        try:
            payload = original_fetch(url)
        except Exception as exc:
            attempts.append({"source": url, "status": f"failed: {type(exc).__name__}"})
            raise
        attempts.append({"source": url, "status": "success"})
        return payload

    data_access._fetch = tracked_fetch
    return attempts, original_fetch


def _actual_source(attempts: list[dict[str, str]]) -> str:
    successes = [item["source"] for item in attempts if item["status"] == "success"]
    if successes:
        return successes[-1]
    configured = os.environ.get("FINS_DATA_ZIP", data_access.DATA_ZIP_URL)
    return f"{configured} (official loader cache; fetch not repeated in this process)"


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


def validate_outputs(
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


def main() -> None:
    attempts, original_fetch = _track_official_loader_source()
    try:
        equities, equity_audit = etl.load_clean_equities(return_audit=True)
        crypto, crypto_audit = etl.load_clean_crypto(return_audit=True)
        _news, news_audit = etl.load_clean_news(return_audit=True)
    finally:
        data_access._fetch = original_fetch

    source = _actual_source(attempts)
    panels, feature_audit = features.build_return_panels(equities, crypto)
    engine = portfolios.run_all_funds(panels)
    summary = validate_outputs(engine, panels)
    combined_audit = pd.concat(
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

    _write_csv(engine.fund_returns, OUTPUTS["fund_returns"])
    _write_csv(engine.fund_weights, OUTPUTS["fund_weights"])
    _write_csv(engine.performance_metrics, OUTPUTS["performance_metrics"])
    _write_csv(engine.solver_audit, OUTPUTS["solver_audit"])
    _write_csv(combined_audit[etl.AUDIT_COLUMNS], OUTPUTS["portfolio_data_audit"])

    print(f"official data source: {source}")
    print(
        "outputs: "
        f"funds={summary['funds']} return_rows={summary['return_rows']} "
        f"weight_rows={summary['weight_rows']}"
    )
    print(
        "audits: "
        f"fallbacks={summary['fallbacks']} "
        f"constraint_violations={summary['constraint_violations']}"
    )
    for universe, panel in panels.items():
        print(
            f"{universe}: {panel.index.min().date()} to {panel.index.max().date()} "
            f"rows={len(panel)} tickers={panel.shape[1]}"
        )


if __name__ == "__main__":
    main()
