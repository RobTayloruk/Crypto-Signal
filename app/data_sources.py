"""Data providers and fallback fixtures for the Crypto Signal dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd
import requests

COINGECKO_API = "https://api.coingecko.com/api/v3"
FEAR_GREED_API = "https://api.alternative.me/fng/"


class DataProviderError(RuntimeError):
    """Raised when remote data cannot be loaded and no fallback is allowed."""


def _compute_features(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return data

    data = data.copy()
    data["volume_to_mcap"] = data["total_volume"] / data["market_cap"].replace(0, pd.NA)
    data["momentum_24h"] = data["price_change_percentage_24h_in_currency"].fillna(0)
    data["momentum_7d"] = data["price_change_percentage_7d_in_currency"].fillna(0)
    data["trend_strength"] = data["momentum_24h"] * 0.4 + data["momentum_7d"] * 0.6

    def _volatility(prices_wrap: Dict[str, List[float]]) -> float:
        prices = pd.Series((prices_wrap or {}).get("price", []), dtype="float64")
        if prices.size < 3:
            return 0.0
        returns = prices.pct_change().dropna()
        if returns.empty:
            return 0.0
        return float(returns.std() * (returns.size ** 0.5)) * 100

    data["volatility_score"] = data["sparkline_in_7d"].apply(_volatility)
    return data


def _fallback_market_data() -> pd.DataFrame:
    rows = [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 67000,
            "market_cap": 1300000000000,
            "total_volume": 29000000000,
            "price_change_percentage_24h_in_currency": 1.8,
            "price_change_percentage_7d_in_currency": 4.1,
            "sparkline_in_7d": {"price": [62500, 63100, 63900, 64200, 65100, 66100, 67000]},
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 3300,
            "market_cap": 390000000000,
            "total_volume": 16000000000,
            "price_change_percentage_24h_in_currency": 2.4,
            "price_change_percentage_7d_in_currency": 6.3,
            "sparkline_in_7d": {"price": [3020, 3080, 3120, 3150, 3210, 3260, 3300]},
        },
        {
            "id": "solana",
            "symbol": "sol",
            "name": "Solana",
            "current_price": 152,
            "market_cap": 69000000000,
            "total_volume": 3200000000,
            "price_change_percentage_24h_in_currency": -0.6,
            "price_change_percentage_7d_in_currency": 3.9,
            "sparkline_in_7d": {"price": [141, 144, 149, 146, 150, 154, 152]},
        },
    ]
    return _compute_features(pd.DataFrame(rows))


def get_market_data(vs_currency: str = "usd", per_page: int = 40, allow_fallback: bool = True) -> pd.DataFrame:
    try:
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
        return _compute_features(pd.DataFrame(response.json()))
    except requests.RequestException as exc:
        if allow_fallback:
            return _fallback_market_data()
        raise DataProviderError(str(exc)) from exc


def get_fear_greed(allow_fallback: bool = True) -> Dict[str, str]:
    try:
        response = requests.get(FEAR_GREED_API, params={"limit": 1}, timeout=10)
        response.raise_for_status()
        latest = response.json().get("data", [{}])[0]
        return {
            "value": latest.get("value", "50"),
            "classification": latest.get("value_classification", "Neutral"),
            "timestamp": latest.get("timestamp", ""),
            "source": "live",
        }
    except requests.RequestException:
        if allow_fallback:
            return {
                "value": "50",
                "classification": "Neutral",
                "timestamp": str(int(datetime.utcnow().timestamp())),
                "source": "fallback",
            }
        raise
