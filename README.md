# Crypto Signal Pro Dashboard

A modern, professional crypto intelligence dashboard built with Streamlit.

## What this project includes

- Real-time market data ingestion from **CoinGecko** (open public API)
- Market sentiment ingestion from **Alternative.me Fear & Greed Index**
- Professional analytics UI with three workspaces:
  - **Market**: market structure and microtrend visuals
  - **AI Insights**: actionable signal scoring and risk context
  - **Auto Trade Bot**: presets, sizing logic, and webhook payload preview
- Deterministic AI-style trade hints for explainable decision support

## Auto Trade Bot features

- Strategy presets:
  - `Scalp Pro`
  - `Intraday Alpha`
  - `Swing Smart`
- Risk model controls:
  - account size
  - risk per trade
  - max simultaneous positions
  - stop-loss / take-profit percentages
- Trade plan output per symbol:
  - entry
  - stop loss
  - take profit
  - position size units
- Webhook-ready JSON preview for downstream execution services

## Run locally

```bash
pip install -r app/requirements-dashboard.txt
streamlit run app/dashboard.py
```

## Data sources

- CoinGecko API: https://www.coingecko.com/en/api
- Alternative.me Fear & Greed API: https://api.alternative.me/fng/

## Disclaimer

This software is for educational and research purposes only and does not constitute financial advice.
