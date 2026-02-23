#!/usr/bin/env python3
"""Streamlit dashboard for real-time crypto market data and AI trade hints.

Data sources:
- CoinGecko public API (open source market data)
- Alternative.me Fear & Greed Index (open sentiment data)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

COINGECKO_API = "https://api.coingecko.com/api/v3"
FEAR_GREED_API = "https://api.alternative.me/fng/"


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
    """Fetch top market data from CoinGecko with sparkline for trend analysis."""
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
    """Fetch market sentiment from Alternative.me Fear & Greed API."""
    response = requests.get(FEAR_GREED_API, params={"limit": 1}, timeout=10)
    response.raise_for_status()
    payload = response.json()
    latest = payload.get("data", [{}])[0]
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
    """Generate a deterministic AI-style trade hint using market features."""
    trend = float(row["trend_strength"])
    liquidity = float(row["volume_to_mcap"] * 100)
    volatility = float(row["volatility_score"])

    score = 50 + (trend * 1.1) + (liquidity * 1.2) - (volatility * 0.5)
    score += (sentiment_value - 50) * 0.3
    score = max(0, min(100, score))

    if score >= 68:
        action = "Momentum Long Setup"
        rationale = (
            "Positive trend acceleration with supportive liquidity. "
            "Consider scaling entries instead of a single full-size position."
        )
    elif score <= 38:
        action = "Defensive / Mean-Reversion Watch"
        rationale = (
            "Risk-adjusted profile is weak. Protect capital, avoid chasing moves, "
            "and wait for structure confirmation."
        )
    else:
        action = "Range Trade / Wait for Breakout"
        rationale = (
            "Signal quality is mixed. Focus on clear invalidation levels and "
            "smaller position sizing."
        )

    if volatility > 20:
        risk_note = "High volatility regime: prefer smaller size and wider stops."
    elif volatility < 8:
        risk_note = "Low volatility regime: watch for breakout compression setups."
    else:
        risk_note = "Normal volatility regime: maintain standard risk allocation."

    return Insight(
        symbol=row["symbol"].upper(),
        score=round(score, 2),
        confidence=classify_confidence(score),
        action=action,
        rationale=rationale,
        risk_note=risk_note,
    )


def build_dashboard() -> None:
    st.set_page_config(page_title="Crypto Signal AI Dashboard", layout="wide")
    st.title("📈 Crypto Signal: Real-Time AI Dashboard")
    st.caption(
        "Open-source data powered by CoinGecko + Alternative.me. "
        "Insights are educational and not financial advice."
    )

    with st.sidebar:
        st.header("Controls")
        currency = st.selectbox("Quote currency", options=["usd", "eur", "gbp"], index=0)
        coin_count = st.slider("Top assets to load", min_value=10, max_value=100, value=25, step=5)
        st.button("Refresh data")

    try:
        market_df = get_market_data(currency, coin_count)
        sentiment = get_fear_greed()
    except requests.RequestException as exc:
        st.error(f"Failed to load remote market data: {exc}")
        return

    if market_df.empty:
        st.warning("No market data returned from provider.")
        return

    fg_value = float(sentiment["value"]) if str(sentiment["value"]).isdigit() else 50.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assets tracked", f"{len(market_df)}")
    c2.metric("Total market cap", f"{market_df['market_cap'].sum():,.0f} {currency.upper()}")
    c3.metric("Avg 24h change", f"{market_df['momentum_24h'].mean():.2f}%")
    c4.metric("Fear & Greed", f"{sentiment['value']} ({sentiment['classification']})")

    chart_df = market_df.nlargest(15, "market_cap").copy()
    fig = px.scatter(
        chart_df,
        x="market_cap",
        y="momentum_24h",
        size="total_volume",
        color="volatility_score",
        hover_name="name",
        log_x=True,
        labels={
            "market_cap": f"Market Cap ({currency.upper()})",
            "momentum_24h": "24h Change %",
            "volatility_score": "7d Volatility",
        },
        title="Market Structure: Size vs Momentum vs Volatility",
    )
    st.plotly_chart(fig, use_container_width=True)

    selected = st.selectbox("Inspect asset", options=market_df["id"].tolist(), index=0)
    selected_row = market_df.loc[market_df["id"] == selected].iloc[0]

    sparkline = selected_row.get("sparkline_in_7d", {}).get("price", [])
    if sparkline:
        spark_df = pd.DataFrame({"index": range(len(sparkline)), "price": sparkline})
        line_fig = go.Figure(go.Scatter(x=spark_df["index"], y=spark_df["price"], mode="lines"))
        line_fig.update_layout(
            title=f"{selected_row['name']} 7d Microtrend",
            xaxis_title="Points",
            yaxis_title=f"Price ({currency.upper()})",
            height=320,
        )
        st.plotly_chart(line_fig, use_container_width=True)

    st.subheader("🤖 AI Trade Tips")
    top_candidates = market_df.sort_values("trend_strength", ascending=False).head(8)
    insights = [generate_ai_insight(row, fg_value) for _, row in top_candidates.iterrows()]
    insights_df = pd.DataFrame([ins.__dict__ for ins in insights]).sort_values("score", ascending=False)
    st.dataframe(insights_df, use_container_width=True, hide_index=True)

    best = insights_df.iloc[0]
    st.info(
        f"Top opportunity this cycle: **{best['symbol']}** | "
        f"Action: **{best['action']}** | Confidence: **{best['confidence']}**"
    )


if __name__ == "__main__":
    build_dashboard()
