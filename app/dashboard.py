#!/usr/bin/env python3
"""Crypto Signal Pro - Trading Platform & Data Dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.bot import BOT_PRESETS, build_order_plan
from app.platform import build_asset_snapshot, build_market_insights


@st.cache_data(ttl=120)
def load_platform_data(currency: str, universe_size: int) -> dict:
    return build_market_insights(vs_currency=currency, universe_size=universe_size)


@st.cache_data(ttl=120)
def load_asset_snapshot(coin_id: str, symbol: str, currency: str) -> dict:
    return build_asset_snapshot(coin_id=coin_id, symbol=symbol, vs_currency=currency, days=14)


def render_header(payload: dict, currency: str) -> None:
    market_df = payload["market"]
    sentiment = payload["sentiment"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tracked Assets", len(market_df))
    c2.metric("Total Market Cap", f"{market_df['market_cap'].sum():,.0f} {currency.upper()}")
    c3.metric("Avg 24h Move", f"{market_df['momentum_24h'].mean():.2f}%")
    c4.metric("Fear & Greed", f"{sentiment['value']} ({sentiment['classification']})")


def render_market_overview(payload: dict, currency: str) -> None:
    market_df = payload["market"]
    st.subheader("Live Market Structure")

    fig = px.scatter(
        market_df.nlargest(min(25, len(market_df)), "market_cap"),
        x="market_cap",
        y="momentum_24h",
        size="total_volume",
        color="volatility_score",
        hover_name="name",
        log_x=True,
        title="Market Cap vs Momentum vs Volatility",
        labels={"market_cap": f"Market Cap ({currency.upper()})", "momentum_24h": "24h %"},
        template="plotly_dark",
    )
    st.plotly_chart(fig, use_container_width=True)

    bot_heatmap = payload["bot_heatmap"]
    st.subheader("Bot Consensus Heatmap")
    st.dataframe(bot_heatmap, use_container_width=True, hide_index=True)


def render_asset_terminal(payload: dict, currency: str) -> None:
    market_df = payload["market"]
    st.subheader("Asset Trading Terminal")
    selected_coin = st.selectbox("Select asset", options=market_df["id"].tolist())
    selected = market_df[market_df["id"] == selected_coin].iloc[0]

    snapshot = load_asset_snapshot(selected_coin, selected["symbol"].upper(), currency)
    ind = snapshot["indicators"]
    latest = ind.iloc[-1]

    chart = go.Figure()
    chart.add_trace(go.Scatter(x=ind["timestamp"], y=ind["close"], mode="lines", name="Close"))
    chart.add_trace(go.Scatter(x=ind["timestamp"], y=ind["ema_20"], mode="lines", name="EMA 20"))
    chart.add_trace(go.Scatter(x=ind["timestamp"], y=ind["sma_20"], mode="lines", name="SMA 20"))
    chart.add_trace(go.Scatter(x=ind["timestamp"], y=ind["bb_upper"], mode="lines", name="BB Upper", line={"dash": "dot"}))
    chart.add_trace(go.Scatter(x=ind["timestamp"], y=ind["bb_lower"], mode="lines", name="BB Lower", line={"dash": "dot"}))
    chart.update_layout(template="plotly_dark", title=f"{selected['name']} Price + Key Indicators", height=420)
    st.plotly_chart(chart, use_container_width=True)

    i1, i2, i3, i4, i5 = st.columns(5)
    i1.metric("RSI (14)", f"{latest['rsi_14']:.2f}")
    i2.metric("MACD", f"{latest['macd']:.4f}")
    i3.metric("Stoch K", f"{latest['stoch_k']:.2f}")
    i4.metric("ATR (14)", f"{latest['atr_14']:.4f}")
    i5.metric("VWAP", f"{latest['vwap']:.4f}")

    st.subheader("Bot Signals")
    st.dataframe(snapshot["bot_signals"], use_container_width=True, hide_index=True)


def render_ai_and_execution(payload: dict, market_df: pd.DataFrame) -> None:
    st.subheader("AI Insights & Execution")
    ai_df = payload["ai_insights"].copy()
    st.dataframe(ai_df.head(20), use_container_width=True, hide_index=True)

    preset_name = st.selectbox("Execution preset", list(BOT_PRESETS.keys()), index=1)
    preset = BOT_PRESETS[preset_name]

    col1, col2, col3 = st.columns(3)
    account_size = col1.number_input("Portfolio size", min_value=100.0, value=15000.0, step=100.0)
    execution_mode = col2.selectbox("Execution mode", ["Paper", "Live-ready webhook"], index=0)
    max_positions = col3.slider("Max positions", 1, 10, int(preset["max_positions"]))

    orders_df = build_order_plan(
        insights_df=ai_df,
        market_df=market_df,
        preset=preset,
        account_size=account_size,
        max_positions=max_positions,
        execution_mode=execution_mode,
    )
    if orders_df.empty:
        st.warning("No orders generated for current preset and market conditions.")
        return

    st.dataframe(orders_df, use_container_width=True, hide_index=True)
    st.code(
        {
            "execution_mode": execution_mode,
            "preset": preset_name,
            "timeframe": preset["timeframe"],
            "orders": orders_df.to_dict(orient="records"),
        },
        language="json",
    )


def main() -> None:
    st.set_page_config(page_title="Crypto Signal Pro Platform", page_icon="📈", layout="wide")
    st.title("📈 Crypto Signal Pro: Trading Platform + Live Data Dashboard")
    st.caption("Live market intelligence, full indicator stack, strategy bots, and execution planning.")

    with st.sidebar:
        st.header("Workspace Controls")
        currency = st.selectbox("Quote currency", ["usd", "eur", "gbp"], index=0)
        universe_size = st.slider("Universe size", 20, 120, 40, 10)

    payload = load_platform_data(currency=currency, universe_size=universe_size)
    market_df = payload["market"]
    if market_df.empty:
        st.error("No market data available.")
        return

    render_header(payload, currency)

    tab1, tab2, tab3 = st.tabs(["Market Dashboard", "Trading Terminal", "Execution Center"])
    with tab1:
        render_market_overview(payload, currency)
    with tab2:
        render_asset_terminal(payload, currency)
    with tab3:
        render_ai_and_execution(payload, market_df)


if __name__ == "__main__":
    main()
