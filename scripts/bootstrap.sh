#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m py_compile app/dashboard.py app/platform.py app/market_data.py app/indicators.py app/bots.py app/signals.py app/bot.py

echo "Bootstrap complete. Run: streamlit run app/dashboard.py"
