PORT ?= 8000

run:
	uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --reload

worker:
	python worker.py

format:
	python -m pip install black && black app

lint:
	python -m pip install ruff && ruff check app
