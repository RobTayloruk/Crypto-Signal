.PHONY: install run lint test check-env bootstrap docker-up

install:
	python -m pip install -r requirements.txt

check-env:
	python app/self_check.py

bootstrap:
	bash scripts/bootstrap.sh

run:
	bash scripts/run_local.sh

lint:
	python -m py_compile app/dashboard.py app/platform.py app/market_data.py app/indicators.py app/bots.py app/signals.py app/bot.py app/self_check.py tests/test_core.py

test:
	python -m pytest -q

docker-up:
	docker compose up --build
