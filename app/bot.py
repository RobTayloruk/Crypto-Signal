"""Auto-trade preset and order planning utilities."""

from __future__ import annotations

from typing import Dict

import pandas as pd

BOT_PRESETS: Dict[str, Dict[str, float]] = {
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


def build_order_plan(insights_df: pd.DataFrame, market_df: pd.DataFrame, preset: Dict[str, float], account_size: float, max_positions: int, execution_mode: str) -> pd.DataFrame:
    tradable = insights_df[insights_df["score"] >= preset["min_signal_score"]].head(max_positions).copy()
    if tradable.empty:
        return pd.DataFrame()

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

        orders.append(
            {
                "symbol": row["symbol"],
                "signal_score": row["score"],
                "entry": round(entry, 6),
                "stop_loss": round(stop, 6),
                "take_profit": round(target, 6),
                "position_size_units": round(risk_amount / unit_risk, 4),
                "action": "BUY",
                "execution_mode": execution_mode,
            }
        )

    return pd.DataFrame(orders).sort_values("signal_score", ascending=False) if orders else pd.DataFrame()
