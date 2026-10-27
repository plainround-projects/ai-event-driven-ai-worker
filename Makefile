# make up | run | burst | crash-test | test | lint | check | audit | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
PKG := inbox_worker

-include .env
export

$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@

install: $(STAMP) ## create .venv from the hash-pinned lock file

env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }

lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock

lock: ## re-resolve requirements.lock and requirements-dev.lock with hashes (needs uv)
	uv pip compile pyproject.toml --universal --generate-hashes -q -o requirements.lock
	uv pip compile pyproject.toml --universal --extra dev --generate-hashes -q -o requirements-dev.lock

.PHONY: help install env up db reset queries enqueue worker relay status webhook-demo serve-webhook bench-webhook run burst crash-test \
        redrive smoke record test test-integration test-e2e test-live lint format audit check docker-build down clean

help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort

WORKER := $(PY) -m inbox_worker.interfaces.cli
SMOKE_ADAPTER ?= recorded
PSQL := docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q
POSTGRES_USER ?= inbox
POSTGRES_DB ?= inbox

up: env install ## start PostgreSQL in a container and apply sql/001_schema.sql and sql/002_seed.sql
	docker compose up -d --wait postgres
	$(MAKE) --no-print-directory db

db: install ## rebuild the schema (DDL and seed) from the numbered scripts
	$(WORKER) db

reset: install ## empty every table (sql/reset.sql)
	$(WORKER) reset

queries: ## run sql/003_queries.sql
	docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql

webhook-demo: install ## a valid, a tampered and a replayed request against the same signature code
	$(WORKER) webhook-demo

bench-webhook: install ## 500 signed requests against the running webhook code: p95 must stay under 100 ms
	$(WORKER) bench-webhook

enqueue: install ## generate the 1,000 sample events (2% delivered twice, 1% poison) and queue every delivery
	$(WORKER) enqueue

worker: install ## process deliveries until idle with the fake model (set MODEL_ADAPTER=claude for the real one)
	$(WORKER) worker --until-idle

relay: install ## send the acknowledgments in the outbox through the fake mail sender
	$(WORKER) relay --once

status: install ## counts, open dead letters, and whether any event is lost or has two tickets
	$(WORKER) status

redrive: install ## put dead letter DEAD_ID back on the queue (after the cause is fixed)
	$(WORKER) redrive $(DEAD_ID)

run: install reset ## the happy path: queue the sample inbox, process it, replay it, send acknowledgments, show the counts
	$(WORKER) enqueue
	$(WORKER) worker --until-idle
	$(WORKER) status
	$(WORKER) enqueue
	$(WORKER) worker --until-idle
	$(WORKER) relay --once
	$(WORKER) status
	$(MAKE) --no-print-directory queries

burst: install ## 500 events in ten seconds at concurrency 5 and 20 against a fake model that allows 30 calls a second
	$(WORKER) burst

crash-test: install ## kill the worker after the model call and after the commit, restart it, compare event ids
	$(WORKER) crash-test --at after_model
	$(WORKER) crash-test --at after_commit

smoke: install ## 20 events through the recorded model, or the real one with SMOKE_ADAPTER=claude (needs ANTHROPIC_API_KEY)
	MODEL_ADAPTER=$(SMOKE_ADAPTER) $(PY) scripts/smoke.py

record: install ## record the 20 smoke emails with the real model into tests/fixtures/cassettes/live-v1.json (needs ANTHROPIC_API_KEY)
	MODEL_ADAPTER=claude $(PY) scripts/smoke.py --record

serve-webhook: install ## start the webhook on WEBHOOK_PORT
	$(WORKER) serve-webhook

test: install ## unit tests (no services) with coverage; domain and application stay at 95% or more
	$(PY) -m pytest tests/unit --cov=$(PKG) --cov-report=term
	$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95

test-integration: install ## the adapters against the running PostgreSQL (make up first)
	$(PY) -m pytest tests/integration -m integration

test-e2e: install ## the lesson's scenarios through the command-line programs (make up first)
	$(PY) -m pytest tests/e2e -m e2e

test-live: install ## the opt-in test that calls the real model (needs ANTHROPIC_API_KEY)
	RUN_LIVE=1 $(PY) -m pytest tests/live -m live

check: lint test ## everything that needs no services

docker-build: ## build the image of the webhook and the worker
	docker build -t ai-event-driven-ai-worker:dev .

down: ## stop PostgreSQL and delete its data
	docker compose down -v

clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml
