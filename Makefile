.PHONY: install run lint test

install:
	python -m pip install -r requirements.txt

run:
	streamlit run app/dashboard.py

lint:
	python -m py_compile app/dashboard.py app/data_sources.py app/signals.py app/bot.py

test:
	python -m pytest -q
