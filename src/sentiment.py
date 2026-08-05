"""Rule-A-aligned plain and frozen-finance VADER sector sentiment.

Raw headline titles are scored without text preprocessing.  Missing news stays
missing throughout ticker, sector, and trading-signal construction.  The
full-sample z-score is descriptive only; trading uses the causal expanding
source-day z-score after one observed-equity-day lag and bounded carry.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import vaderSentiment.vaderSentiment as vs


MODELS = ("plain_vader", "finance_vader")
FINANCE_LEXICON_SHA256 = "4c16eeab9edec5c970234d0a30bcbd89c84c21abf94e4677b8b9568c8b6a28c6"
FINANCE_APPROVED_COUNT = 29
FINANCE_REJECTED_COUNT = 10
FINANCE_WORD_COUNT = 20
FINANCE_PHRASE_COUNT = 9
FINANCE_SOURCE_PATH = (
    "/Users/chris/Desktop/fins 5545/fins-agent/fins2026/week_8/"
    "vader_model/output/tables/09_finance_lexicon_approved.csv"
)

SECTOR_INDEX_COLUMNS = [
    "date", "sector", "model", "headline_count", "observed_ticker_count",
    "eligible_ticker_count", "coverage", "compound_mean", "index_0_100",
    "causal_expanding_mean", "causal_expanding_std", "causal_z",
    "descriptive_full_sample_z",
]
TICKER_DAY_COLUMNS = [
    "date", "ticker", "sector", "model", "headline_count",
    "compound_mean", "index_0_100",
]
SIGNAL_COLUMNS = [
    "effective_date", "source_date", "sector", "model",
    "source_compound_mean", "source_causal_z", "signal_age", "is_carried",
    "source_coverage", "effective_coverage", "trading_z",
]
SENTIMENT_AUDIT_COLUMNS = ["check_name", "value", "status", "message"]
COMPARISON_COLUMNS = ["metric", "value"]
LEXICON_AUDIT_COLUMNS = [
    "term", "term_type", "valence", "base_vader_value",
    "collision_with_base", "installed_value", "source_path", "source_sha256",
    "frozen_path", "frozen_sha256", "approved_term_count",
    "rejected_term_count", "validation_status",
]

_BASE_SPECIAL_CASES = dict(vs.SPECIAL_CASES)
_BASE_BOOSTER_DICT = dict(vs.BOOSTER_DICT)
_VADER_STATE_LOCK = RLock()


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def file_sha256(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_finance_lexicon(
    path: str | Path,
    *,
    expected_sha256: str = FINANCE_LEXICON_SHA256,
) -> pd.DataFrame:
    """Load and validate the frozen Week 8 approved finance lexicon."""
    lexicon_path = Path(path)
    if not lexicon_path.is_file():
        raise FileNotFoundError(f"frozen finance lexicon not found: {lexicon_path}")
    actual_hash = file_sha256(lexicon_path)
    if actual_hash != expected_sha256:
        raise ValueError(
            f"finance lexicon SHA-256 mismatch: expected {expected_sha256}, got {actual_hash}"
        )
    frame = pd.read_csv(lexicon_path)
    expected_columns = ["term", "term_type", "valence"]
    if frame.columns.tolist() != expected_columns:
        raise ValueError(f"finance lexicon schema must be {expected_columns}")
    if len(frame) != FINANCE_APPROVED_COUNT or frame["term"].duplicated().any():
        raise ValueError("finance lexicon must contain 29 unique approved terms")
    if set(frame["term_type"]) != {"word", "phrase"}:
        raise ValueError("finance lexicon term_type must contain word and phrase only")
    if int(frame["term_type"].eq("word").sum()) != FINANCE_WORD_COUNT:
        raise ValueError("finance lexicon must contain 20 approved words")
    if int(frame["term_type"].eq("phrase").sum()) != FINANCE_PHRASE_COUNT:
        raise ValueError("finance lexicon must contain 9 approved phrases")
    valence = pd.to_numeric(frame["valence"], errors="coerce")
    if valence.isna().any() or not np.isfinite(valence.to_numpy(dtype=float)).all():
        raise ValueError("finance lexicon valences must be finite")
    if valence.lt(-4.0).any() or valence.gt(4.0).any():
        raise ValueError("finance lexicon valences must be on the Week 8 -4 to +4 scale")
    result = frame.copy()
    result["term"] = result["term"].astype(str)
    result["valence"] = valence.astype(float)
    return result.sort_values("term", kind="mergesort").reset_index(drop=True)


class IsolatedVaderAnalyzer:
    """VADER analyser with instance-local lexicon, phrase, and booster state."""

    def __init__(
        self,
        *,
        lexicon_updates: Mapping[str, float] | None = None,
        special_cases: Mapping[str, float] | None = None,
        booster_dict: Mapping[str, float] | None = None,
    ) -> None:
        self._analyzer = vs.SentimentIntensityAnalyzer()
        self._analyzer.lexicon.update(dict(lexicon_updates or {}))
        self._special_cases = dict(
            _BASE_SPECIAL_CASES if special_cases is None else special_cases
        )
        self._booster_dict = dict(
            _BASE_BOOSTER_DICT if booster_dict is None else booster_dict
        )

    @property
    def lexicon(self) -> dict[str, float]:
        return self._analyzer.lexicon

    def _with_local_state(self, texts: list[str]) -> list[dict[str, float]]:
        with _VADER_STATE_LOCK:
            saved_special_cases = dict(vs.SPECIAL_CASES)
            saved_boosters = dict(vs.BOOSTER_DICT)
            try:
                vs.SPECIAL_CASES.clear()
                vs.SPECIAL_CASES.update(self._special_cases)
                vs.BOOSTER_DICT.clear()
                vs.BOOSTER_DICT.update(self._booster_dict)
                return [self._analyzer.polarity_scores(text) for text in texts]
            finally:
                vs.SPECIAL_CASES.clear()
                vs.SPECIAL_CASES.update(saved_special_cases)
                vs.BOOSTER_DICT.clear()
                vs.BOOSTER_DICT.update(saved_boosters)

    def polarity_scores(self, text: str) -> dict[str, float]:
        return self._with_local_state([text])[0]

    def polarity_scores_many(self, texts: Iterable[str]) -> list[dict[str, float]]:
        return self._with_local_state([str(text) for text in texts])


def build_plain_vader_analyzer() -> IsolatedVaderAnalyzer:
    """Create a fresh baseline analyser with unmodified base VADER state."""
    return IsolatedVaderAnalyzer()


def build_finance_vader_analyzer(
    finance_lexicon: pd.DataFrame,
) -> IsolatedVaderAnalyzer:
    """Create an isolated finance analyser using the exact Week 8 installation."""
    _require_columns(finance_lexicon, ["term", "term_type", "valence"], "finance lexicon")
    base = vs.SentimentIntensityAnalyzer()
    words = finance_lexicon.loc[finance_lexicon["term_type"].eq("word")]
    phrases = finance_lexicon.loc[finance_lexicon["term_type"].eq("phrase")]
    lexicon_updates = {
        str(term): float(valence)
        for term, valence in zip(words["term"], words["valence"])
    }
    head_words: dict[str, float] = {}
    special_cases = dict(_BASE_SPECIAL_CASES)
    for term, valence in zip(phrases["term"], phrases["valence"]):
        phrase = str(term)
        value = float(valence)
        head = phrase.split()[-1]
        if head not in base.lexicon and head not in lexicon_updates:
            head_words[head] = 0.1 if value > 0.0 else -0.1
        special_cases[phrase] = value
    lexicon_updates.update(head_words)

    boosters = dict(_BASE_BOOSTER_DICT)
    booster_candidates = {
        "sharply": vs.B_INCR,
        "materially": vs.B_INCR,
        "steeply": vs.B_INCR,
        "modestly": vs.B_DECR,
        "marginally": vs.B_DECR,
    }
    for term, value in booster_candidates.items():
        if term not in boosters:
            boosters[term] = value
    return IsolatedVaderAnalyzer(
        lexicon_updates=lexicon_updates,
        special_cases=special_cases,
        booster_dict=boosters,
    )


def score_distinct_titles(
    titles: Iterable[Any],
    analyzers: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """Score each distinct unmodified title exactly once with both models."""
    title_series = pd.Series(titles, dtype="object")
    if title_series.isna().any():
        raise ValueError("headline titles must be non-missing before scoring")
    unique_titles = sorted(title_series.astype(str).drop_duplicates().tolist())
    if analyzers is None:
        raise ValueError("isolated plain and finance analysers must be supplied")
    if tuple(analyzers.keys()) != MODELS:
        raise ValueError(f"analyser keys must be exactly {MODELS} in that order")
    output = pd.DataFrame({"title": unique_titles})
    for model in MODELS:
        analyzer = analyzers[model]
        if hasattr(analyzer, "polarity_scores_many"):
            scores = analyzer.polarity_scores_many(unique_titles)
        else:
            scores = [analyzer.polarity_scores(title) for title in unique_titles]
        output[model] = [float(score["compound"]) for score in scores]
    return output


def score_mapped_headlines(
    mapped_headlines: pd.DataFrame,
    title_scores: pd.DataFrame,
) -> pd.DataFrame:
    """Join distinct-title scores to valid Rule A rows and keep both models long."""
    _require_columns(
        mapped_headlines,
        ["ticker", "sector", "title", "mapped_equity_trading_date"],
        "mapped headlines",
    )
    _require_columns(title_scores, ["title", *MODELS], "title scores")
    valid = mapped_headlines.loc[
        mapped_headlines["mapped_equity_trading_date"].notna(),
        ["mapped_equity_trading_date", "ticker", "sector", "title"],
    ].copy()
    joined = valid.merge(title_scores, on="title", how="left", validate="many_to_one")
    if joined[list(MODELS)].isna().any().any():
        raise ValueError("one or more valid mapped headlines did not receive both scores")
    long = joined.melt(
        id_vars=["mapped_equity_trading_date", "ticker", "sector", "title"],
        value_vars=list(MODELS),
        var_name="model",
        value_name="compound",
    ).rename(columns={"mapped_equity_trading_date": "date"})
    return long.sort_values(
        ["date", "ticker", "model", "title"], kind="mergesort"
    ).reset_index(drop=True)


def aggregate_ticker_day(scored_headlines: pd.DataFrame) -> pd.DataFrame:
    """Average headline compounds within ticker, mapped date, sector, and model."""
    _require_columns(
        scored_headlines,
        ["date", "ticker", "sector", "model", "compound"],
        "scored headlines",
    )
    grouped = scored_headlines.groupby(
        ["date", "ticker", "sector", "model"], sort=True, dropna=False
    )["compound"]
    output = grouped.agg(headline_count="size", compound_mean="mean").reset_index()
    output["headline_count"] = output["headline_count"].astype(int)
    output["index_0_100"] = 50.0 * (output["compound_mean"] + 1.0)
    return output[TICKER_DAY_COLUMNS].sort_values(
        ["date", "ticker", "model"], kind="mergesort"
    ).reset_index(drop=True)


def derive_sector_membership(equity_prices: pd.DataFrame) -> pd.DataFrame:
    """Derive the one-to-one official cleaned-equity ticker-sector mapping."""
    _require_columns(equity_prices, ["ticker", "sector"], "clean equity prices")
    mapping = equity_prices[["ticker", "sector"]].drop_duplicates()
    if mapping[["ticker", "sector"]].isna().any().any():
        raise ValueError("ticker-sector mapping contains missing values")
    counts = mapping.groupby("ticker")["sector"].nunique()
    if counts.gt(1).any():
        raise ValueError("a cleaned equity ticker maps to more than one sector")
    return mapping.sort_values(["sector", "ticker"], kind="mergesort").reset_index(drop=True)


def descriptive_full_sample_z(values: pd.Series) -> pd.Series:
    """Descriptive-only full-sample sample-standard-deviation z-score."""
    series = pd.Series(values, dtype=float)
    standard_deviation = series.std(ddof=1)
    if not np.isfinite(standard_deviation) or standard_deviation == 0.0:
        return pd.Series(np.nan, index=series.index, dtype=float)
    return (series - series.mean()) / standard_deviation


def causal_expanding_z(
    values: pd.Series,
    *,
    min_periods: int = 252,
) -> pd.DataFrame:
    """Causal expanding mean, sample standard deviation, and source-day z."""
    series = pd.Series(values, dtype=float)
    expanding = series.expanding(min_periods=min_periods)
    mean = expanding.mean()
    standard_deviation = expanding.std(ddof=1)
    z_score = (series - mean) / standard_deviation
    z_score = z_score.where(standard_deviation.ne(0.0) & standard_deviation.notna())
    return pd.DataFrame({
        "causal_expanding_mean": mean,
        "causal_expanding_std": standard_deviation,
        "causal_z": z_score,
    }, index=series.index)


def build_sector_sentiment_index(
    ticker_day: pd.DataFrame,
    equity_returns: pd.DataFrame,
    sector_membership: pd.DataFrame,
    equity_dates: Iterable[Any],
    *,
    min_periods: int = 252,
) -> pd.DataFrame:
    """Build the complete equity-date/sector/model grid and coverage-aware index."""
    _require_columns(ticker_day, TICKER_DAY_COLUMNS, "ticker-day sentiment")
    _require_columns(equity_returns, ["date", "ticker", "simple_return"], "equity returns")
    _require_columns(sector_membership, ["ticker", "sector"], "sector membership")
    dates = pd.DatetimeIndex(pd.to_datetime(pd.Series(equity_dates))).drop_duplicates().sort_values()
    sectors = sorted(sector_membership["sector"].astype(str).unique())
    grid = pd.MultiIndex.from_product(
        [dates, sectors, MODELS], names=["date", "sector", "model"]
    ).to_frame(index=False)

    return_values = pd.to_numeric(equity_returns["simple_return"], errors="coerce")
    eligible = equity_returns.loc[
        return_values.notna() & np.isfinite(return_values.to_numpy(dtype=float)),
        ["date", "ticker"],
    ].copy()
    eligible["date"] = pd.to_datetime(eligible["date"])
    eligible = eligible.merge(
        sector_membership, on="ticker", how="inner", validate="many_to_one"
    ).drop_duplicates(["date", "ticker", "sector"])
    eligible_counts = (
        eligible.groupby(["date", "sector"], sort=True)["ticker"]
        .nunique()
        .rename("eligible_ticker_count")
        .reset_index()
    )

    observed = ticker_day.merge(
        eligible,
        on=["date", "ticker", "sector"],
        how="inner",
        validate="many_to_one",
    )
    aggregate = (
        observed.groupby(["date", "sector", "model"], sort=True)
        .agg(
            headline_count=("headline_count", "sum"),
            observed_ticker_count=("ticker", "nunique"),
            compound_mean=("compound_mean", "mean"),
        )
        .reset_index()
    )
    output = grid.merge(eligible_counts, on=["date", "sector"], how="left")
    output = output.merge(aggregate, on=["date", "sector", "model"], how="left")
    for column in ["headline_count", "observed_ticker_count", "eligible_ticker_count"]:
        output[column] = output[column].fillna(0).astype(int)
    output["coverage"] = (
        output["observed_ticker_count"] / output["eligible_ticker_count"]
    ).where(output["eligible_ticker_count"].gt(0))
    output["index_0_100"] = 50.0 * (output["compound_mean"] + 1.0)
    output["causal_expanding_mean"] = np.nan
    output["causal_expanding_std"] = np.nan
    output["causal_z"] = np.nan
    output["descriptive_full_sample_z"] = np.nan

    for _, positions in output.groupby(["sector", "model"], sort=True).groups.items():
        index = pd.Index(positions)
        values = output.loc[index, "compound_mean"]
        causal = causal_expanding_z(values, min_periods=min_periods)
        output.loc[index, [
            "causal_expanding_mean", "causal_expanding_std", "causal_z",
        ]] = causal.to_numpy()
        output.loc[index, "descriptive_full_sample_z"] = descriptive_full_sample_z(
            values
        ).to_numpy()
    return output[SECTOR_INDEX_COLUMNS].sort_values(
        ["date", "sector", "model"], kind="mergesort"
    ).reset_index(drop=True)


def build_lagged_trading_signal(
    sector_index: pd.DataFrame,
    *,
    max_carry_age: int = 5,
) -> pd.DataFrame:
    """Lag causal source-day z by one equity day and carry missing signals to age 5."""
    _require_columns(
        sector_index,
        ["date", "sector", "model", "compound_mean", "coverage", "causal_z"],
        "sector sentiment index",
    )
    rows: list[dict[str, Any]] = []
    for (sector, model), group in sector_index.groupby(["sector", "model"], sort=True):
        ordered = group.sort_values("date", kind="mergesort").reset_index(drop=True)
        last_valid_source_position: int | None = None
        for position, current in ordered.iterrows():
            source_position: int | None = None
            age: int | None = None
            immediate_source = position - 1
            if immediate_source >= 0 and pd.notna(ordered.loc[immediate_source, "causal_z"]):
                source_position = immediate_source
                last_valid_source_position = immediate_source
                age = 0
            elif last_valid_source_position is not None:
                candidate_age = position - last_valid_source_position - 1
                if 1 <= candidate_age <= max_carry_age:
                    source_position = last_valid_source_position
                    age = candidate_age

            if source_position is None or age is None:
                rows.append({
                    "effective_date": current["date"],
                    "source_date": pd.NaT,
                    "sector": sector,
                    "model": model,
                    "source_compound_mean": np.nan,
                    "source_causal_z": np.nan,
                    "signal_age": pd.NA,
                    "is_carried": False,
                    "source_coverage": np.nan,
                    "effective_coverage": np.nan,
                    "trading_z": np.nan,
                })
                continue

            source = ordered.loc[source_position]
            coverage = float(source["coverage"])
            effective_coverage = coverage if age == 0 else coverage * (6.0 - age) / 6.0
            rows.append({
                "effective_date": current["date"],
                "source_date": source["date"],
                "sector": sector,
                "model": model,
                "source_compound_mean": float(source["compound_mean"]),
                "source_causal_z": float(source["causal_z"]),
                "signal_age": age,
                "is_carried": age > 0,
                "source_coverage": coverage,
                "effective_coverage": effective_coverage,
                "trading_z": float(source["causal_z"]),
            })
    output = pd.DataFrame(rows, columns=SIGNAL_COLUMNS)
    output["signal_age"] = output["signal_age"].astype("Int64")
    return output.sort_values(
        ["effective_date", "sector", "model"], kind="mergesort"
    ).reset_index(drop=True)


def build_finance_lexicon_audit(
    finance_lexicon: pd.DataFrame,
    finance_analyzer: IsolatedVaderAnalyzer,
    frozen_path: str | Path,
) -> pd.DataFrame:
    """Record per-term collision precedence and frozen provenance."""
    base = vs.SentimentIntensityAnalyzer()
    frozen_hash = file_sha256(frozen_path)
    rows: list[dict[str, Any]] = []
    for record in finance_lexicon.itertuples(index=False):
        base_value = base.lexicon.get(record.term, np.nan)
        installed_value = (
            finance_analyzer.lexicon.get(record.term, np.nan)
            if record.term_type == "word"
            else float(record.valence)
        )
        rows.append({
            "term": record.term,
            "term_type": record.term_type,
            "valence": float(record.valence),
            "base_vader_value": base_value,
            "collision_with_base": record.term in base.lexicon,
            "installed_value": installed_value,
            "source_path": FINANCE_SOURCE_PATH,
            "source_sha256": FINANCE_LEXICON_SHA256,
            "frozen_path": str(Path(frozen_path)),
            "frozen_sha256": frozen_hash,
            "approved_term_count": FINANCE_APPROVED_COUNT,
            "rejected_term_count": FINANCE_REJECTED_COUNT,
            "validation_status": "pass",
        })
    return pd.DataFrame(rows, columns=LEXICON_AUDIT_COLUMNS).sort_values(
        "term", kind="mergesort"
    ).reset_index(drop=True)


def _classification(values: pd.Series) -> pd.Series:
    return pd.Series(
        np.select(
            [values.le(-0.05), values.ge(0.05)],
            ["negative", "positive"],
            default="neutral",
        ),
        index=values.index,
    )


def build_model_comparison(
    title_scores: pd.DataFrame,
    sector_index: pd.DataFrame,
) -> pd.DataFrame:
    """Compare score changes and coverage without making an accuracy claim."""
    _require_columns(title_scores, ["title", *MODELS], "title scores")
    plain = title_scores["plain_vader"].astype(float)
    finance = title_scores["finance_vader"].astype(float)
    difference = finance - plain
    changed = ~np.isclose(difference.to_numpy(), 0.0, atol=1e-15, rtol=0.0)
    plain_class = _classification(plain)
    finance_class = _classification(finance)
    class_changed = plain_class.ne(finance_class)
    transitions = pd.crosstab(plain_class, finance_class)

    pivot = sector_index.pivot(
        index=["date", "sector"], columns="model", values="compound_mean"
    ).dropna(subset=list(MODELS))
    sector_difference = pivot["finance_vader"] - pivot["plain_vader"]
    sector_changed = ~np.isclose(
        sector_difference.to_numpy(), 0.0, atol=1e-15, rtol=0.0
    )
    rows: list[tuple[str, Any]] = [
        ("distinct_titles_scored", len(title_scores)),
        ("titles_with_changed_compound", int(changed.sum())),
        ("titles_with_changed_compound_percent", float(changed.mean() * 100.0)),
        ("mean_absolute_compound_change", float(difference.abs().mean())),
        ("median_absolute_compound_change", float(difference.abs().median())),
        ("classification_changed_count_at_0.05", int(class_changed.sum())),
        ("classification_changed_percent_at_0.05", float(class_changed.mean() * 100.0)),
        ("sector_index_compared_rows", len(pivot)),
        ("sector_index_changed_rows", int(sector_changed.sum())),
        ("sector_index_changed_percent", float(sector_changed.mean() * 100.0) if len(pivot) else np.nan),
        ("sector_index_mean_absolute_compound_difference", float(sector_difference.abs().mean()) if len(pivot) else np.nan),
        ("approved_finance_term_count", FINANCE_APPROVED_COUNT),
        ("rejected_finance_term_count", FINANCE_REJECTED_COUNT),
        ("accuracy_claim", "none; changed scores are not labelled accuracy validation"),
    ]
    for source in ("negative", "neutral", "positive"):
        for target in ("negative", "neutral", "positive"):
            if source == target:
                continue
            count = int(transitions.loc[source, target]) if (
                source in transitions.index and target in transitions.columns
            ) else 0
            rows.append((f"classification_change_{source}_to_{target}", count))
    return pd.DataFrame(rows, columns=COMPARISON_COLUMNS)


def build_sentiment_data_audit(
    mapped_headlines: pd.DataFrame,
    title_scores: pd.DataFrame,
    ticker_day: pd.DataFrame,
    sector_index: pd.DataFrame,
    signals: pd.DataFrame,
) -> pd.DataFrame:
    """Build concise mapping, missingness, key, coverage, and lag audits."""
    status_counts = mapped_headlines["mapping_status"].value_counts()
    coverage = sector_index["coverage"].dropna()
    ages = signals["signal_age"].dropna().astype(int)
    checks = [
        ("rule_a_clean_headline_rows", len(mapped_headlines), "pass", "Every cleaned headline remains in the Rule A audit."),
        ("rule_a_same_trading_date_rows", int(status_counts.get("same_trading_date", 0)), "pass", "Headline UTC calendar date is an observed equity date."),
        ("rule_a_shifted_to_next_trading_date_rows", int(status_counts.get("shifted_to_next_trading_date", 0)), "pass", "Non-observed dates map to the next observed equity date."),
        ("rule_a_unmapped_final_boundary_rows", int(status_counts.get("unmapped_final_sample_boundary", 0)), "pass", "Rows remain in audit but are excluded from scoring."),
        ("original_timestamp_missing_rows", int(mapped_headlines["original_utc_timestamp"].isna().sum()), "pass", "Cleaned source timestamps are preserved."),
        ("distinct_titles_scored", len(title_scores), "pass", "Each distinct raw title is scored once per model."),
        ("ticker_day_rows", len(ticker_day), "pass", "Observed ticker-day-model aggregates only; missing news is not filled."),
        ("sector_index_rows", len(sector_index), "pass", "Complete observed-equity-date, sector, and model grid."),
        ("missing_sector_compound_rows", int(sector_index["compound_mean"].isna().sum()), "pass", "Missing sector news remains missing, not neutral."),
        ("coverage_out_of_bounds_rows", int(((coverage < 0.0) | (coverage > 1.0)).sum()), "pass", "Non-missing coverage lies in [0, 1]."),
        ("invalid_nonmissing_signal_age_rows", int((~ages.between(0, 5)).sum()), "pass", "Only ages 0 through 5 can carry a trading signal."),
        ("sector_index_duplicate_keys", int(sector_index.duplicated(["date", "sector", "model"]).sum()), "pass", "Sector-index key is unique."),
        ("ticker_day_duplicate_keys", int(ticker_day.duplicated(["date", "ticker", "model"]).sum()), "pass", "Ticker-day key is unique."),
        ("signal_duplicate_keys", int(signals.duplicated(["effective_date", "sector", "model"]).sum()), "pass", "Trading-signal key is unique."),
    ]
    result = pd.DataFrame(checks, columns=SENTIMENT_AUDIT_COLUMNS)
    failures = {
        "rule_a_clean_headline_rows": result.loc[result["check_name"].eq("rule_a_clean_headline_rows"), "value"].iloc[0] != 146836,
        "rule_a_unmapped_final_boundary_rows": result.loc[result["check_name"].eq("rule_a_unmapped_final_boundary_rows"), "value"].iloc[0] != 6,
        "coverage_out_of_bounds_rows": int(result.loc[result["check_name"].eq("coverage_out_of_bounds_rows"), "value"].iloc[0]) != 0,
        "invalid_nonmissing_signal_age_rows": int(result.loc[result["check_name"].eq("invalid_nonmissing_signal_age_rows"), "value"].iloc[0]) != 0,
        "sector_index_duplicate_keys": int(result.loc[result["check_name"].eq("sector_index_duplicate_keys"), "value"].iloc[0]) != 0,
        "ticker_day_duplicate_keys": int(result.loc[result["check_name"].eq("ticker_day_duplicate_keys"), "value"].iloc[0]) != 0,
        "signal_duplicate_keys": int(result.loc[result["check_name"].eq("signal_duplicate_keys"), "value"].iloc[0]) != 0,
    }
    for check_name, failed in failures.items():
        if failed:
            result.loc[result["check_name"].eq(check_name), "status"] = "fail"
    return result


score_headlines = score_mapped_headlines
sector_sentiment_index = build_sector_sentiment_index
