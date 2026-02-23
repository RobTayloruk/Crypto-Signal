"""Trading bots and signal engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd


@dataclass
class BotSignal:
    symbol: str
    bot: str
    side: str
    confidence: str
    score: float
    reason: str


class BaseBot:
    name = "BaseBot"

    def evaluate(self, symbol: str, ind: pd.DataFrame) -> BotSignal:
        raise NotImplementedError


class TrendBot(BaseBot):
    name = "TrendBot"

    def evaluate(self, symbol: str, ind: pd.DataFrame) -> BotSignal:
        row = ind.iloc[-1]
        score = 50.0
        score += 12 if row["close"] > row["ema_20"] else -10
        score += 10 if row["macd"] > row["signal"] else -8
        score += 8 if row["rsi_14"] > 50 else -6
        side = "BUY" if score >= 55 else "HOLD"
        conf = "High" if score >= 70 else "Moderate" if score >= 55 else "Low"
        return BotSignal(symbol, self.name, side, conf, round(max(0, min(100, score)), 2), "Trend-following EMA+MACD+RSI consensus")


class MeanReversionBot(BaseBot):
    name = "MeanReversionBot"

    def evaluate(self, symbol: str, ind: pd.DataFrame) -> BotSignal:
        row = ind.iloc[-1]
        score = 50.0
        score += 15 if row["rsi_14"] < 35 else -8
        score += 12 if row["close"] < row["bb_lower"] else -7
        score += 6 if row["stoch_k"] < 20 else -5
        side = "BUY" if score >= 60 else "HOLD"
        conf = "High" if score >= 75 else "Moderate" if score >= 60 else "Low"
        return BotSignal(symbol, self.name, side, conf, round(max(0, min(100, score)), 2), "Oversold reversion with Bollinger and Stochastic confirmation")


class BreakoutBot(BaseBot):
    name = "BreakoutBot"

    def evaluate(self, symbol: str, ind: pd.DataFrame) -> BotSignal:
        row = ind.iloc[-1]
        prev = ind.iloc[-2] if len(ind) > 1 else row
        score = 50.0
        score += 14 if row["close"] > row["bb_upper"] else -6
        score += 10 if row["volume"] > prev["volume"] else -4
        score += 8 if row["close"] > row["vwap"] else -5
        side = "BUY" if score >= 62 else "HOLD"
        conf = "High" if score >= 76 else "Moderate" if score >= 62 else "Low"
        return BotSignal(symbol, self.name, side, conf, round(max(0, min(100, score)), 2), "Breakout momentum above bands with volume/VWAP confirmation")


def run_bot_suite(symbol: str, indicator_df: pd.DataFrame) -> pd.DataFrame:
    bots: List[BaseBot] = [TrendBot(), MeanReversionBot(), BreakoutBot()]
    signals = [bot.evaluate(symbol, indicator_df).__dict__ for bot in bots]
    return pd.DataFrame(signals).sort_values("score", ascending=False)


def aggregate_symbol_score(bot_signals: pd.DataFrame) -> Dict[str, float]:
    if bot_signals.empty:
        return {"aggregate_score": 0.0, "buy_votes": 0.0}
    return {
        "aggregate_score": float(bot_signals["score"].mean()),
        "buy_votes": float((bot_signals["side"] == "BUY").sum()),
    }
