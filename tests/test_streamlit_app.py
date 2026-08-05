"""Static and Streamlit AppTest checks for the precomputed investor app."""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import app_utils


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "streamlit_app.py"


def _start_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=40)
    app.run()
    assert not app.exception
    return app


def test_app_imports_only_precomputed_utility_module_and_has_no_network_client() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert "from src import app_utils" in text
    for prohibited in (
        "src.data_access", "src.etl", "src.features", "src.portfolios",
        "src.sentiment", "src.fusion", "requests.", "urllib.", "httpx.",
    ):
        assert prohibited not in text


def test_deployed_requirements_include_plotly_and_exclude_sentiment_scorer() -> None:
    requirements = [
        line.strip() for line in (ROOT / "requirements.txt").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert any(line.startswith("plotly>=") and ",<" in line for line in requirements)
    assert not any("vadersentiment" in line.lower() for line in requirements)
    dev = (ROOT / "requirements-dev.txt").read_text()
    assert "vaderSentiment==3.3.2" in dev


def test_app_starts_and_all_five_investor_journey_tabs_are_present() -> None:
    app = _start_app()
    assert [tab.label for tab in app.tabs] == [
        "Fund Explorer", "Fund Fact Sheet", "Allocation Lab",
        "Sentiment Lab", "Fusion Evidence",
    ]
    visible_text = " ".join(
        [item.value for item in app.warning]
        + [item.value for item in app.caption]
        + [item.value for item in app.info]
    )
    assert "underperformed" in visible_text
    assert "latest target weights" in APP_PATH.read_text().lower()


@pytest.mark.parametrize("fund_id", sorted(app_utils.EXPECTED_FUND_IDS))
def test_every_fund_can_render_a_fact_sheet_selection(fund_id: str) -> None:
    app = _start_app()
    app.selectbox(key="fact_sheet_fund").set_value(fund_id).run()
    assert not app.exception
    assert app.selectbox(key="fact_sheet_fund").value == fund_id
