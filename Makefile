# Makefile — non-Windows / CI entrypoint.
# Mirrors scripts/docker-*.ps1 so the same workflow runs in GitHub Actions, Codespaces,
# and Linux dev hosts. Windows users should still call scripts/docker-up.ps1 etc.
#
# Usage:
#   make help
#   make build
#   make up
#   make down
#   make status
#   make logs SVC=mail-service
#   make validate

COMPOSE_BASE := docker-compose.yml
PROFILE_FLAG := $(shell test -n "$$COMPOSE_PROFILES" && echo -f docker-compose.$$COMPOSE_PROFILES.yml)

DC := docker compose -f $(COMPOSE_BASE) $(PROFILE_FLAG)

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: build
build: ## Build all images (NO_CACHE=1 to force)
ifdef NO_CACHE
	$(DC) build --no-cache
else
	$(DC) build
endif

.PHONY: build-one
build-one: ## Build one service: make build-one SVC=mail-service
	$(DC) build $(SVC)

.PHONY: up
up: ## Start stack + wait for healthchecks
	$(DC) up -d --remove-orphans
	@./scripts/wait-healthy.sh

.PHONY: down
down: ## Stop stack (PRUNE_VOLUMES=1 to drop postgres_data)
	$(DC) down
ifdef PRUNE_VOLUMES
	docker volume rm account-creation_postgres_data || true
endif

.PHONY: status
status: ## Show compose ps, healthchecks, disk
	@$(DC) ps
	@docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo "--- healthchecks ---"
	@for svc in $$($(DC) config --services); do \
	  name=$$(docker ps --filter "label=com.docker.compose.service=$$svc" --format '{{.Names}}' | head -1); \
	  if [ -n "$$name" ]; then \
	    printf "  %-20s %s\n" "$$svc" "$$(docker inspect --format '{{.State.Health.Status}}' $$name 2>/dev/null || echo none)"; \
	  else \
	    printf "  %-20s (not running)\n" "$$svc"; \
	  fi; \
	done
	@echo "--- disk ---"
	@docker system df

.PHONY: logs
logs: ## Tail logs: make logs SVC=mail-service N=200
	$(DC) logs --tail=$${N:-100} --follow $${SVC:-}

.PHONY: validate
validate: ## Validate compose file (no services started)
	$(DC) config > /dev/null
	@echo "compose OK"

.PHONY: smoke
smoke: ## Run runtime + traefik smoke tests
	pwsh scripts/smoke-runtime-contract.ps1
	pwsh scripts/smoke-traefik-routes.ps1

.PHONY: clean
clean: ## Remove stopped containers, dangling images, build cache
	docker container prune -f
	docker image prune -f
	docker builder prune -f --filter "until=24h"

.PHONY: prune
prune: ## Nuclear: stop + remove volumes + build cache (DESTRUCTIVE)
	$(DC) down -v
	docker volume rm account-creation_postgres_data || true
	docker system prune -af
