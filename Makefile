.DEFAULT_GOAL := help
.PHONY: help run db db-stop migrate migrate-new fmt fmt-check
.PHONY: lint test check build api up down logs

COMPOSE := docker compose --project-directory . -f docker/compose.yml
COMPOSE_PROD := docker compose --project-directory . -f docker/compose.prod.yml

help: ## List available targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN { FS = ":.*?## " }; { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }'

run: ## Run the API natively
	cargo run --bin zeitzeit

db: ## Start the dev database
	$(COMPOSE) up -d db

db-stop: ## Stop the dev database (keeping the data)
	$(COMPOSE) down

migrate: ## Apply migrations
	sqlx migrate run

migrate-new: ## Create a migration: make migrate-new name=add_users
	@test -n "$(name)" || { echo "usage: make migrate-new name=<name>"; exit 1; }
	sqlx migrate add -r "$(name)"

fmt:
	cargo fmt --all

lint: ## Clippy warnings as errors
	cargo clippy --all-targets --locked -- -D warnings

test:
	cargo test --locked

check: fmt-check lint test ## Run everything CI runs

build:
	cargo build --release --locked

api: ## Run the API in dev container
	$(COMPOSE) --profile api up --build api

up: ## Start production stack
	$(COMPOSE_PROD) up -d --build

down: ## Stop production stack
	$(COMPOSE_PROD) down

logs: ## Follow the production API logs
	$(COMPOSE_PROD) logs -f api
