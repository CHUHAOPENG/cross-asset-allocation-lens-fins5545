"""Synthetic tests for isolated VADER scoring and causal sector sentiment."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import vaderSentiment.vaderSentiment as vs

from src.sentiment import (
    MODELS,
    SECTOR_INDEX_COLUMNS,
    SIGNAL_COLUMNS,
    TICKER_DAY_COLUMNS,
    aggregate_ticker_day,
    build_finance_vader_analyzer,
    build_lagged_trading_signal,
    build_plain_vader_analyzer,
    build_sector_sentiment_index,
    causal_expanding_z,
    derive_sector_membership,
    load_finance_lexicon,
    score_distinct_titles,
    score_mapped_headlines,
)


LEXICON_PATH = Path(__file__).resolve().parents[1] / "resources/finance_vader_lexicon.csv"


def test_plain_and_finance_analyzers_are_isolated_deterministic_and_collision_wins() -> None:
    lexicon = load_finance_lexicon(LEXICON_PATH)
    special_before = dict(vs.SPECIAL_CASES)
    boosters_before = dict(vs.BOOSTER_DICT)
    plain = build_plain_vader_analyzer()
    finance = build_finance_vader_analyzer(lexicon)

    plain_collision_before = plain.lexicon["litigation"]
    finance_collision = finance.lexicon["litigation"]
    assert finance_collision == pytest.approx(-2.0)
    assert finance_collision != plain_collision_before
    sentence = "The company reported an earnings beat."
    finance_first = finance.polarity_scores(sentence)["compound"]
    plain_middle = plain.polarity_scores(sentence)["compound"]
    finance_second = finance.polarity_scores(sentence)["compound"]
    plain_after = plain.polarity_scores("The firm faces litigation.")["compound"]
    assert finance_first == finance_second
    assert finance_first != plain_middle
    assert plain.lexicon["litigation"] == plain_collision_before
    assert finance.lexicon["litigation"] == pytest.approx(-2.0)
    assert plain_after == build_plain_vader_analyzer().polarity_scores(
        "The firm faces litigation."
    )["compound"]
    assert vs.SPECIAL_CASES == special_before
    assert vs.BOOSTER_DICT == boosters_before


def test_raw_casing_punctuation_booster_and_negation_are_preserved_by_scoring() -> None:
    plain = build_plain_vader_analyzer()
    assert plain.polarity_scores("This is good.")["compound"] != plain.polarity_scores(
        "THIS IS GOOD!!!"
    )["compound"]
    assert plain.polarity_scores("good")["compound"] != plain.polarity_scores(
        "very good"
    )["compound"]
    assert plain.polarity_scores("good")["compound"] > 0.0
    assert plain.polarity_scores("not good")["compound"] < 0.0


class _CountingAnalyzer:
    def __init__(self, multiplier: float) -> None:
        self.multiplier = multiplier
        self.calls: list[str] = []

    def polarity_scores(self, title: str) -> dict[str, float]:
        self.calls.append(title)
        return {"compound": self.multiplier * len(title) / 100.0}


def test_distinct_titles_are_scored_once_and_joined_back_to_every_valid_row() -> None:
    plain = _CountingAnalyzer(1.0)
    finance = _CountingAnalyzer(-1.0)
    analyzers = {"plain_vader": plain, "finance_vader": finance}
    scores = score_distinct_titles(["Same", "Same", "Other"], analyzers)
    assert len(scores) == 2
    assert sorted(plain.calls) == ["Other", "Same"]
    assert sorted(finance.calls) == ["Other", "Same"]

    mapped = pd.DataFrame({
        "mapped_equity_trading_date": pd.to_datetime([
            "2023-01-03", "2023-01-03", "2023-01-04", None,
        ]),
        "ticker": ["AAA", "BBB", "AAA", "AAA"],
        "sector": ["Tech"] * 4,
        "title": ["Same", "Same", "Other", "Same"],
    })
    joined = score_mapped_headlines(mapped, scores)
    assert len(joined) == 3 * 2
    assert set(joined["model"]) == set(MODELS)
    assert joined["compound"].notna().all()


def test_headline_to_ticker_day_and_equal_weight_sector_coverage_missingness() -> None:
    scored = pd.DataFrame({
        "date": pd.to_datetime([
            "2023-01-03", "2023-01-03", "2023-01-03",
            "2023-01-03", "2023-01-03", "2023-01-03",
        ]),
        "ticker": ["AAA", "AAA", "BBB", "AAA", "AAA", "BBB"],
        "sector": ["Tech"] * 6,
        "model": ["plain_vader"] * 3 + ["finance_vader"] * 3,
        "title": ["a", "b", "c", "a", "b", "c"],
        "compound": [0.2, 0.4, -0.2, 0.3, 0.5, -0.1],
    })
    ticker_day = aggregate_ticker_day(scored)
    plain_aaa = ticker_day.loc[
        ticker_day["ticker"].eq("AAA") & ticker_day["model"].eq("plain_vader")
    ].iloc[0]
    assert plain_aaa["headline_count"] == 2
    assert plain_aaa["compound_mean"] == pytest.approx(0.3)
    assert plain_aaa["index_0_100"] == pytest.approx(65.0)

    dates = pd.to_datetime(["2023-01-02", "2023-01-03", "2023-01-04"])
    equity_prices = pd.DataFrame({
        "ticker": ["AAA", "BBB"] * 3,
        "sector": ["Tech", "Tech"] * 3,
    })
    membership = derive_sector_membership(equity_prices)
    returns = pd.DataFrame({
        "date": np.repeat(dates, 2),
        "ticker": ["AAA", "BBB"] * 3,
        "simple_return": [np.nan, np.nan, 0.01, 0.02, 0.01, 0.02],
    })
    index = build_sector_sentiment_index(
        ticker_day, returns, membership, dates, min_periods=2
    )
    assert index.columns.tolist() == SECTOR_INDEX_COLUMNS
    day = index.loc[index["date"].eq(pd.Timestamp("2023-01-03"))]
    assert set(day["observed_ticker_count"]) == {2}
    assert set(day["eligible_ticker_count"]) == {2}
    assert set(day["coverage"]) == {1.0}
    expected_plain = (0.3 + -0.2) / 2.0
    assert day.loc[day["model"].eq("plain_vader"), "compound_mean"].iloc[0] == pytest.approx(
        expected_plain
    )
    missing_day = index.loc[index["date"].eq(pd.Timestamp("2023-01-04"))]
    assert (missing_day["headline_count"] == 0).all()
    assert (missing_day["observed_ticker_count"] == 0).all()
    assert missing_day["compound_mean"].isna().all()
    assert missing_day["index_0_100"].isna().all()
    first_day = index.loc[index["date"].eq(pd.Timestamp("2023-01-02"))]
    assert (first_day["eligible_ticker_count"] == 0).all()
    assert first_day["coverage"].isna().all()


def test_causal_expanding_minimum_and_future_perturbation() -> None:
    rng = np.random.default_rng(3)
    values = pd.Series(rng.normal(size=270))
    baseline = causal_expanding_z(values, min_periods=252)
    altered_values = values.copy()
    altered_values.iloc[260:] += 1000.0
    altered = causal_expanding_z(altered_values, min_periods=252)
    assert baseline["causal_z"].iloc[:251].isna().all()
    assert pd.notna(baseline["causal_z"].iloc[251])
    pd.testing.assert_frame_equal(baseline.iloc[:260], altered.iloc[:260])


def test_one_day_lag_five_day_carry_decay_and_age_six_expiry() -> None:
    dates = pd.bdate_range("2023-01-02", periods=9)
    sector_index = pd.DataFrame({
        "date": dates,
        "sector": "Tech",
        "model": "finance_vader",
        "compound_mean": [np.nan, 0.4] + [np.nan] * 7,
        "coverage": [np.nan, 0.6] + [0.0] * 7,
        "causal_z": [np.nan, 1.5] + [np.nan] * 7,
        "descriptive_full_sample_z": [999.0] * 9,
    })
    signal = build_lagged_trading_signal(sector_index).set_index("effective_date")
    age_zero_date = dates[2]
    assert signal.loc[age_zero_date, "source_date"] == dates[1]
    assert signal.loc[age_zero_date, "signal_age"] == 0
    assert not signal.loc[age_zero_date, "is_carried"]
    assert signal.loc[age_zero_date, "effective_coverage"] == pytest.approx(0.6)
    for age in range(1, 6):
        row = signal.loc[dates[2 + age]]
        assert row["signal_age"] == age
        assert row["is_carried"]
        assert row["effective_coverage"] == pytest.approx(0.6 * (6 - age) / 6)
        assert row["trading_z"] == 1.5
    expired = signal.loc[dates[8]]
    assert pd.isna(expired["signal_age"])
    assert pd.isna(expired["trading_z"])
    assert pd.isna(expired["effective_coverage"])


def test_descriptive_full_sample_z_cannot_enter_trading_signal_and_schemas_are_stable() -> None:
    dates = pd.bdate_range("2023-01-02", periods=4)
    base = pd.DataFrame({
        "date": dates,
        "sector": "Tech",
        "model": "plain_vader",
        "compound_mean": [0.1, 0.2, 0.3, 0.4],
        "coverage": [0.5] * 4,
        "causal_z": [np.nan, 1.0, 2.0, 3.0],
        "descriptive_full_sample_z": [-99.0, -99.0, -99.0, -99.0],
    })
    altered = base.copy()
    altered["descriptive_full_sample_z"] = 99999.0
    first = build_lagged_trading_signal(base)
    second = build_lagged_trading_signal(altered)
    pd.testing.assert_frame_equal(first, second)
    assert first.columns.tolist() == SIGNAL_COLUMNS
    assert not first.duplicated(["effective_date", "sector", "model"]).any()
    assert first.equals(first.sort_values(
        ["effective_date", "sector", "model"], kind="mergesort"
    ).reset_index(drop=True))
    assert TICKER_DAY_COLUMNS == [
        "date", "ticker", "sector", "model", "headline_count",
        "compound_mean", "index_0_100",
    ]
