#!/usr/bin/env python3
"""Streamlit dashboard for real-time crypto market data, AI hints, and bot presets.

Data sources:
- CoinGecko public API (open source market data)
- Alternative.me Fear & Greed Index (open sentiment data)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

COINGECKO_API = "https://api.coingecko.com/api/v3"
FEAR_GREED_API = "https://api.alternative.me/fng/"

BOT_PRESETS = {
    "Scalp Pro": {
        "timeframe": "5m",
        "risk_per_trade": 0.75,
        "max_positions": 6,
        "stop_loss_pct": 1.1,
        "take_profit_pct": 2.2,
        "min_signal_score": 65,
    },
    "Intraday Alpha": {
        "timeframe": "15m",
        "risk_per_trade": 1.0,
        "max_positions": 4,
        "stop_loss_pct": 1.8,
        "take_profit_pct": 3.6,
        "min_signal_score": 62,
    },
    "Swing Smart": {
        "timeframe": "4h",
        "risk_per_trade": 1.25,
        "max_positions": 3,
        "stop_loss_pct": 4.0,
        "take_profit_pct": 9.0,
        "min_signal_score": 58,
    },
}


@dataclass
class Insight:
    symbol: str
    score: float
    confidence: str
    action: str
    rationale: str
    risk_note: str


@st.cache_data(ttl=60)
def get_market_data(vs_currency: str, per_page: int) -> pd.DataFrame:
    response = requests.get(
        f"{COINGECKO_API}/coins/markets",
        params={
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "true",
            "price_change_percentage": "24h,7d",
        },
        timeout=20,
    )
    response.raise_for_status()
    data = pd.DataFrame(response.json())
    if data.empty:
        return data

    data["volume_to_mcap"] = data["total_volume"] / data["market_cap"].replace(0, pd.NA)
    data["momentum_24h"] = data["price_change_percentage_24h_in_currency"].fillna(0)
    data["momentum_7d"] = data["price_change_percentage_7d_in_currency"].fillna(0)
    data["trend_strength"] = data["momentum_24h"] * 0.4 + data["momentum_7d"] * 0.6

    def _volatility(sparkline: Dict[str, List[float]]) -> float:
        prices = pd.Series((sparkline or {}).get("price", []), dtype="float64")
        if prices.size < 3:
            return 0.0
        returns = prices.pct_change().dropna()
        if returns.empty:
            return 0.0
        return float(returns.std() * math.sqrt(returns.size)) * 100

    data["volatility_score"] = data["sparkline_in_7d"].apply(_volatility)
    return data


@st.cache_data(ttl=300)
def get_fear_greed() -> Dict[str, str]:
    response = requests.get(FEAR_GREED_API, params={"limit": 1}, timeout=10)
    response.raise_for_status()
    latest = response.json().get("data", [{}])[0]
    return {
        "value": latest.get("value", "N/A"),
        "classification": latest.get("value_classification", "Unknown"),
        "timestamp": latest.get("timestamp", ""),
    }


def classify_confidence(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 50:
        return "Moderate"
    return "Low"


def generate_ai_insight(row: pd.Series, sentiment_value: float) -> Insight:
    trend = float(row["trend_strength"])
    liquidity = float(row["volume_to_mcap"] * 100)
    volatility = float(row["volatility_score"])

    score = 50 + (trend * 1.1) + (liquidity * 1.2) - (volatility * 0.5)
    score += (sentiment_value - 50) * 0.3
    score = max(0, min(100, score))

    if score >= 68:
        action = "Momentum Long Setup"
        rationale = "Trend and liquidity are aligned; staged entries are preferred over all-in execution."
    elif score <= 38:
        action = "Defensive / Mean-Reversion Watch"
        rationale = "Signal quality is weak; protect capital and wait for cleaner structure."
    else:
        action = "Range Trade / Wait for Breakout"
        rationale = "Mixed conditions; favor reduced size with strict invalidation levels."

    if volatility > 20:
        risk_note = "High volatility regime: smaller sizing and wider stops."
    elif volatility < 8:
        risk_note = "Low volatility regime: compression breakout watch."
    else:
        risk_note = "Normal volatility regime: standard risk budget."

    return Insight(
        symbol=row["symbol"].upper(),
        score=round(score, 2),
        confidence=classify_confidence(score),
        action=action,
        rationale=rationale,
        risk_note=risk_note,
    )


def _render_header(sentiment: Dict[str, str], market_df: pd.DataFrame, currency: str) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assets tracked", f"{len(market_df)}")
    c2.metric("Total market cap", f"{market_df['market_cap'].sum():,.0f} {currency.upper()}")
    c3.metric("Average 24h change", f"{market_df['momentum_24h'].mean():.2f}%")
    c4.metric("Fear & Greed", f"{sentiment['value']} ({sentiment['classification']})")


def _render_market_tab(market_df: pd.DataFrame, currency: str) -> None:
    st.subheader("Market Structure")
    chart_df = market_df.nlargest(15, "market_cap").copy()

    scatter = px.scatter(
        chart_df,
        x="market_cap",
        y="momentum_24h",
        size="total_volume",
        color="volatility_score",
        hover_name="name",
        log_x=True,
        labels={
            "market_cap": f"Market Cap ({currency.upper()})",
            "momentum_24h": "24h Momentum %",
            "volatility_score": "7d Volatility",
        },
        title="Market Cap vs Momentum vs Volatility",
        template="plotly_dark",
    )
    st.plotly_chart(scatter, use_container_width=True)

    selected = st.selectbox("Inspect asset", options=market_df["id"].tolist(), index=0)
    selected_row = market_df.loc[market_df["id"] == selected].iloc[0]

    prices = selected_row.get("sparkline_in_7d", {}).get("price", [])
    if prices:
        spark_df = pd.DataFrame({"point": range(len(prices)), "price": prices})
        line = go.Figure(go.Scatter(x=spark_df["point"], y=spark_df["price"], mode="lines"))
        line.update_layout(
            title=f"{selected_row['name']} 7D Microtrend",
            xaxis_title="Observation",
            yaxis_title=f"Price ({currency.upper()})",
            height=320,
            template="plotly_dark",
        )
        st.plotly_chart(line, use_container_width=True)


def _render_ai_tab(market_df: pd.DataFrame, sentiment_value: float) -> pd.DataFrame:
    st.subheader("AI Tips & Hints")
    top_candidates = market_df.sort_values("trend_strength", ascending=False).head(10)
    insights = [generate_ai_insight(row, sentiment_value) for _, row in top_candidates.iterrows()]
    insights_df = pd.DataFrame([ins.__dict__ for ins in insights]).sort_values("score", ascending=False)

    st.dataframe(insights_df, use_container_width=True, hide_index=True)
    top = insights_df.iloc[0]
    st.success(
        f"Top setup: **{top['symbol']}** • {top['action']} • Confidence: **{top['confidence']}** • Score: **{top['score']}**"
    )
    return insights_df


def _render_bot_tab(insights_df: pd.DataFrame, market_df: pd.DataFrame, currency: str) -> None:
    st.subheader("Auto Trade Bot Console")
    st.caption("Professional execution planning with configurable presets. Simulation mode only.")

    preset_name = st.selectbox("Strategy preset", list(BOT_PRESETS.keys()), index=1)
    preset = BOT_PRESETS[preset_name]

    col1, col2, col3 = st.columns(3)
    account_size = col1.number_input("Portfolio size", min_value=100.0, value=10000.0, step=100.0)
    execution_mode = col2.selectbox("Execution mode", ["Paper", "Live-ready webhook"], index=0)
    max_positions = col3.slider("Max simultaneous positions", 1, 10, int(preset["max_positions"]))

    with st.expander("Preset risk profile", expanded=True):
        st.json(
            {
                **preset,
                "execution_mode": execution_mode,
                "max_positions_override": max_positions,
            }
        )

    tradable = insights_df[insights_df["score"] >= preset["min_signal_score"]].head(max_positions).copy()
    if tradable.empty:
        st.warning("No assets meet current preset threshold. Lower min score or wait for next cycle.")
        return

    price_map = market_df.set_index("symbol")["current_price"].to_dict()
    orders = []
    for _, row in tradable.iterrows():
        symbol = row["symbol"].lower()
        entry = float(price_map.get(symbol, 0.0))
        if entry <= 0:
            continue
        risk_amount = account_size * (preset["risk_per_trade"] / 100)
        stop = entry * (1 - preset["stop_loss_pct"] / 100)
        target = entry * (1 + preset["take_profit_pct"] / 100)
        unit_risk = max(entry - stop, 1e-8)
        quantity = risk_amount / unit_risk

        orders.append(
            {
                "symbol": row["symbol"],
                "signal_score": row["score"],
                "entry": round(entry, 6),
                "stop_loss": round(stop, 6),
                "take_profit": round(target, 6),
                "position_size_units": round(quantity, 4),
                "action": "BUY",
                "execution_mode": execution_mode,
            }
        )

    if not orders:
        st.warning("Could not build orders from current data.")
        return

    orders_df = pd.DataFrame(orders).sort_values("signal_score", ascending=False)
    st.dataframe(orders_df, use_container_width=True, hide_index=True)

    st.code(
        f"""POST /trade/webhook
{{
  "preset": "{preset_name}",
  "timeframe": "{preset['timeframe']}",
  "orders": {orders_df.head(3).to_dict(orient='records')}
}}""",
        language="json",
    )

    st.info(
        "Bot workflow: signal filter → risk sizing → stop/target generation → webhook payload. "
        "Connect this payload to your exchange executor service for real trading."
    )


def build_dashboard() -> None:
    st.set_page_config(page_title="Crypto Signal Pro Dashboard", page_icon="📊", layout="wide")
    st.title("📊 Crypto Signal Pro")
    st.caption(
        "Real-time open data intelligence with AI hints and professional auto-trade planning. "
        "Educational only; not financial advice."
    )

    with st.sidebar:
        st.header("Global Controls")
        currency = st.selectbox("Quote currency", ["usd", "eur", "gbp"], index=0)
        coin_count = st.slider("Assets to load", 20, 120, 40, 10)
        st.toggle("Auto-refresh every minute", value=True, disabled=True)

    try:
        market_df = get_market_data(currency, coin_count)
        sentiment = get_fear_greed()
    except requests.RequestException as exc:
        st.error(f"Failed to load upstream data: {exc}")
        return

    if market_df.empty:
        st.warning("No market data available from provider.")
        return

    fg_value = float(sentiment["value"]) if str(sentiment["value"]).isdigit() else 50.0

    _render_header(sentiment, market_df, currency)

    tab_market, tab_ai, tab_bot = st.tabs(["Market", "AI Insights", "Auto Trade Bot"])
    with tab_market:
        _render_market_tab(market_df, currency)
    with tab_ai:
        insights_df = _render_ai_tab(market_df, fg_value)
    with tab_bot:
        if "insights_df" not in locals():
            insights_df = _render_ai_tab(market_df, fg_value)
        _render_bot_tab(insights_df, market_df, currency)


if __name__ == "__main__":
    build_dashboard()
