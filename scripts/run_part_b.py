"""Reproduce the twelve OOS funds and causal sector-sentiment artifacts.

Run from the project root:

    python scripts/run_part_b.py

This runner does not implement fusion, figures, report prose, or Streamlit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import os
import pathlib
import platform
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import data_access, etl, features, portfolios, sentiment  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent.parent
LEXICON_PATH = ROOT / "resources/finance_vader_lexicon.csv"
OUTPUTS = {
    "fund_returns": ROOT / "results/data/fund_returns.csv",
    "fund_weights": ROOT / "results/data/fund_weights.csv",
    "sector_sentiment_index": ROOT / "results/data/sector_sentiment_index.csv",
    "ticker_day_sentiment": ROOT / "results/data/ticker_day_sentiment.csv",
    "sector_sentiment_signal": ROOT / "results/data/sector_sentiment_signal.csv",
    "performance_metrics": ROOT / "results/tables/performance_metrics.csv",
    "solver_audit": ROOT / "results/tables/solver_audit.csv",
    "portfolio_data_audit": ROOT / "results/tables/portfolio_data_audit.csv",
    "news_mapping_audit": ROOT / "results/tables/news_mapping_audit.csv",
    "sentiment_data_audit": ROOT / "results/tables/sentiment_data_audit.csv",
    "sentiment_model_comparison": ROOT / "results/tables/sentiment_model_comparison.csv",
    "finance_lexicon_audit": ROOT / "results/tables/finance_lexicon_audit.csv",
    "run_manifest": ROOT / "results/tables/run_manifest.csv",
}
INTERACTION_002_CORE_HASHES = {
    "fund_returns": "709322f5158707667a220dccb30c1713032264d4378d0c8de412693a3d432756",
    "fund_weights": "8f9c45fb2e20bea0f3353d0a830100c60b15c2c1a746790be39a63c395f872b7",
    "performance_metrics": "a1687e1de010ffb8b4349c46dbbc9b8aa94c110bf98e08817d03ef20f2aa7945",
}


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", float_format="%.16g")


def _file_sha256(path: pathlib.Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    ]


def build_run_manifest(
    *,
    run_timestamp: str,
    git_head_before_run: str,
    official_source: str,
    source_zip_sha256: str,
    output_frames: dict[str, pd.DataFrame],
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
        ("package.nltk.version", _package_version("nltk")),
        ("package.vaderSentiment.version", _package_version("vaderSentiment")),
        ("package.vader.version", _package_version("vader")),
        ("official_data_source", official_source),
        ("official_source_zip_sha256", source_zip_sha256),
        ("sample_end_date", "2023-12-31"),
    ]
    rows.extend(_locked_parameter_manifest_rows())
    for name, frame in output_frames.items():
        relative_path = OUTPUTS[name].relative_to(ROOT).as_posix()
        rows.append((f"output.{relative_path}.rows", str(len(frame))))
        rows.append((f"output.{relative_path}.sha256", _file_sha256(OUTPUTS[name])))
    return pd.DataFrame(rows, columns=["key", "value"])


def main() -> None:
    run_timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    git_head_before_run = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
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

    mapping_output = mapped.copy()
    mapping_output["original_utc_timestamp"] = mapping_output[
        "original_utc_timestamp"
    ].map(lambda value: value.isoformat() if pd.notna(value) else "")
    output_frames = {
        "fund_returns": engine.fund_returns,
        "fund_weights": engine.fund_weights,
        "sector_sentiment_index": sector_index,
        "ticker_day_sentiment": ticker_day,
        "sector_sentiment_signal": signals,
        "performance_metrics": engine.performance_metrics,
        "solver_audit": engine.solver_audit,
        "portfolio_data_audit": portfolio_audit[etl.AUDIT_COLUMNS],
        "news_mapping_audit": mapping_output,
        "sentiment_data_audit": sentiment_audit,
        "sentiment_model_comparison": comparison,
        "finance_lexicon_audit": finance_audit,
    }
    for name, frame in output_frames.items():
        _write_csv(frame, OUTPUTS[name])

    for name, expected_hash in INTERACTION_002_CORE_HASHES.items():
        actual_hash = _file_sha256(OUTPUTS[name])
        if actual_hash != expected_hash:
            raise AssertionError(
                f"Interaction 002 {name} changed: expected {expected_hash}, got {actual_hash}"
            )

    manifest = build_run_manifest(
        run_timestamp=run_timestamp,
        git_head_before_run=git_head_before_run,
        official_source=source,
        source_zip_sha256=source_zip_hash,
        output_frames=output_frames,
    )
    _write_csv(manifest, OUTPUTS["run_manifest"])

    print(f"official data source: {source}")
    print(f"official source ZIP SHA-256: {source_zip_hash}")
    print(
        "portfolios: "
        f"funds={portfolio_summary['funds']} return_rows={portfolio_summary['return_rows']} "
        f"weight_rows={portfolio_summary['weight_rows']} "
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
    print(f"manifest: rows={len(manifest)} path={OUTPUTS['run_manifest'].relative_to(ROOT)}")


if __name__ == "__main__":
    main()
