.PHONY: up down build test lint migrate makemigrations run-worker

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

test:
	pytest tests/ -v

lint:
	ruff check .

migrate:
	alembic upgrade head

makemigrations:
	alembic revision --autogenerate -m "$(m)"

run-worker:
	python -m src.workers.queue_poller
