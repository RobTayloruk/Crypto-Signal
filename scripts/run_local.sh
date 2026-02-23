#!/usr/bin/env bash
set -euo pipefail

python app/self_check.py
streamlit run app/dashboard.py
