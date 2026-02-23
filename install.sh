#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

echo "[1/4] Creating virtual environment at ${VENV_DIR}"
${PYTHON_BIN} -m venv "${VENV_DIR}"

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "[2/4] Upgrading pip"
python -m pip install --upgrade pip

echo "[3/4] Installing dependencies"
python -m pip install -r requirements.txt

echo "[4/4] Running environment self-check"
python app/self_check.py

echo "Installation complete."
echo "Run the platform with: source ${VENV_DIR}/bin/activate && streamlit run app/dashboard.py"
