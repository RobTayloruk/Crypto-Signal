import pandas as pd

from app.bot import BOT_PRESETS, build_order_plan
from app.bots import run_bot_suite
from app.indicators import with_indicators
from app.market_data import get_ohlcv
from app.platform import build_asset_snapshot, build_market_insights
from app.signals import classify_confidence, generate_ai_insight


def test_confidence_bands():
    assert classify_confidence(80) == "High"
    assert classify_confidence(60) == "Moderate"
    assert classify_confidence(10) == "Low"


def test_indicator_stack_builds():
    ohlcv = get_ohlcv("bitcoin", days=2)
    ind = with_indicators(ohlcv)
    required = {"rsi_14", "macd", "signal", "bb_upper", "atr_14", "stoch_k", "obv", "vwap"}
    assert required.issubset(ind.columns)


def test_bot_suite_outputs_signals():
    ohlcv = get_ohlcv("bitcoin", days=2)
    ind = with_indicators(ohlcv)
    signals = run_bot_suite("BTC", ind)
    assert len(signals) == 3
    assert {"bot", "side", "score"}.issubset(signals.columns)


def test_market_insights_and_orders():
    payload = build_market_insights("usd", 20)
    assert not payload["market"].empty
    assert not payload["ai_insights"].empty

    ai_df = payload["ai_insights"].head(5).copy()
    market_df = payload["market"]
    orders = build_order_plan(ai_df, market_df, BOT_PRESETS["Intraday Alpha"], 10000, 3, "Paper")
    assert isinstance(orders, pd.DataFrame)


def test_asset_snapshot_has_terminal_components():
    snap = build_asset_snapshot("bitcoin", "BTC", "usd", days=7)
    assert not snap["ohlcv"].empty
    assert not snap["indicators"].empty
    assert not snap["bot_signals"].empty
    assert "aggregate_score" in snap["summary"]


def test_ai_insight_shape():
    payload = build_market_insights("usd", 20)
    row = payload["market"].iloc[0]
    ins = generate_ai_insight(row, 50)
    assert ins.symbol
    assert 0 <= ins.score <= 100
