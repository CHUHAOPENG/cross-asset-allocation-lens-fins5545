"""Inherited return features and calendar-safe portfolio input panels.

Returns are always calculated within ticker on native observed dates with no
price filling.  Crypto returns are calculated before any equity-calendar
selection.  This module contains no sentiment scoring or trading signal.
"""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

from src.etl import AUDIT_COLUMNS


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _normalise_native_dates(values: pd.Series) -> pd.Series:
    dates = pd.to_datetime(values, errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_convert("UTC").dt.tz_localize(None)
    return dates.dt.normalize()


def observed_equity_calendar(values: Iterable[Any]) -> pd.DatetimeIndex:
    """Return the sorted unique dates observed in the cleaned equity data."""
    dates = _normalise_native_dates(pd.Series(values))
    return pd.DatetimeIndex(dates.dropna().drop_duplicates().sort_values())


def daily_returns(prices: pd.DataFrame, price_col: str = "adjClose") -> pd.DataFrame:
    """Calculate ticker-isolated simple returns on each ticker's native dates."""
    _require_columns(prices, ["ticker", "date", price_col], "price data")
    work = prices.copy(deep=True)
    work["date"] = _normalise_native_dates(work["date"])
    work = work.sort_values(["ticker", "date"], kind="mergesort").reset_index(drop=True)
    work["simple_return"] = (
        work.groupby("ticker", sort=False)[price_col].pct_change(fill_method=None)
    )
    return work


def align_crypto_returns_to_equity_calendar(
    crypto_returns: pd.DataFrame,
    equity_dates: Iterable[Any],
) -> pd.DataFrame:
    """Select already-computed native crypto returns onto observed equity dates."""
    _require_columns(crypto_returns, ["ticker", "date", "simple_return"], "crypto returns")
    calendar = observed_equity_calendar(equity_dates)
    work = crypto_returns.copy(deep=True)
    work["date"] = _normalise_native_dates(work["date"])
    return (
        work.loc[work["date"].isin(calendar)]
        .sort_values(["ticker", "date"], kind="mergesort")
        .reset_index(drop=True)
    )


def _wide_returns(returns: pd.DataFrame, label: str) -> pd.DataFrame:
    _require_columns(returns, ["date", "ticker", "simple_return"], label)
    if returns.duplicated(["date", "ticker"]).any():
        raise ValueError(f"{label} has duplicate date-ticker rows")
    panel = returns.pivot(index="date", columns="ticker", values="simple_return")
    panel.index = pd.DatetimeIndex(panel.index)
    panel.columns.name = None
    return panel.sort_index().sort_index(axis=1)


def build_return_panels(
    equity_prices: pd.DataFrame,
    crypto_prices: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Build Equity, Crypto, and Combined wide return panels plus audits."""
    equity_returns = daily_returns(equity_prices)
    crypto_returns = daily_returns(crypto_prices)
    equity_panel = _wide_returns(equity_returns, "equity returns")
    crypto_panel = _wide_returns(crypto_returns, "crypto returns")

    overlap = sorted(set(equity_panel.columns).intersection(crypto_panel.columns))
    if overlap:
        raise ValueError(f"equity and crypto ticker labels overlap: {overlap}")
    aligned_crypto = crypto_panel.reindex(equity_panel.index)
    combined_panel = pd.concat([equity_panel, aligned_crypto], axis=1).sort_index(axis=1)
    panels = {
        "equity": equity_panel,
        "crypto": crypto_panel,
        "combined": combined_panel,
    }

    rows: list[dict[str, Any]] = []
    for universe, panel in panels.items():
        values = panel.to_numpy(dtype=float)
        finite_or_missing = np.isfinite(values) | np.isnan(values)
        checks = [
            ("panel_rows", len(panel), "pass", "Observed dates in the wide return panel."),
            ("panel_tickers", panel.shape[1], "pass", "Ticker columns in the wide return panel."),
            ("panel_first_date", panel.index.min(), "pass", "First native or comparison-calendar date."),
            ("panel_last_date", panel.index.max(), "pass", "Last native or comparison-calendar date."),
            ("panel_missing_cells", int(panel.isna().sum().sum()), "warning", "Missing returns are retained and never filled."),
            ("panel_nonfinite_nonmissing_cells", int((~finite_or_missing).sum()), "pass" if finite_or_missing.all() else "fail", "Every non-missing return must be finite."),
            ("duplicate_panel_dates", int(panel.index.duplicated().sum()), "pass", "Return-panel dates are unique."),
        ]
        for check_name, observed_value, status, message in checks:
            rows.append({
                "stage": "features",
                "universe": universe,
                "date": pd.NaT,
                "fund_id": "",
                "ticker": "",
                "check_name": check_name,
                "observed_value": observed_value,
                "status": status,
                "message": message,
            })
    audit = pd.DataFrame(rows, columns=AUDIT_COLUMNS)
    if (audit["status"] == "fail").any():
        raise ValueError("return-panel finite-value audit failed")
    return panels, audit


def assemble_headline_panel(
    headlines: pd.DataFrame,
    equity_dates: Iterable[Any],
) -> pd.DataFrame:
    """Map and assemble raw headline text without scoring it.

    The supplied timestamp contributes only its UTC calendar date.  Each row is
    mapped to the same observed equity date or the next observed equity date.
    Titles remain unchanged and are collected only for later, separately scoped
    sentiment work.
    """
    _require_columns(headlines, ["date", "ticker", "sector", "title"], "headlines")
    work = headlines.copy(deep=True)
    timestamp = pd.to_datetime(work["date"], errors="coerce", utc=True)
    source_date = timestamp.dt.tz_convert("UTC").dt.tz_localize(None).dt.normalize()
    calendar = observed_equity_calendar(equity_dates)
    calendar_values = calendar.to_numpy(dtype="datetime64[ns]")
    source_values = source_date.to_numpy(dtype="datetime64[ns]")
    mapped_values = np.full(len(work), np.datetime64("NaT"), dtype="datetime64[ns]")
    valid = ~pd.isna(source_values)
    positions = np.searchsorted(calendar_values, source_values[valid], side="left")
    within = positions < len(calendar_values)
    source_locations = np.flatnonzero(valid)
    mapped_values[source_locations[within]] = calendar_values[positions[within]]
    work["mapped_equity_trading_date"] = pd.to_datetime(mapped_values)
    work["original_utc_timestamp"] = timestamp
    valid_work = work.loc[work["mapped_equity_trading_date"].notna()].copy()
    grouped = (
        valid_work.groupby(
            ["mapped_equity_trading_date", "ticker", "sector"],
            sort=True,
            dropna=False,
        )["title"]
        .agg(headline_count="size", headline_titles=lambda values: tuple(values.tolist()))
        .reset_index()
    )
    return grouped.sort_values(
        ["mapped_equity_trading_date", "ticker"], kind="mergesort"
    ).reset_index(drop=True)
