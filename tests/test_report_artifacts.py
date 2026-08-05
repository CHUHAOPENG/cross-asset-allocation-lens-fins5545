from __future__ import annotations

import ast
from pathlib import Path
import re

import numpy as np
import pandas as pd

from scripts import build_report_artifacts
from src import app_utils


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_APP_TABS = [
    "Fund Explorer",
    "Fund Fact Sheet",
    "Allocation Lab",
    "Sentiment Lab",
    "Fusion Evidence",
]


def _requirement_names(path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        names.add(re.split(r"[<>=!~]", line, maxsplit=1)[0].lower())
    return names


def test_report_artifacts_are_complete_and_consistent() -> None:
    build_report_artifacts.validate_report_outputs()

    summary = pd.read_csv(ROOT / "results/tables/report_fund_summary.csv")
    assert len(summary) == 13
    assert set(summary["fund_id"]) == app_utils.EXPECTED_FUND_IDS

    allocation = pd.read_csv(
        ROOT / "results/tables/report_allocation_example_weights.csv"
    )
    assert len(allocation) == 4
    assert np.isclose(allocation["illustrative_weight"].sum(), 1.0, atol=1e-12)

    catalog = pd.read_csv(ROOT / "results/tables/report_exhibit_catalog.csv")
    all_sector_artifact = (
        "results/figures/report_all_sector_sentiment_small_multiples.png"
    )
    assert catalog["artifact"].eq(all_sector_artifact).sum() == 1


def test_all_sector_sentiment_figure_input_preserves_scope_and_gaps() -> None:
    artifacts = app_utils.load_app_artifacts(ROOT)
    frame = build_report_artifacts._all_sector_sentiment_input(artifacts)

    assert set(frame["sector"]) == set(build_report_artifacts.EXPECTED_EQUITY_SECTORS)
    assert frame["sector"].nunique() == 10
    assert frame["model"].eq("finance_vader").all()
    assert frame.groupby("sector")["date"].size().eq(1006).all()
    missing_sentiment = frame["compound_mean"].isna()
    assert missing_sentiment.any()
    assert frame.loc[missing_sentiment, "index_0_100"].isna().all()


def test_final_report_references_existing_local_artifacts() -> None:
    report_path = ROOT / "report/FINAL_REPORT.md"
    report = report_path.read_text(encoding="utf-8")
    references = re.findall(r"\]\((\.\./[^)#]+)(?:#[^)]+)?\)", report)

    assert references
    assert not (ROOT / "report/OUTLINE.md").exists()
    for reference in references:
        assert (report_path.parent / reference).resolve().is_file(), reference


def test_readme_and_report_match_actual_streamlit_tab_names() -> None:
    tree = ast.parse((ROOT / "streamlit_app.py").read_text(encoding="utf-8"))
    tab_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "tabs"
    ]
    assert len(tab_calls) == 1
    tabs_node = tab_calls[0].args[0]
    assert isinstance(tabs_node, (ast.List, ast.Tuple))
    actual_tabs = [ast.literal_eval(element) for element in tabs_node.elts]
    assert actual_tabs == EXPECTED_APP_TABS

    report = (ROOT / "report/FINAL_REPORT.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for tab in EXPECTED_APP_TABS:
        assert f"**{tab}**" in report
        assert f"**{tab}**" in readme
    for obsolete in ("**Start Here**", "**Compare Funds**", "**Fund Fact Sheets**", "**Sentiment & Fusion**"):
        assert obsolete not in report
        assert obsolete not in readme


def test_dependency_split_matches_runtime_boundary() -> None:
    runtime = _requirement_names(ROOT / "requirements.txt")
    development = _requirement_names(ROOT / "requirements-dev.txt")

    assert runtime == {"streamlit", "pandas", "numpy", "plotly"}
    assert {"scipy", "pyarrow", "requests", "matplotlib", "vadersentiment", "pytest"} <= development
    assert not ({"scipy", "pyarrow", "requests", "matplotlib", "vadersentiment", "pytest"} & runtime)
