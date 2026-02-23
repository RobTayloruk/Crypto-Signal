# Crypto Signal Pro Platform

A complete Python trading platform + crypto data dashboard with live market ingestion, advanced indicators, multi-bot strategy scoring, AI insights, and execution planning.

## Features

- **Live market data ingestion** from CoinGecko (universe and per-asset chart history)
- **Advanced dashboard graphics**:
  - market structure scatter
  - market cap treemap
  - top momentum movers bar chart
  - price + EMA/SMA/Bollinger overlays
  - RSI oscillator panel
  - MACD panel
  - bot radar chart
  - AI strength polar wheel
  - position allocation pie chart
- **Full indicator stack**: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic, OBV, VWAP
- **Trading bots**: TrendBot, MeanReversionBot, BreakoutBot
- **AI insight scoring** with confidence and rationale
- **Execution center** with presets and webhook-ready order payloads
- **Wallet integration (watch-only)** for BTC and ETH balances/tx stats
- **Real-time terminal** stream for top-signal updates and market pulse logs
- **Installation executable**: `./install.sh`
- **Fallback fixtures** to keep app functional if API calls fail

## Project Structure

- `app/dashboard.py` – Streamlit UI
- `app/platform.py` – orchestration layer
- `app/market_data.py` – live/fallback market adapters
- `app/indicators.py` – technical indicators
- `app/bots.py` – bot engines and aggregation
- `app/signals.py` – AI scoring
- `app/bot.py` – order planner presets
- `app/self_check.py` – dependency/env validator
- `tests/test_core.py` – platform tests

## Quick Start

```bash
python -m pip install -r requirements.txt
python app/self_check.py
streamlit run app/dashboard.py
```

## One-command bootstrap

```bash
bash scripts/bootstrap.sh
```

## Docker Run

```bash
docker compose up --build
```

## Developer Commands

```bash
make install
make check-env
make lint
make test
make run
```

## Notes

If upstream APIs are rate-limited or unavailable, fallback datasets are used so the app remains navigable.

## Disclaimer

Educational and research use only. This software is not financial advice.
