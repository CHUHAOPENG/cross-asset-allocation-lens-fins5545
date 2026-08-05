"""Synthetic tests for inherited ETL, returns, and calendar behaviour."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.etl import DataIntegrityError, clean_news_headlines, clean_price_data
from src.features import build_return_panels, daily_returns


def _price_rows(
    ticker: str,
    dates: pd.DatetimeIndex,
    values: list[float],
    *,
    sector: str | None = None,
) -> pd.DataFrame:
    frame = pd.DataFrame({
        "ticker": ticker,
        "date": dates,
        "open": values,
        "high": np.asarray(values) + 1.0,
        "low": np.asarray(values) - 1.0,
        "close": values,
        "adjClose": values,
        "volume": 100,
    })
    if sector is not None:
        frame["sector"] = sector
    return frame


def test_daily_returns_are_ticker_isolated_and_never_fill_missing_prices() -> None:
    dates = pd.date_range("2023-01-01", periods=4, freq="D")
    prices = pd.concat([
        _price_rows("AAA", dates, [100.0, 110.0, np.nan, 121.0]),
        _price_rows("BBB", dates, [50.0, 55.0, 60.5, 66.55]),
    ], ignore_index=True)
    result = daily_returns(prices)
    aaa = result.loc[result["ticker"].eq("AAA"), "simple_return"].reset_index(drop=True)
    bbb = result.loc[result["ticker"].eq("BBB"), "simple_return"].reset_index(drop=True)
    assert np.isnan(aaa.iloc[0])
    assert aaa.iloc[1] == pytest.approx(0.10)
    assert np.isnan(aaa.iloc[2])
    assert np.isnan(aaa.iloc[3])
    assert np.isnan(bbb.iloc[0])
    assert bbb.iloc[1:].to_numpy() == pytest.approx(np.full(3, 0.10))


def test_crypto_returns_remain_native_before_equity_calendar_selection() -> None:
    crypto_dates = pd.date_range("2023-01-06", periods=5, freq="D")
    equity_dates = pd.bdate_range("2023-01-06", "2023-01-10")
    equity = _price_rows("AAA", equity_dates, [100.0, 101.0, 102.0], sector="Tech")
    crypto = _price_rows("BTC-USD", crypto_dates, [100.0, 110.0, 121.0, 133.1, 146.41])
    panels, _audit = build_return_panels(equity, crypto)

    assert pd.Timestamp("2023-01-07") in panels["crypto"].index
    assert panels["combined"].index.equals(panels["equity"].index)
    assert panels["combined"].loc[pd.Timestamp("2023-01-09"), "BTC-USD"] == pytest.approx(0.10)
    assert panels["combined"].loc[pd.Timestamp("2023-01-09"), "BTC-USD"] != pytest.approx(
        133.1 / 100.0 - 1.0
    )


def test_price_cleaning_drops_identical_duplicate_and_caps_sample() -> None:
    dates = pd.to_datetime(["2023-12-31", "2024-01-01"])
    raw = _price_rows("BTC-USD", dates, [100.0, 101.0])
    raw = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    clean, audit = clean_price_data(raw, "crypto_prices")
    assert len(clean) == 1
    assert clean["date"].max() == pd.Timestamp("2023-12-31")
    removed = audit.loc[audit["check_name"].eq("removed_duplicate_key_rows"), "observed_value"]
    assert int(removed.iloc[0]) == 1


def test_price_cleaning_rejects_conflicting_duplicate_key() -> None:
    row = _price_rows("BTC-USD", pd.DatetimeIndex(["2023-01-01"]), [100.0])
    conflict = row.copy()
    conflict["adjClose"] = 999.0
    with pytest.raises(DataIntegrityError, match="conflicting"):
        clean_price_data(pd.concat([row, conflict], ignore_index=True), "crypto_prices")


def test_news_cleaning_uses_exact_normalised_date_title_key() -> None:
    raw = pd.DataFrame({
        "date": pd.to_datetime([
            "2023-01-02 01:00:00+00:00",
            "2023-01-02 02:00:00+00:00",
            "2023-01-02 03:00:00+00:00",
        ]),
        "ticker": ["AAA", "AAA", "AAA"],
        "sector": ["Tech", "Tech", "Tech"],
        "title": ["Same headline", "Same headline", "Different headline"],
        "url": ["u1", "u2", "u3"],
        "publisher": [None, None, "p"],
    })
    clean, _audit = clean_news_headlines(raw)
    assert clean["title"].tolist() == ["Same headline", "Different headline"]
