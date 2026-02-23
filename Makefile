.PHONY: install run lint test

install:
	python -m pip install -r requirements.txt

run:
	streamlit run app/dashboard.py

lint:
	python -m py_compile app/dashboard.py app/platform.py app/market_data.py app/indicators.py app/bots.py app/signals.py app/bot.py tests/test_core.py

test:
	python -m pytest -q
