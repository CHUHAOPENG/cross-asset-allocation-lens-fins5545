"""Synthetic regression tests for the complete approved Rule A mapping."""
from __future__ import annotations

import pandas as pd

from src.features import RULE_A_LABEL, map_news_rule_a
from src.sentiment import build_lagged_trading_signal


def test_rule_a_same_day_weekend_gap_final_boundary_and_timestamp_preservation() -> None:
    calendar = pd.to_datetime(["2023-01-06", "2023-01-09", "2023-01-10"])
    timestamps = pd.to_datetime([
        "2023-01-06 00:00:00+00:00",
        "2023-01-07 14:15:00+00:00",
        "2023-01-08 03:00:00+00:00",
        "2023-01-11 12:00:00+00:00",
    ])
    headlines = pd.DataFrame({
        "date": timestamps,
        "ticker": ["AAA"] * 4,
        "sector": ["Tech"] * 4,
        "title": ["same", "weekend", "gap", "final"],
    })
    mapped = map_news_rule_a(headlines, calendar).set_index("title")

    assert mapped.loc["same", "mapped_equity_trading_date"] == pd.Timestamp("2023-01-06")
    assert mapped.loc["same", "mapping_status"] == "same_trading_date"
    assert mapped.loc["same", "mapping_delay_calendar_days"] == 0
    assert mapped.loc["weekend", "mapped_equity_trading_date"] == pd.Timestamp("2023-01-09")
    assert mapped.loc["weekend", "mapping_delay_calendar_days"] == 2
    assert mapped.loc["gap", "mapped_equity_trading_date"] == pd.Timestamp("2023-01-09")
    assert mapped.loc["gap", "mapping_delay_calendar_days"] == 1
    assert pd.isna(mapped.loc["final", "mapped_equity_trading_date"])
    assert mapped.loc["final", "mapping_status"] == "unmapped_final_sample_boundary"
    assert mapped.loc["same", "timestamp_time_of_day_status"] == "calendar_date_only_midnight"
    assert mapped.loc["weekend", "timestamp_time_of_day_status"] == "non_midnight_time_unverified"
    assert (mapped["mapping_rule"] == RULE_A_LABEL).all()
    expected = pd.Series(timestamps, index=["same", "weekend", "gap", "final"])
    expected.index.name = "title"
    pd.testing.assert_series_equal(
        mapped["original_utc_timestamp"].sort_index(),
        expected.sort_index().rename("original_utc_timestamp"),
    )


def test_weekend_news_mapped_monday_can_first_trade_tuesday() -> None:
    dates = pd.bdate_range("2023-01-06", periods=4)
    weekend = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-07 12:00:00+00:00"]),
        "ticker": ["AAA"],
        "sector": ["Tech"],
        "title": ["Weekend headline"],
    })
    mapped = map_news_rule_a(weekend, dates)
    assert mapped.loc[0, "mapped_equity_trading_date"] == pd.Timestamp("2023-01-09")

    sector_index = pd.DataFrame({
        "date": dates,
        "sector": "Tech",
        "model": "plain_vader",
        "compound_mean": [0.0, 0.4, float("nan"), float("nan")],
        "coverage": [1.0, 0.6, 0.0, 0.0],
        "causal_z": [float("nan"), 1.25, float("nan"), float("nan")],
        "descriptive_full_sample_z": [99.0, 99.0, 99.0, 99.0],
    })
    signal = build_lagged_trading_signal(sector_index).set_index("effective_date")
    assert pd.isna(signal.loc[pd.Timestamp("2023-01-09"), "trading_z"])
    assert signal.loc[pd.Timestamp("2023-01-10"), "source_date"] == pd.Timestamp("2023-01-09")
    assert signal.loc[pd.Timestamp("2023-01-10"), "trading_z"] == 1.25
