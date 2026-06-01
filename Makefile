.PHONY: build dev down migrate seed shell bash logs test test-cov lint format clean prod-up prod-down


build:
	docker compose build

dev:
	docker compose --env-file .env up -d --build --remove-orphans

down:
	docker compose --env-file .env down -v

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed --size medium

shell:
	docker compose exec backend python

bash:
	docker compose exec backend bash

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest

test-cov:
	docker compose exec backend pytest --cov

lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run ruff format .

prod-up:
	docker compose --env-file .env.prod -f docker-compose.yaml -f docker-compose.prod.yaml up -d --build --remove-orphans

prod-down:
	docker compose --env-file .env.prod -f docker-compose.yaml -f docker-compose.prod.yaml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
