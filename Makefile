# Makefile for Oilify
# Provides convenient targets for running docker compose without relying on a .env file

# Set environment. Users can override ENV on the CLI (e.g., make up ENV=prod)
ENV ?= dev

# Derive project name and compose file from ENV
PROJECT_NAME := oilify-$(ENV)
COMPOSE_FILE := docker-compose.$(ENV).yml

DC = COMPOSE_PROJECT_NAME=$(PROJECT_NAME) docker compose -f $(COMPOSE_FILE)

.PHONY: help up up-dev up-prod down reset rebuild-reset db-upgrade db-downgrade

help:
	@echo "Makefile targets:"
	@echo "  make up                ->  start services (detached, builds first). Default ENV=dev"
	@echo "  make up-dev            -> start services using docker-compose.dev.yml"
	@echo "  make up-prod           -> start services using docker-compose.prod.yml"
	@echo "  make down              -> stop and remove services"
	@echo "  make reset             -> stop services and remove containers, networks, and volumes"
	@echo "  make rebuild-reset     -> reset the stack and rebuild it from scratch"
	@echo "  make db-upgrade        -> run backend Alembic migrations to head"
	@echo "  make db-downgrade      -> downgrade backend Alembic migrations by one revision"

up:
	$(DC) up

rebuild:
	$(DC) up --build

up-dev:
	$(MAKE) up ENV=dev

up-prod:
	$(MAKE) up ENV=prod

down:
	$(DC) down

reset:
	$(DC) down -v --remove-orphans

rebuild-reset:
	$(MAKE) reset && $(MAKE) rebuild

db-upgrade:
	cd oilify-studio-backend && uv run alembic upgrade head

db-downgrade:
	cd oilify-studio-backend && uv run alembic downgrade -1
