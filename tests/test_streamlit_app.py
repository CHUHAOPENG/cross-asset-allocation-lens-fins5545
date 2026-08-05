"""Static and Streamlit AppTest checks for the precomputed investor app."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import tomllib

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src import app_utils


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "streamlit_app.py"
CONFIG_PATH = ROOT / ".streamlit" / "config.toml"


def _start_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=40)
    app.run()
    assert not app.exception
    return app


def test_app_imports_only_precomputed_utility_module_and_has_no_network_client() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported_modules == {
        "__future__", "pathlib", "pandas", "plotly.express",
        "plotly.graph_objects", "streamlit", "src",
    }
    assert "from src import app_utils" in text
    for prohibited in (
        "src.data_access", "src.etl", "src.features", "src.portfolios",
        "src.sentiment", "src.fusion", "requests.", "urllib.", "httpx.",
        "socket.", "aiohttp.",
    ):
        assert prohibited not in text


def test_streamlit_config_forces_the_approved_light_theme() -> None:
    with CONFIG_PATH.open("rb") as config_file:
        config = tomllib.load(config_file)
    assert config["server"]["headless"] is True
    assert config["browser"]["gatherUsageStats"] is False
    assert config["theme"] == {
        "base": "light",
        "primaryColor": "#C94352",
        "backgroundColor": "#F7F9FC",
        "secondaryBackgroundColor": "#FFFFFF",
        "textColor": "#1F2933",
        "font": "sans serif",
    }


def test_every_plotly_render_explicitly_disables_streamlit_theming() -> None:
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    plotly_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "st"
        and node.func.attr == "plotly_chart"
    ]
    assert plotly_calls
    for call in plotly_calls:
        theme = next((keyword.value for keyword in call.keywords if keyword.arg == "theme"), None)
        assert isinstance(theme, ast.Constant) and theme.value is None


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


def test_visible_oos_and_effective_dates_have_no_timestamp_component() -> None:
    app = _start_app()
    visible_text = " ".join(
        str(item.value)
        for collection in (app.caption, app.info, app.success, app.warning)
        for item in collection
    )
    assert "00:00:00" not in visible_text

    checked_columns = 0
    date_columns = {
        "OOS start", "OOS end", "Date", "as_of_date",
        "latest_signal_source_date",
    }
    for element in app.dataframe:
        frame = element.value
        if not isinstance(frame, pd.DataFrame):
            continue
        for column in date_columns.intersection(frame.columns):
            checked_columns += 1
            values = frame[column].dropna().astype(str)
            assert values.map(lambda value: bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}|—", value))).all()
            assert not values.str.contains(r"\d{2}:\d{2}:\d{2}", regex=True).any()
    assert checked_columns >= 5


def test_scatter_uses_readable_fund_group_and_hover_labels() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert 'color="Universe group"' in text
    assert 'hover_name="display_name"' in text
    assert 'symbol="method"' not in text


@pytest.mark.parametrize("fund_id", sorted(app_utils.EXPECTED_FUND_IDS))
def test_every_fund_can_render_a_fact_sheet_selection(fund_id: str) -> None:
    app = _start_app()
    app.selectbox(key="fact_sheet_fund").set_value(fund_id).run()
    assert not app.exception
    assert app.selectbox(key="fact_sheet_fund").value == fund_id
