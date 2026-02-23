# Crypto Signal Pro Platform

A rebuilt Python trading platform + data dashboard with live crypto market ingestion, full technical indicator coverage, strategy bots, and execution planning.

## Core capabilities

- **Live market data** from CoinGecko (market universe + per-asset market chart)
- **Professional dashboard UI** with tabs for market overview, trading terminal, and execution center
- **Rich visuals** including treemap, momentum movers chart, RSI/MACD panels, bot radar chart, AI signal wheel, and allocation pie chart
- **Indicator engine** with:
  - SMA / EMA
  - RSI
  - MACD (line, signal, histogram)
  - Bollinger Bands
  - ATR
  - Stochastic (%K/%D)
  - OBV
  - VWAP
- **Strategy bots**:
  - TrendBot
  - MeanReversionBot
  - BreakoutBot
- **AI insights** for each tracked asset with confidence and rationale
- **Execution planner** with bot presets and webhook-ready order payload
- **Fallback data mode** so the platform still runs when upstream APIs are unavailable

## Repository structure

- `app/dashboard.py` — Streamlit platform UI
- `app/platform.py` — orchestration layer
- `app/market_data.py` — live market data adapters
- `app/indicators.py` — technical indicator engine
- `app/bots.py` — strategy bots and signal aggregation
- `app/signals.py` — deterministic AI insight scoring
- `app/bot.py` — execution presets and order builder
- `tests/test_core.py` — platform unit checks

## Quickstart

```bash
python -m pip install -r requirements.txt
streamlit run app/dashboard.py
```

## Development

```bash
make install
make lint
make test
make run
```

## Disclaimer

Educational and research use only. This software is not financial advice.
