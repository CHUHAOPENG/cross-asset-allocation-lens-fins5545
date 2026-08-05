from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pandas as pd

from scripts import build_report_artifacts
from src import app_utils


ROOT = Path(__file__).resolve().parents[1]


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


def test_final_report_references_existing_local_artifacts() -> None:
    report_path = ROOT / "report/FINAL_REPORT.md"
    report = report_path.read_text(encoding="utf-8")
    references = re.findall(r"\]\((\.\./[^)#]+)(?:#[^)]+)?\)", report)

    assert references
    assert not (ROOT / "report/OUTLINE.md").exists()
    for reference in references:
        assert (report_path.parent / reference).resolve().is_file(), reference


def test_dependency_split_matches_runtime_boundary() -> None:
    runtime = _requirement_names(ROOT / "requirements.txt")
    development = _requirement_names(ROOT / "requirements-dev.txt")

    assert runtime == {"streamlit", "pandas", "numpy", "plotly"}
    assert {"scipy", "pyarrow", "requests", "matplotlib", "vadersentiment", "pytest"} <= development
    assert not ({"scipy", "pyarrow", "requests", "matplotlib", "vadersentiment", "pytest"} & runtime)
