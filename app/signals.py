"""Signal generation for deterministic AI-style crypto insights."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Insight:
    symbol: str
    score: float
    confidence: str
    action: str
    rationale: str
    risk_note: str


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
        rationale = "Trend and liquidity align; use staged entries and trail risk."
    elif score <= 38:
        action = "Defensive / Mean-Reversion Watch"
        rationale = "Signal quality is weak; preserve capital and wait for confirmation."
    else:
        action = "Range Trade / Breakout Watch"
        rationale = "Conditions are mixed; reduce size and define invalidation clearly."

    if volatility > 20:
        risk_note = "High volatility: smaller size, wider stops, lower leverage."
    elif volatility < 8:
        risk_note = "Low volatility: monitor compression and breakout triggers."
    else:
        risk_note = "Normal volatility: keep standard risk allocation."

    return Insight(
        symbol=row["symbol"].upper(),
        score=round(score, 2),
        confidence=classify_confidence(score),
        action=action,
        rationale=rationale,
        risk_note=risk_note,
    )
