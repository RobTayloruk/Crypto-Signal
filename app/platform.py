"""Trading platform orchestration: live market + indicators + bots + insights."""

from __future__ import annotations

from typing import Dict

import pandas as pd

from app.bots import aggregate_symbol_score, run_bot_suite
from app.indicators import with_indicators
from app.market_data import get_ohlcv, get_universe
from app.signals import generate_ai_insight
from app.data_sources import get_fear_greed


def build_asset_snapshot(coin_id: str, symbol: str, vs_currency: str, days: int = 14) -> Dict[str, object]:
    ohlcv = get_ohlcv(coin_id=coin_id, vs_currency=vs_currency, days=days)
    indicators = with_indicators(ohlcv)
    bot_signals = run_bot_suite(symbol=symbol, indicator_df=indicators)
    summary = aggregate_symbol_score(bot_signals)
    return {
        "ohlcv": ohlcv,
        "indicators": indicators,
        "bot_signals": bot_signals,
        "summary": summary,
    }


def build_market_insights(vs_currency: str, universe_size: int) -> Dict[str, object]:
    market_df = get_universe(vs_currency=vs_currency, size=universe_size)
    sentiment = get_fear_greed(allow_fallback=True)
    sentiment_value = float(sentiment.get("value", "50"))

    ai_insights = pd.DataFrame(
        [generate_ai_insight(row, sentiment_value).__dict__ for _, row in market_df.iterrows()]
    ).sort_values("score", ascending=False)

    top = market_df.sort_values("market_cap", ascending=False).head(8)
    rows = []
    for _, row in top.iterrows():
        snap = build_asset_snapshot(row["id"], row["symbol"].upper(), vs_currency, days=7)
        rows.append(
            {
                "symbol": row["symbol"].upper(),
                "name": row["name"],
                "aggregate_score": round(snap["summary"]["aggregate_score"], 2),
                "buy_votes": int(snap["summary"]["buy_votes"]),
            }
        )

    bot_heatmap = pd.DataFrame(rows).sort_values("aggregate_score", ascending=False)

    return {
        "market": market_df,
        "sentiment": sentiment,
        "ai_insights": ai_insights,
        "bot_heatmap": bot_heatmap,
    }
