import pandas as pd

from app.bot import BOT_PRESETS, build_order_plan
from app.data_sources import get_fear_greed, get_market_data
from app.signals import classify_confidence, generate_ai_insight


def test_confidence_bands():
    assert classify_confidence(75) == "High"
    assert classify_confidence(55) == "Moderate"
    assert classify_confidence(40) == "Low"


def test_fallback_data_loads():
    df = get_market_data(allow_fallback=True)
    assert not df.empty
    assert {"trend_strength", "volatility_score", "volume_to_mcap"}.issubset(df.columns)


def test_insight_and_order_plan_generation():
    market_df = get_market_data(allow_fallback=True)
    sentiment = float(get_fear_greed(allow_fallback=True)["value"])
    insights_df = pd.DataFrame(
        [generate_ai_insight(row, sentiment).__dict__ for _, row in market_df.iterrows()]
    )
    preset = BOT_PRESETS["Intraday Alpha"]
    orders = build_order_plan(insights_df, market_df, preset, account_size=10000, max_positions=3, execution_mode="Paper")
    assert isinstance(orders, pd.DataFrame)
