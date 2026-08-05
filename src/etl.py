"""Deterministic Project B data loading, cleaning, and integrity audits.

All raw data enters through the frozen :mod:`src.data_access` helper.  The
cleaning rules are adapted from the approved Part A foundation; they do not
fill prices, score text, or create an investment signal.
"""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

from src import data_access


SAMPLE_START = pd.Timestamp("2020-01-01")
SAMPLE_END = pd.Timestamp("2023-12-31")
PRICE_KEY = ["ticker", "date"]
AUDIT_COLUMNS = [
    "stage", "universe", "date", "fund_id", "ticker", "check_name",
    "observed_value", "status", "message",
]


class DataIntegrityError(ValueError):
    """Raised when an authorised deterministic rule cannot resolve the data."""


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise DataIntegrityError(f"{label} missing required columns: {missing}")


def _normalise_price_dates(values: pd.Series) -> pd.Series:
    dates = pd.to_datetime(values, errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_convert("UTC").dt.tz_localize(None)
    return dates.dt.normalize()


def _normalise_news_dates(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, errors="coerce", utc=True)


def _missing_or_blank(values: pd.Series) -> pd.Series:
    return values.isna() | values.astype("string").str.strip().eq("")


def _audit_row(
    stage: str,
    universe: str,
    check_name: str,
    observed_value: Any,
    status: str,
    message: str,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "universe": universe,
        "date": pd.NaT,
        "fund_id": "",
        "ticker": "",
        "check_name": check_name,
        "observed_value": observed_value,
        "status": status,
        "message": message,
    }


def _audit_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def _conflicting_price_rows(frame: pd.DataFrame) -> pd.DataFrame:
    duplicated = frame.loc[frame.duplicated(PRICE_KEY, keep=False)]
    if duplicated.empty:
        return duplicated.copy()
    value_columns = [column for column in frame.columns if column not in PRICE_KEY]
    conflicts: list[Any] = []
    for _, group in duplicated.groupby(PRICE_KEY, sort=False, dropna=False):
        if len(group[value_columns].drop_duplicates()) > 1:
            conflicts.extend(group.index.tolist())
    return frame.loc[conflicts].copy() if conflicts else frame.iloc[0:0].copy()


def clean_price_data(raw: pd.DataFrame, dataset: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean one price panel and return it with compact integrity audit rows."""
    if dataset not in {"equity_prices", "crypto_prices"}:
        raise ValueError("dataset must be equity_prices or crypto_prices")
    required = [
        "ticker", "date", "open", "high", "low", "close", "adjClose", "volume",
    ]
    if dataset == "equity_prices":
        required.append("sector")
    _require_columns(raw, required, dataset)

    work = raw.copy(deep=True)
    raw_rows = len(work)
    raw_exact_duplicates = int(work.duplicated().sum())
    work["ticker"] = work["ticker"].astype("string").str.strip()
    work["date"] = _normalise_price_dates(work["date"])

    missing_required = (
        _missing_or_blank(work["ticker"])
        | work["date"].isna()
        | pd.to_numeric(work["adjClose"], errors="coerce").isna()
    )
    missing_required_count = int(missing_required.sum())
    work = work.loc[~missing_required].copy()

    conflicts = _conflicting_price_rows(work)
    if not conflicts.empty:
        raise DataIntegrityError(
            f"{dataset} has {len(conflicts)} conflicting ticker-date rows; "
            "no authoritative resolution rule exists"
        )
    duplicate_key_excess = int(work.duplicated(PRICE_KEY).sum())
    work = work.drop_duplicates(PRICE_KEY, keep="first")

    outside_sample = work["date"].lt(SAMPLE_START) | work["date"].gt(SAMPLE_END)
    outside_sample_count = int(outside_sample.sum())
    work = work.loc[~outside_sample].copy()
    work = work.sort_values(PRICE_KEY, kind="mergesort").reset_index(drop=True)

    adjusted_close = pd.to_numeric(work["adjClose"], errors="coerce").to_numpy(dtype=float)
    nonfinite_adjusted_close = int((~np.isfinite(adjusted_close)).sum())
    if nonfinite_adjusted_close:
        raise DataIntegrityError(
            f"{dataset} has {nonfinite_adjusted_close} non-finite adjusted-close values"
        )
    if work.duplicated(PRICE_KEY).any():
        raise DataIntegrityError(f"{dataset} clean ticker-date key is not unique")

    numeric_columns = ["open", "high", "low", "close", "adjClose", "volume"]
    numeric = work[numeric_columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    nonfinite_numeric_cells = int((~np.isfinite(numeric)).sum())
    rows = [
        _audit_row("etl", dataset, "raw_rows", raw_rows, "pass", "Rows supplied by the official loader."),
        _audit_row("etl", dataset, "clean_rows", len(work), "pass", "Rows after deterministic cleaning and sample cap."),
        _audit_row("etl", dataset, "unique_tickers", work["ticker"].nunique(), "pass", "Distinct cleaned ticker count."),
        _audit_row("etl", dataset, "first_date", work["date"].min(), "pass", "First cleaned observation date."),
        _audit_row("etl", dataset, "last_date", work["date"].max(), "pass", "Last cleaned observation date; not later than 2023-12-31."),
        _audit_row("etl", dataset, "raw_exact_duplicate_rows", raw_exact_duplicates, "pass", "Exact row duplicates observed before cleaning."),
        _audit_row("etl", dataset, "removed_duplicate_key_rows", duplicate_key_excess, "pass", "Only identical ticker-date duplicates may be collapsed."),
        _audit_row("etl", dataset, "removed_missing_required_rows", missing_required_count, "pass", "Ticker, date, and adjusted close are required."),
        _audit_row("etl", dataset, "removed_outside_sample_rows", outside_sample_count, "pass", "Rows outside 2020-01-01 through 2023-12-31 are excluded."),
        _audit_row("etl", dataset, "clean_duplicate_ticker_date_rows", int(work.duplicated(PRICE_KEY).sum()), "pass", "Clean ticker-date keys are unique."),
        _audit_row(
            "etl", dataset, "nonfinite_numeric_cells", nonfinite_numeric_cells,
            "pass" if nonfinite_numeric_cells == 0 else "warning",
            "Non-finite non-key numeric cells are audited; adjusted close is always finite.",
        ),
    ]
    return work, _audit_frame(rows)


def clean_news_headlines(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean headline records without scoring or otherwise analysing their text."""
    required = ["date", "ticker", "sector", "title", "url", "publisher"]
    _require_columns(raw, required, "news_headlines")
    work = raw.copy(deep=True)
    work["_source_order"] = np.arange(len(work))
    raw_rows = len(work)
    work["ticker"] = work["ticker"].astype("string").str.strip()
    work["date"] = _normalise_news_dates(work["date"])
    work["_normalised_date"] = work["date"].dt.normalize()

    missing_required = (
        _missing_or_blank(work["ticker"])
        | work["date"].isna()
        | _missing_or_blank(work["title"])
    )
    missing_required_count = int(missing_required.sum())
    work = work.loc[~missing_required].copy()
    duplicate_key = ["ticker", "_normalised_date", "title"]
    duplicate_excess = int(work.duplicated(duplicate_key).sum())
    work = work.drop_duplicates(duplicate_key, keep="first")

    calendar_date = work["_normalised_date"].dt.tz_localize(None)
    outside_sample = calendar_date.lt(SAMPLE_START) | calendar_date.gt(SAMPLE_END)
    outside_sample_count = int(outside_sample.sum())
    work = work.loc[~outside_sample].copy()
    work = (
        work.sort_values(["ticker", "date", "title", "_source_order"], kind="mergesort")
        .drop(columns=["_normalised_date", "_source_order"])
        .reset_index(drop=True)
    )
    normalised_key = work.assign(_normalised_date=work["date"].dt.normalize())
    if normalised_key.duplicated(["ticker", "_normalised_date", "title"]).any():
        raise DataIntegrityError("news clean ticker-normalised-date-title key is not unique")

    rows = [
        _audit_row("etl", "news_headlines", "raw_rows", raw_rows, "pass", "Rows supplied by the official loader."),
        _audit_row("etl", "news_headlines", "clean_rows", len(work), "pass", "Rows after exact-key cleaning and sample cap."),
        _audit_row("etl", "news_headlines", "unique_tickers", work["ticker"].nunique(), "pass", "Distinct cleaned ticker count."),
        _audit_row("etl", "news_headlines", "first_date", work["date"].min(), "pass", "First retained UTC headline timestamp."),
        _audit_row("etl", "news_headlines", "last_date", work["date"].max(), "pass", "Last retained UTC headline timestamp."),
        _audit_row("etl", "news_headlines", "removed_exact_headline_key_rows", duplicate_excess, "pass", "Exact ticker-normalised-date-title duplicates removed."),
        _audit_row("etl", "news_headlines", "removed_missing_required_rows", missing_required_count, "pass", "Ticker, timestamp, and title are required."),
        _audit_row("etl", "news_headlines", "removed_outside_sample_rows", outside_sample_count, "pass", "Rows outside the common sample are excluded."),
        _audit_row("etl", "news_headlines", "missing_publisher_rows", int(_missing_or_blank(work["publisher"]).sum()), "warning", "Publisher missingness is retained and is not an economic signal."),
    ]
    return work, _audit_frame(rows)


def load_clean_equities(return_audit: bool = False):
    clean, audit = clean_price_data(data_access.load_equity_prices(), "equity_prices")
    return (clean, audit) if return_audit else clean


def load_clean_crypto(return_audit: bool = False):
    clean, audit = clean_price_data(data_access.load_crypto_prices(), "crypto_prices")
    return (clean, audit) if return_audit else clean


def load_clean_news(return_audit: bool = False):
    clean, audit = clean_news_headlines(data_access.load_news_headlines())
    return (clean, audit) if return_audit else clean
