#!/usr/bin/env python3
"""Crypto Signal Pro Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.bot import BOT_PRESETS, build_order_plan
from app.data_sources import get_fear_greed, get_market_data
from app.signals import generate_ai_insight


@st.cache_data(ttl=60)
def load_market_data(vs_currency: str, per_page: int) -> pd.DataFrame:
    return get_market_data(vs_currency=vs_currency, per_page=per_page, allow_fallback=True)


@st.cache_data(ttl=300)
def load_sentiment() -> dict:
    return get_fear_greed(allow_fallback=True)


def render_header(sentiment: dict, market_df: pd.DataFrame, currency: str) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assets", f"{len(market_df)}")
    c2.metric("Total Market Cap", f"{market_df['market_cap'].sum():,.0f} {currency.upper()}")
    c3.metric("Avg 24h Change", f"{market_df['momentum_24h'].mean():.2f}%")
    source = sentiment.get("source", "live")
    c4.metric("Fear & Greed", f"{sentiment['value']} ({sentiment['classification']})", help=f"Source: {source}")


def render_market_tab(market_df: pd.DataFrame, currency: str) -> None:
    st.subheader("Market Structure")
    chart_df = market_df.nlargest(min(15, len(market_df)), "market_cap")

    fig = px.scatter(
        chart_df,
        x="market_cap",
        y="momentum_24h",
        size="total_volume",
        color="volatility_score",
        hover_name="name",
        log_x=True,
        title="Market Cap vs Momentum vs Volatility",
        labels={"market_cap": f"Market Cap ({currency.upper()})", "momentum_24h": "24h Change %"},
        template="plotly_dark",
    )
    st.plotly_chart(fig, use_container_width=True)

    selected = st.selectbox("Inspect asset", options=market_df["id"].tolist(), index=0)
    row = market_df.loc[market_df["id"] == selected].iloc[0]

    spark = row.get("sparkline_in_7d", {}).get("price", [])
    if spark:
        spark_df = pd.DataFrame({"point": range(len(spark)), "price": spark})
        line = go.Figure(go.Scatter(x=spark_df["point"], y=spark_df["price"], mode="lines"))
        line.update_layout(
            title=f"{row['name']} 7D Microtrend",
            xaxis_title="Observation",
            yaxis_title=f"Price ({currency.upper()})",
            template="plotly_dark",
            height=320,
        )
        st.plotly_chart(line, use_container_width=True)


def build_insights(market_df: pd.DataFrame, sentiment_value: float) -> pd.DataFrame:
    top_candidates = market_df.sort_values("trend_strength", ascending=False).head(min(10, len(market_df)))
    insights = [generate_ai_insight(row, sentiment_value).__dict__ for _, row in top_candidates.iterrows()]
    return pd.DataFrame(insights).sort_values("score", ascending=False)


def render_ai_tab(insights_df: pd.DataFrame) -> None:
    st.subheader("AI Trade Tips")
    st.dataframe(insights_df, use_container_width=True, hide_index=True)
    top = insights_df.iloc[0]
    st.success(f"Top setup: {top['symbol']} • {top['action']} • Confidence: {top['confidence']} • Score: {top['score']}")


def render_bot_tab(insights_df: pd.DataFrame, market_df: pd.DataFrame) -> None:
    st.subheader("Auto Trade Bot")
    st.caption("Preset-driven execution planner. Use Paper mode by default.")

    preset_name = st.selectbox("Strategy preset", list(BOT_PRESETS.keys()), index=1)
    preset = BOT_PRESETS[preset_name]

    col1, col2, col3 = st.columns(3)
    account_size = col1.number_input("Portfolio size", min_value=100.0, value=10000.0, step=100.0)
    execution_mode = col2.selectbox("Execution mode", ["Paper", "Live-ready webhook"], index=0)
    max_positions = col3.slider("Max positions", 1, 10, int(preset["max_positions"]))

    orders_df = build_order_plan(insights_df, market_df, preset, account_size, max_positions, execution_mode)
    if orders_df.empty:
        st.warning("No assets currently match this preset's minimum signal score.")
        return

    st.dataframe(orders_df, use_container_width=True, hide_index=True)
    st.code(
        {
            "preset": preset_name,
            "timeframe": preset["timeframe"],
            "orders": orders_df.to_dict(orient="records"),
        },
        language="json",
    )


def main() -> None:
    st.set_page_config(page_title="Crypto Signal Pro", page_icon="📊", layout="wide")
    st.title("📊 Crypto Signal Pro Dashboard")
    st.caption("Real-time open-data crypto analytics with AI hints and auto-trade planning.")

    with st.sidebar:
        st.header("Controls")
        currency = st.selectbox("Quote currency", ["usd", "eur", "gbp"], index=0)
        coin_count = st.slider("Assets to load", 20, 120, 40, 10)

    market_df = load_market_data(currency, coin_count)
    sentiment = load_sentiment()
    sentiment_value = float(sentiment.get("value", "50"))

    if market_df.empty:
        st.error("No market data available.")
        return

    render_header(sentiment, market_df, currency)
    insights_df = build_insights(market_df, sentiment_value)

    tab_market, tab_ai, tab_bot = st.tabs(["Market", "AI Insights", "Auto Trade Bot"])
    with tab_market:
        render_market_tab(market_df, currency)
    with tab_ai:
        render_ai_tab(insights_df)
    with tab_bot:
        render_bot_tab(insights_df, market_df)


if __name__ == "__main__":
    main()
