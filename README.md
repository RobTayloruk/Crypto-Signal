# Crypto Signal Pro

A clean, working repository for a professional Streamlit crypto dashboard.

## Features

- Real-time market data from CoinGecko
- Sentiment feed from Alternative.me Fear & Greed index
- Professional tabbed UI:
  - Market structure analytics
  - AI trade insights
  - Auto-trade planning console
- Bot presets with risk sizing and webhook payload output
- Offline-friendly fallback sample data so the app still runs when APIs are unavailable

## Project layout

- `app/dashboard.py` — Streamlit application
- `app/data_sources.py` — live API and fallback data providers
- `app/signals.py` — deterministic AI-style signal engine
- `app/bot.py` — presets and order plan generator
- `tests/test_core.py` — core behavior checks

## Quickstart

```bash
python -m pip install -r requirements.txt
streamlit run app/dashboard.py
```

## Development commands

```bash
make install
make lint
make test
make run
```

## Disclaimer

Educational use only. This project does not provide financial advice.
