.DEFAULT_GOAL := help
.PHONY: help run migrate migrate-new fmt fmt-check lint test check build \
  dev-up dev-down dev-logs dev-db-up dev-db-stop dev-db-logs up down logs

COMPOSE := docker compose --project-directory . -f docker/compose.yml
DEV     := $(COMPOSE) -f docker/compose.dev.yml
PROD    := $(COMPOSE) -f docker/compose.prod.yml

help: ## List available targets
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN { FS = ":.*?## " }; { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }'

# --- Native development -----------------------------------------------------

run: ## Run the API natively
	cargo run --bin zeitzeit

migrate: ## Apply migrations
	sqlx migrate run

migrate-new: ## Create a migration: make migrate-new name=add_users
	@test -n "$(name)" || { echo "usage: make migrate-new name=<name>"; exit 1; }
	sqlx migrate add -r "$(name)"

# --- Checks (CI runs the same steps) ----------------------------------------

fmt: ## Format the code
	cargo fmt --all

fmt-check: ## Check formatting
	cargo fmt --all --check

lint: ## Clippy warnings as errors
	cargo clippy --all-targets --locked -- -D warnings

test: ## Run the tests (needs the dev database)
	cargo test --locked

check: fmt-check lint test ## Run everything CI runs

build: ## Release build with cargo (not a Docker build)
	cargo build --release --locked

# --- Dev containers: database + API (cargo-watch) ---------------------------

dev-up: ## Dev: start database and API (foreground)
	$(DEV) --profile api up --build api

dev-down: ## Dev: stop and remove the containers (keeping the data)
	$(DEV) --profile api down

dev-logs: ## Dev: follow the API logs
	$(DEV) logs -f api

# The database alone, for native `cargo run` and the tests.
dev-db-up: ## Dev: start the database only
	$(DEV) up -d db

dev-db-stop: ## Dev: stop the database only (keeping the data)
	$(DEV) stop db

dev-db-logs: ## Dev: follow the database logs
	$(DEV) logs -f db

# --- Production stack -------------------------------------------------------

up: ## Start the production stack
	$(PROD) up -d --build

down: ## Stop the production stack
	$(PROD) down

logs: ## Follow the production API logs
	$(PROD) logs -f api
