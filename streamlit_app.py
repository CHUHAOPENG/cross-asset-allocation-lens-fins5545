"""Cross-Asset Allocation Lens — precomputed investor research application."""
from __future__ import annotations

import pathlib

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import app_utils


ROOT = pathlib.Path(__file__).resolve().parent
RESULTS = ROOT / "results"
PALETTE = {
    "navy": "#17324D",
    "blue": "#2F6B9A",
    "cyan": "#5AA6A6",
    "orange": "#D97745",
    "gold": "#C99A2E",
    "red": "#B94A48",
    "ink": "#1F2933",
    "muted": "#66788A",
    "paper": "#F5F7FA",
}
FUND_COLORS = [
    "#17324D", "#2F6B9A", "#D97745", "#5AA6A6", "#8B5FBF", "#C99A2E",
    "#B94A48", "#4C8C6D", "#7A6F9B", "#457B9D", "#A26769", "#6B705C",
    "#E07A5F",
]


st.set_page_config(
    page_title="Cross-Asset Allocation Lens",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    :root { --navy:#17324D; --blue:#2F6B9A; --orange:#D97745; --paper:#F5F7FA; }
    .stApp { background: linear-gradient(180deg, #F7F9FC 0%, #FFFFFF 28%); }
    .block-container { max-width: 1480px; padding-top: 1.6rem; padding-bottom: 3rem; }
    .hero { padding: 1.35rem 1.55rem; border-radius: 18px;
            background: linear-gradient(120deg, #17324D, #2F6B9A 70%, #5AA6A6); }
    .hero, .hero h1, .hero p, .hero .eyebrow { color: #FFFFFF; }
    .hero h1 { margin: 0; font-size: clamp(2rem, 4vw, 3.25rem); letter-spacing: -0.03em; }
    .hero p { margin: .55rem 0 0; max-width: 920px; font-size: 1.04rem; }
    .eyebrow { text-transform: uppercase; letter-spacing: .12em; font-weight: 700;
               font-size: .75rem; }
    div[data-testid="stHeadingWithActionElements"],
    div[data-testid="stMarkdownContainer"] > p,
    div[data-testid="stMarkdownContainer"] > ul,
    div[data-testid="stMarkdownContainer"] > ol,
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpanderDetails"] div[data-testid="stMarkdownContainer"] > p,
    div[data-testid="stExpanderDetails"] div[data-testid="stMarkdownContainer"] > ul {
        color: #1F2933;
    }
    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] p { color: #4A5B6B; }
    div[data-testid="stWidgetLabel"],
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stToggle"] label,
    div[data-testid="stToggle"] label p,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stMultiSelect"] label p,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stNumberInput"] label p { color: #1F2933; }
    div[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #DDE5EC;
                                  border-radius: 14px; padding: .8rem 1rem; }
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricValue"] { color: #1F2933; }
    div[data-testid="stTabs"] button[role="tab"] { color: #526374; font-weight: 650; }
    div[data-testid="stTabs"] button[role="tab"] p { color: inherit; }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #17324D; border-bottom-color: #C94352;
    }
    div[data-testid="stAlert"],
    div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] > p {
        color: #1F2933;
    }
    .disclosure { border-left: 4px solid #D97745; padding: .7rem 1rem;
                  background: #FFF3E8; border-radius: 0 10px 10px 0;
                  color: #1F2933; }
    .target-label { color:#17324D; font-weight:700; }
    .small-note { color:#526374; font-size:.88rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading validated precomputed artifacts …")
def _load_artifacts(project_root: str) -> app_utils.AppArtifacts:
    return app_utils.load_app_artifacts(project_root)


def _format_percent(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:.1%}"


def _format_number(value: float, digits: int = 2) -> str:
    return "—" if pd.isna(value) else f"{value:.{digits}f}"


def _format_display_dates(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return a display-only copy with dates rendered as ISO calendar dates."""
    output = frame.copy()
    for column in columns:
        if column in output.columns:
            parsed = pd.to_datetime(output[column], errors="coerce")
            output[column] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), "—")
    return output


def _render_plotly(figure: go.Figure, *, key: str) -> None:
    """Apply the approved light Plotly presentation and render without theming."""
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"color": PALETTE["ink"]},
        legend={
            "bgcolor": "rgba(255,255,255,0.92)",
            "bordercolor": "#DDE5EC",
            "borderwidth": 1,
            "font": {"color": PALETTE["ink"]},
        },
        hoverlabel={
            "bgcolor": "#FFFFFF",
            "bordercolor": "#CBD5E1",
            "font": {"color": PALETTE["ink"]},
        },
    )
    figure.update_xaxes(
        gridcolor="#E5E7EB", linecolor="#CBD5E1", zerolinecolor="#CBD5E1"
    )
    figure.update_yaxes(
        gridcolor="#E5E7EB", linecolor="#CBD5E1", zerolinecolor="#CBD5E1"
    )
    st.plotly_chart(figure, width="stretch", key=key, theme=None)


def _line_chart(
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: str,
    title: str,
    y_title: str,
    percent_axis: bool = False,
) -> go.Figure:
    figure = px.line(
        frame,
        x=x,
        y=y,
        color=color,
        title=title,
        color_discrete_sequence=FUND_COLORS,
    )
    figure.update_traces(line={"width": 2.2}, connectgaps=False)
    figure.update_layout(
        template="plotly_white",
        height=430,
        legend_title_text="",
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
        xaxis_title="Date",
        yaxis_title=y_title,
    )
    figure.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")
    if percent_axis:
        figure.update_yaxes(tickformat=".1%")
    return figure


def _method_note(method: str, universe: str) -> str:
    method_text = {
        "equal_weight": "Capped equal weighting across assets eligible at each decision date.",
        "minimum_variance": "Expanding walk-forward minimum-variance targets using shrunk sample covariance.",
        "risk_parity": "Expanding walk-forward targets balancing percentage risk contributions.",
        "max_sharpe": "Expanding walk-forward maximum-Sharpe targets with shrunk expected returns and zero risk-free rate.",
        "risk_parity_sentiment": "The fixed coverage-aware finance-sentiment overlay applied to Equity Risk Parity; it was not retuned after observing results.",
    }[method]
    calendar = (
        "native seven-day crypto calendar and 365-period annualisation"
        if universe == "crypto"
        else "observed equity-date calendar and 252-period annualisation"
    )
    return f"{method_text} Results use the {calendar}. Targets become effective after the decision date."


try:
    artifacts = _load_artifacts(str(ROOT))
except app_utils.ArtifactError as exc:
    st.error("The precomputed application artifacts are unavailable or invalid.")
    st.code(str(exc))
    st.info("From the project root, run `python scripts/run_part_b.py`, then reload this page.")
    st.stop()

catalog = artifacts.fund_catalog.sort_values("display_name", kind="mergesort")
labels = app_utils.fund_label_map(catalog)
all_funds = catalog["fund_id"].tolist()
sample_start = artifacts.fund_returns["date"].min().date().isoformat()
sample_end = artifacts.fund_returns["date"].max().date().isoformat()

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Systematic portfolio research</div>
      <h1>Cross-Asset Allocation Lens</h1>
      <p>Compare 13 walk-forward funds, inspect their latest rebalance targets,
      test a fund-level allocation, and examine the fixed sentiment overlay—using
      committed out-of-sample results only.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    f"Precomputed sample coverage: {sample_start} to {sample_end}. "
    "Individual fund OOS periods are shown wherever funds are selected."
)

with st.expander("Data, cost, and educational-use disclosure", expanded=False):
    st.markdown(
        """
        - This app reads committed precomputed results and performs no model fitting,
          backtesting, sentiment scoring, data download, or allocation optimisation.
        - Fund results include the project's recorded one-way trading-cost model.
          Management fees, taxes, and investor-level cross-fund transaction costs are
          not included.
        - “Holdings” means **latest target weights from the most recent rebalance**,
          not live market holdings or real-time positions.
        - Historical OOS evidence does not predict future performance. This tool is
          analytical and educational only, not personalised financial advice.
        """
    )

tab_explorer, tab_fact, tab_allocation, tab_sentiment, tab_fusion = st.tabs([
    "Fund Explorer",
    "Fund Fact Sheet",
    "Allocation Lab",
    "Sentiment Lab",
    "Fusion Evidence",
])


with tab_explorer:
    st.header("Fund Explorer")
    st.write("Compare fund-level net outcomes first, then inspect gross results where useful.")
    filter_col, basis_col = st.columns([3, 1])
    with filter_col:
        categories = st.multiselect(
            "Fund groups",
            ["Equity", "Crypto", "Combined", "Sentiment-Augmented"],
            default=["Equity", "Crypto", "Combined", "Sentiment-Augmented"],
            key="explorer_categories",
        )
    with basis_col:
        basis_label = st.radio(
            "Performance basis", ["Net", "Gross"], horizontal=True,
            key="explorer_basis",
        )
    basis = basis_label.lower()
    comparison = app_utils.filter_fund_comparison(
        artifacts.fund_catalog,
        artifacts.performance_metrics,
        categories=categories,
        basis=basis,
    )
    if comparison.empty:
        st.warning("Select at least one fund group to populate the comparison.")
    else:
        display = comparison.rename(columns={
            "display_name": "Fund",
            "universe": "Universe",
            "method": "Method",
            "first_live_date": "OOS start",
            "last_date": "OOS end",
            "periods_per_year": "Annualisation",
            f"cumulative_return_{basis}": "Cumulative return",
            f"annualised_return_{basis}": "Annualised return",
            f"annualised_volatility_{basis}": "Annualised volatility",
            f"sharpe_{basis}": "Sharpe",
            f"max_drawdown_{basis}": "Maximum drawdown",
            "total_turnover": "Total turnover",
            "total_trading_cost": "Total trading cost",
            "rebalance_count": "Rebalances",
            "fallback_count": "Fallbacks",
        })
        display["Universe"] = display["Universe"].str.title()
        display["Method"] = display["Method"].map({
            "equal_weight": "Equal Weight",
            "minimum_variance": "Minimum Variance",
            "risk_parity": "Risk Parity",
            "max_sharpe": "Maximum Sharpe",
            "risk_parity_sentiment": "Risk Parity + Sentiment",
        })
        display = _format_display_dates(display, ["OOS start", "OOS end"])
        comparison_order = [
            "Fund", "Cumulative return", "Annualised return",
            "Annualised volatility", "Sharpe", "Maximum drawdown",
            "Universe", "Method", "OOS start", "OOS end", "Annualisation",
            "Total turnover", "Total trading cost", "Rebalances", "Fallbacks",
        ]
        st.dataframe(
            display[comparison_order],
            width="stretch",
            hide_index=True,
            column_config={
                "Fund": st.column_config.TextColumn(width="medium"),
                "Universe": st.column_config.TextColumn(width="small"),
                "Method": st.column_config.TextColumn(width="medium"),
                "OOS start": st.column_config.TextColumn(width="small"),
                "OOS end": st.column_config.TextColumn(width="small"),
                "Cumulative return": st.column_config.NumberColumn(format="percent"),
                "Annualised return": st.column_config.NumberColumn(format="percent"),
                "Annualised volatility": st.column_config.NumberColumn(format="percent"),
                "Maximum drawdown": st.column_config.NumberColumn(format="percent"),
                "Total turnover": st.column_config.NumberColumn(format="percent"),
                "Total trading cost": st.column_config.NumberColumn(format="percent"),
            },
        )
        scatter_data = comparison.copy()
        scatter_data["Universe group"] = scatter_data["universe"].map({
            "equity": "Equity", "crypto": "Crypto", "combined": "Combined",
        })
        scatter_data["Method"] = scatter_data["method"].map({
            "equal_weight": "Equal Weight",
            "minimum_variance": "Minimum Variance",
            "risk_parity": "Risk Parity",
            "max_sharpe": "Maximum Sharpe",
            "risk_parity_sentiment": "Risk Parity + Sentiment",
        })
        scatter = px.scatter(
            scatter_data,
            x=f"annualised_volatility_{basis}",
            y=f"annualised_return_{basis}",
            color="Universe group",
            hover_name="display_name",
            hover_data={
                "Universe group": False,
                "Method": True,
                f"annualised_volatility_{basis}": ":.1%",
                f"annualised_return_{basis}": ":.1%",
            },
            title=f"{basis_label} annualised return versus volatility",
            labels={
                f"annualised_volatility_{basis}": "Annualised volatility",
                f"annualised_return_{basis}": "Annualised return",
            },
            color_discrete_map={
                "Equity": PALETTE["blue"],
                "Crypto": PALETTE["orange"],
                "Combined": PALETTE["cyan"],
            },
        )
        scatter.update_layout(height=480, legend_title_text="Fund group")
        scatter.update_xaxes(title="Annualised volatility", tickformat=".1%")
        scatter.update_yaxes(title="Annualised arithmetic return", tickformat=".1%")
        _render_plotly(scatter, key="explorer_scatter")

    default_compare = ["equity_risk_parity", "equity_risk_parity_sentiment"]
    selected_compare = st.multiselect(
        "Funds for growth and drawdown",
        all_funds,
        default=default_compare,
        format_func=lambda value: labels[value],
        key="explorer_growth_funds",
    )
    if selected_compare:
        selected_catalog = catalog.loc[catalog["fund_id"].isin(selected_compare), [
            "display_name", "first_live_date", "last_date", "periods_per_year",
        ]]
        selected_catalog = _format_display_dates(
            selected_catalog.rename(columns={
                "display_name": "Fund", "first_live_date": "OOS start",
                "last_date": "OOS end", "periods_per_year": "Annualisation",
            }),
            ["OOS start", "OOS end"],
        )
        st.dataframe(
            selected_catalog,
            hide_index=True,
            width="stretch",
            column_config={
                "Fund": st.column_config.TextColumn(width="large"),
                "OOS start": st.column_config.TextColumn(width="small"),
                "OOS end": st.column_config.TextColumn(width="small"),
            },
        )
        series = artifacts.fund_returns.loc[
            artifacts.fund_returns["fund_id"].isin(selected_compare)
        ].copy()
        series["Fund"] = series["fund_id"].map(labels)
        growth_col = f"growth_{basis}"
        drawdown_col = f"drawdown_{basis}"
        left, right = st.columns(2)
        with left:
            _render_plotly(
                _line_chart(series, x="date", y=growth_col, color="Fund", title=f"Growth of $1 — {basis_label}", y_title="Growth of $1"),
                key="explorer_growth",
            )
        with right:
            _render_plotly(
                _line_chart(series, x="date", y=drawdown_col, color="Fund", title=f"Drawdown — {basis_label}", y_title="Drawdown", percent_axis=True),
                key="explorer_drawdown",
            )


with tab_fact:
    st.header("Fund Fact Sheet")
    selected_fact = st.selectbox(
        "Choose one of the 13 funds",
        all_funds,
        format_func=lambda value: labels[value],
        key="fact_sheet_fund",
    )
    fund = catalog.loc[catalog["fund_id"].eq(selected_fact)].iloc[0]
    metric = artifacts.performance_metrics.loc[
        artifacts.performance_metrics["fund_id"].eq(selected_fact)
    ].iloc[0]
    st.subheader(fund["display_name"])
    st.caption(
        f"{fund['short_description']} OOS {fund['first_live_date'].date().isoformat()} to "
        f"{fund['last_date'].date().isoformat()} · {int(fund['periods_per_year'])}-period annualisation."
    )
    cards = st.columns(6)
    cards[0].metric("Growth of $1 (net)", _format_number(1.0 + metric["cumulative_return_net"]))
    cards[1].metric("Annualised return (net)", _format_percent(metric["annualised_return_net"]))
    cards[2].metric("Annualised volatility", _format_percent(metric["annualised_volatility_net"]))
    cards[3].metric("Sharpe (net)", _format_number(metric["sharpe_net"]))
    cards[4].metric("Maximum drawdown", _format_percent(metric["max_drawdown_net"]))
    cards[5].metric("Cumulative return (net)", _format_percent(metric["cumulative_return_net"]))
    detail_cards = st.columns(5)
    detail_cards[0].metric("Total turnover", _format_percent(metric["total_turnover"]))
    detail_cards[1].metric("Trading cost", _format_percent(metric["total_trading_cost"]))
    detail_cards[2].metric("Rebalances", f"{int(metric['rebalance_count'])}")
    detail_cards[3].metric("Fallbacks", f"{int(metric['fallback_count'])}")
    detail_cards[4].metric("Observations", f"{int(metric['observations']):,}")

    fund_series = artifacts.fund_returns.loc[
        artifacts.fund_returns["fund_id"].eq(selected_fact)
    ].copy()
    fact_chart = go.Figure()
    fact_chart.add_trace(go.Scatter(x=fund_series["date"], y=fund_series["growth_net"], name="Net", line={"color": PALETTE["navy"], "width": 2.5}))
    fact_chart.add_trace(go.Scatter(x=fund_series["date"], y=fund_series["growth_gross"], name="Gross", line={"color": PALETTE["orange"], "width": 1.8, "dash": "dash"}))
    fact_chart.update_layout(template="plotly_white", height=440, title="Growth of $1 — gross and net", xaxis_title="Date", yaxis_title="Growth of $1", hovermode="x unified", legend_title_text="")
    fact_chart.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")
    _render_plotly(fact_chart, key="fact_sheet_growth")

    st.markdown('<div class="target-label">Latest target weights from the most recent rebalance</div>', unsafe_allow_html=True)
    holdings = app_utils.latest_target_holdings(
        artifacts.fund_current_holdings, selected_fact
    )
    as_of = holdings["as_of_date"].iloc[0].date().isoformat()
    st.caption(f"Target effective date: {as_of}. These are not live market holdings.")
    top = holdings.head(12).sort_values("target_weight")
    hold_left, hold_right = st.columns([3, 2])
    with hold_left:
        holding_chart = px.bar(
            top,
            x="target_weight",
            y="ticker",
            orientation="h",
            color="asset_class",
            title="Top target weights",
            color_discrete_map={"equity": PALETTE["blue"], "crypto": PALETTE["orange"]},
        )
        holding_chart.update_layout(template="plotly_white", height=470, legend_title_text="")
        holding_chart.update_xaxes(tickformat=".1%", title="Target weight")
        holding_chart.update_yaxes(title="")
        _render_plotly(holding_chart, key="fact_sheet_holdings_chart")
    with hold_right:
        st.dataframe(
            holdings[["holding_rank", "ticker", "asset_class", "target_weight"]].rename(columns={
                "holding_rank": "Rank", "ticker": "Ticker",
                "asset_class": "Asset class", "target_weight": "Target weight",
            }),
            width="stretch",
            hide_index=True,
            column_config={"Target weight": st.column_config.NumberColumn(format="percent")},
        )
        st.download_button(
            "Download full target table",
            holdings.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_fact}_latest_target_weights.csv",
            mime="text/csv",
            key="fact_sheet_holdings_download",
        )

    default_tickers = holdings.head(5)["ticker"].tolist()
    history_tickers = st.multiselect(
        "Tickers for target-weight history",
        holdings["ticker"].tolist(),
        default=default_tickers,
        key="fact_sheet_history_tickers",
    )
    if history_tickers:
        history = app_utils.selected_fund_weight_history(
            artifacts.fund_weights, selected_fact, tickers=history_tickers
        )
        history_chart = px.line(
            history,
            x="effective_date",
            y="target_weight",
            color="ticker",
            markers=True,
            title="Target weights through rebalance dates",
            color_discrete_sequence=FUND_COLORS,
        )
        history_chart.update_layout(template="plotly_white", height=440, legend_title_text="Ticker")
        history_chart.update_yaxes(tickformat=".1%", title="Target weight")
        history_chart.update_xaxes(
            title="Target effective date",
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d",
        )
        _render_plotly(history_chart, key="fact_sheet_weight_history")
    st.info(_method_note(fund["method"], fund["universe"]))


with tab_allocation:
    st.header("Allocation Lab")
    st.write("Test your own fund-level allocation. The app does not optimise or recommend weights.")
    allocation_funds = st.multiselect(
        "Select 2–6 funds",
        all_funds,
        default=["equity_risk_parity", "equity_risk_parity_sentiment"],
        max_selections=6,
        format_func=lambda value: labels[value],
        key="allocation_funds",
    )
    if not 2 <= len(allocation_funds) <= 6:
        st.warning("Select between 2 and 6 funds to run the allocation lab.")
    else:
        allocation_method_label = st.radio(
            "Allocation method",
            ["Buy & Hold", "Monthly Reset"],
            horizontal=True,
            key="allocation_method",
        )
        st.caption(
            "Buy & Hold lets fund sleeves drift. Monthly Reset restores targets on "
            "the first available common-period date of each calendar month."
        )
        base_percentage = round(100.0 / len(allocation_funds), 2)
        defaults = [base_percentage] * (len(allocation_funds) - 1)
        defaults.append(round(100.0 - sum(defaults), 2))
        inputs = {}
        columns = st.columns(min(3, len(allocation_funds)))
        for position, (fund_id, default) in enumerate(zip(allocation_funds, defaults, strict=True)):
            with columns[position % len(columns)]:
                inputs[fund_id] = st.number_input(
                    labels[fund_id],
                    min_value=0.0,
                    max_value=100.0,
                    value=float(default),
                    step=1.0,
                    format="%.2f",
                    key=f"allocation_pct_{fund_id}",
                )
        total_percentage = sum(inputs.values())
        st.metric("Allocation total", f"{total_percentage:.2f}%")
        try:
            allocations = app_utils.validate_allocations({
                fund_id: percentage / 100.0 for fund_id, percentage in inputs.items()
            })
        except ValueError as exc:
            st.error(str(exc))
        else:
            annualisation = app_utils.allocation_periods_per_year(
                artifacts.fund_catalog, allocation_funds
            )
            method = "buy_and_hold" if allocation_method_label == "Buy & Hold" else "monthly_reset"
            simulation = app_utils.simulate_allocation(
                artifacts.fund_returns,
                allocations,
                method=method,
                periods_per_year=annualisation,
            )
            metrics = app_utils.calculate_annualised_metrics(
                simulation.daily["portfolio_return"], periods_per_year=annualisation
            )
            st.success(
                f"Exact common finite OOS period: {simulation.common_first_date.date().isoformat()} "
                f"to {simulation.common_last_date.date().isoformat()} · {simulation.observations:,} observations · "
                f"{annualisation}-period annualisation."
            )
            if simulation.excluded_nonfinite_dates:
                st.warning(
                    f"Excluded {simulation.excluded_nonfinite_dates} intersecting date(s) with a "
                    "missing or non-finite selected-fund return; no value was filled."
                )
            allocation_cards = st.columns(5)
            allocation_cards[0].metric("Cumulative return", _format_percent(metrics["cumulative_return"]))
            allocation_cards[1].metric("Annualised return", _format_percent(metrics["annualised_return"]))
            allocation_cards[2].metric("Annualised volatility", _format_percent(metrics["annualised_volatility"]))
            allocation_cards[3].metric("Sharpe", _format_number(metrics["sharpe"]))
            allocation_cards[4].metric("Maximum drawdown", _format_percent(metrics["max_drawdown"]))
            sim_long = simulation.daily.melt(
                id_vars=["date"], value_vars=["portfolio_value", "drawdown"],
                var_name="series", value_name="value",
            )
            allocation_left, allocation_right = st.columns(2)
            with allocation_left:
                growth_fig = px.line(
                    simulation.daily, x="date", y="portfolio_value",
                    title="Simulated growth of $1",
                )
                growth_fig.update_traces(line={"color": PALETTE["navy"], "width": 2.5})
                growth_fig.update_layout(template="plotly_white", height=420, xaxis_title="Date", yaxis_title="Portfolio value")
                growth_fig.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")
                _render_plotly(growth_fig, key="allocation_growth")
            with allocation_right:
                drawdown_fig = px.area(
                    simulation.daily, x="date", y="drawdown",
                    title="Simulated drawdown",
                )
                drawdown_fig.update_traces(line={"color": PALETTE["red"]}, fillcolor="rgba(185,74,72,.20)")
                drawdown_fig.update_layout(template="plotly_white", height=420, xaxis_title="Date", yaxis_title="Drawdown")
                drawdown_fig.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")
                drawdown_fig.update_yaxes(tickformat=".1%")
                _render_plotly(drawdown_fig, key="allocation_drawdown")
            if method == "monthly_reset":
                st.caption(
                    f"Recorded {len(simulation.rebalance_dates)} allocation dates, including "
                    "the initial allocation and each month-start reset."
                )
            st.download_button(
                "Download simulated daily series",
                simulation.daily.to_csv(index=False).encode("utf-8"),
                file_name=f"allocation_{method}.csv",
                mime="text/csv",
                key="allocation_download",
            )
            st.markdown(
                '<div class="disclosure"><b>Cost limitation:</b> simulation uses only '
                'precomputed fund net returns. It deducts no additional management fee, tax, '
                'or cross-fund transaction cost when sleeves are initially allocated or reset.</div>',
                unsafe_allow_html=True,
            )


with tab_sentiment:
    st.header("Sentiment Lab")
    sector_col, model_col, z_col = st.columns([2, 2, 1])
    sectors = sorted(artifacts.sector_sentiment_index["sector"].unique())
    with sector_col:
        selected_sector = st.selectbox("Sector", sectors, key="sentiment_sector")
    with model_col:
        selected_model = st.radio(
            "Model", ["finance_vader", "plain_vader"], horizontal=True,
            format_func=lambda value: "Finance-extended VADER" if value == "finance_vader" else "Plain VADER",
            key="sentiment_model",
        )
    with z_col:
        show_causal = st.toggle("Show causal z-score", value=False, key="sentiment_show_z")
    sentiment_series = app_utils.filter_sentiment_time_series(
        artifacts.sector_sentiment_index,
        sector=selected_sector,
        model=selected_model,
    )
    index_chart = go.Figure(go.Scatter(
        x=sentiment_series["date"],
        y=sentiment_series["index_0_100"],
        mode="lines",
        name="Descriptive index",
        connectgaps=False,
        line={"color": PALETTE["blue"], "width": 2},
    ))
    index_chart.add_hline(y=50, line_dash="dot", line_color=PALETTE["muted"], annotation_text="Neutral score")
    index_chart.update_layout(template="plotly_white", height=430, title=f"{selected_sector} sentiment index (gaps preserved)", xaxis_title="Date", yaxis_title="Index (0–100)", hovermode="x unified")
    index_chart.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")
    _render_plotly(index_chart, key="sentiment_index_chart")
    coverage_chart = go.Figure(go.Scatter(
        x=sentiment_series["date"],
        y=sentiment_series["coverage"],
        mode="lines",
        name="Coverage",
        connectgaps=False,
        line={"color": PALETTE["orange"], "width": 1.8},
        fill="tozeroy",
        fillcolor="rgba(217,119,69,.16)",
    ))
    coverage_chart.update_layout(template="plotly_white", height=330, title="Eligible-ticker news coverage", xaxis_title="Date", yaxis_title="Coverage", showlegend=False)
    coverage_chart.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")
    coverage_chart.update_yaxes(tickformat=".0%", range=[0, 1])
    _render_plotly(coverage_chart, key="sentiment_coverage_chart")
    if show_causal:
        causal_chart = go.Figure(go.Scatter(
            x=sentiment_series["date"],
            y=sentiment_series["causal_z"],
            mode="lines",
            name="Causal source-day z-score",
            connectgaps=False,
            line={"color": PALETTE["cyan"], "width": 1.8},
        ))
        causal_chart.add_hline(y=0, line_dash="dot", line_color=PALETTE["muted"])
        causal_chart.update_layout(template="plotly_white", height=330, title="Causal expanding z-score — separate from the descriptive index", xaxis_title="Date", yaxis_title="Causal z-score")
        causal_chart.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y-%m-%d")
        _render_plotly(causal_chart, key="sentiment_causal_chart")
    snapshot = app_utils.latest_sector_sentiment_snapshot(
        artifacts.sector_sentiment_index, model=selected_model
    )
    snapshot_date = snapshot["date"].iloc[0].date().isoformat()
    st.subheader(f"Latest sector snapshot · {snapshot_date}")
    st.caption("Missing index values remain missing; the app does not replace missing news with 50.")
    snapshot_display = _format_display_dates(snapshot.rename(columns={
            "date": "Date", "sector": "Sector", "headline_count": "Headlines",
            "observed_ticker_count": "Observed tickers",
            "eligible_ticker_count": "Eligible tickers", "coverage": "Coverage",
            "index_0_100": "Index (0–100)", "causal_z": "Causal z-score",
        }), ["Date"])
    st.dataframe(
        snapshot_display,
        hide_index=True,
        width="stretch",
        column_config={
            "Date": st.column_config.TextColumn(width="small"),
            "Coverage": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.info(
        "Rule A maps a headline's UTC calendar date to the same observed equity date or the next one. "
        "Trading use is lagged one additional equity day. No supplied headline means missing coverage, "
        "not neutral sentiment. The finance model uses the frozen approved finance lexicon."
    )


with tab_fusion:
    st.header("Fusion Evidence")
    fusion_summary = app_utils.base_vs_augmented_fusion_summary(
        artifacts.fusion_comparison
    )
    st.warning(fusion_summary["summary_text"])
    st.caption(
        f"Identical OOS comparison: {fusion_summary['common_first_date'].date().isoformat()} to "
        f"{fusion_summary['common_last_date'].date().isoformat()} · {fusion_summary['observations']:,} observations. "
        "This sample is not evidence that either fund is universally better."
    )
    fusion_table = artifacts.fusion_comparison[[
        "fund_id", "cumulative_return_net", "annualised_return_net",
        "annualised_volatility_net", "sharpe_net", "max_drawdown_net",
        "total_turnover", "total_trading_cost", "tracking_error_versus_base",
        "correlation_with_base",
    ]].copy()
    fusion_table["fund_id"] = fusion_table["fund_id"].map(labels)
    st.dataframe(
        fusion_table.rename(columns={
            "fund_id": "Fund", "cumulative_return_net": "Net cumulative return",
            "annualised_return_net": "Net annualised return",
            "annualised_volatility_net": "Net annualised volatility",
            "sharpe_net": "Net Sharpe", "max_drawdown_net": "Net maximum drawdown",
            "total_turnover": "Total turnover", "total_trading_cost": "Trading cost",
            "tracking_error_versus_base": "Tracking error vs base",
            "correlation_with_base": "Correlation with base",
        }),
        hide_index=True,
        width="stretch",
    )
    fusion_ids = ["equity_risk_parity", "equity_risk_parity_sentiment"]
    fusion_returns = artifacts.fund_returns.loc[
        artifacts.fund_returns["fund_id"].isin(fusion_ids)
    ].copy()
    fusion_returns["Fund"] = fusion_returns["fund_id"].map(labels)
    fusion_left, fusion_right = st.columns(2)
    with fusion_left:
        _render_plotly(
            _line_chart(fusion_returns, x="date", y="growth_net", color="Fund", title="Net growth of $1", y_title="Growth of $1"),
            key="fusion_growth",
        )
    with fusion_right:
        _render_plotly(
            _line_chart(fusion_returns, x="date", y="drawdown_net", color="Fund", title="Net drawdown", y_title="Drawdown", percent_axis=True),
            key="fusion_drawdown",
        )
    cost_comparison = artifacts.fusion_comparison[["fund_id", "total_turnover", "total_trading_cost"]].copy()
    cost_comparison["Fund"] = cost_comparison["fund_id"].map(labels)
    cost_long = cost_comparison.melt(
        id_vars=["Fund"], value_vars=["total_turnover", "total_trading_cost"],
        var_name="Measure", value_name="Value",
    )
    cost_long["Measure"] = cost_long["Measure"].map({
        "total_turnover": "Total turnover",
        "total_trading_cost": "Trading cost",
    })
    cost_chart = px.bar(
        cost_long, x="Fund", y="Value", color="Measure", barmode="group",
        title="Turnover and recorded fund-level trading cost",
        color_discrete_map={"Total turnover": PALETTE["blue"], "Trading cost": PALETTE["orange"]},
    )
    cost_chart.update_layout(template="plotly_white", height=420, legend_title_text="")
    cost_chart.update_yaxes(tickformat=".2%")
    _render_plotly(cost_chart, key="fusion_costs")

    st.subheader("Sector multiplier activity")
    st.caption("Grey × marks are missing/no-tilt multiplier 1.0; coloured points are active fixed-rule multipliers.")
    st.image(
        str(RESULTS / "figures/fusion_sector_multiplier_activity.png"),
        caption="Fixed coverage-aware multipliers at target effective dates. Legend is outside the data region.",
        width="stretch",
    )
    st.markdown('<div class="target-label">Latest target weights from the most recent rebalance</div>', unsafe_allow_html=True)
    latest_fusion = artifacts.fusion_current_holdings.copy()
    latest_date = latest_fusion["as_of_date"].max().date().isoformat()
    st.caption(f"Base versus augmented target effective date: {latest_date}. Not live market holdings.")
    largest_changes = latest_fusion.reindex(
        latest_fusion["weight_change"].abs().sort_values(ascending=False).index
    ).head(15).sort_values("weight_change")
    change_chart = px.bar(
        largest_changes,
        x="weight_change",
        y="ticker",
        orientation="h",
        color="weight_change",
        color_continuous_scale=[PALETTE["red"], "#F7F7F7", PALETTE["blue"]],
        color_continuous_midpoint=0,
        title="Largest latest target-weight changes",
    )
    change_chart.update_layout(template="plotly_white", height=500, coloraxis_showscale=False)
    change_chart.update_xaxes(tickformat=".2%", title="Augmented minus base target weight")
    change_chart.update_yaxes(title="")
    _render_plotly(change_chart, key="fusion_latest_changes")
    latest_fusion_display = _format_display_dates(
        latest_fusion, ["as_of_date", "latest_signal_source_date"]
    )
    st.dataframe(
        latest_fusion_display,
        hide_index=True,
        width="stretch",
        column_config={
            "as_of_date": st.column_config.TextColumn(width="small"),
            "latest_signal_source_date": st.column_config.TextColumn(width="small"),
            "base_weight": st.column_config.NumberColumn(format="percent"),
            "augmented_weight": st.column_config.NumberColumn(format="percent"),
            "weight_change": st.column_config.NumberColumn(format="percent"),
            "latest_effective_coverage": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.markdown(
        '<div class="disclosure"><b>Interpretation boundary:</b> the overlay underperformed '
        'the base fund in this sample and had higher turnover. The negative result remains visible; '
        'the fixed rule was not retuned, and neither path is presented as universally better.</div>',
        unsafe_allow_html=True,
    )

st.divider()
st.caption(
    "Cross-Asset Allocation Lens · committed precomputed OOS artifacts · educational use only · "
    "no live holdings, personalised advice, or future-performance claim."
)
