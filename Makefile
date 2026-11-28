# Local development only; does not deploy to AWS.
.DEFAULT_GOAL := help
IMAGE ?= calculator-backend:local
CONTAINER ?= calculator-backend
PORT ?= 8000
PYTHON ?= python3
DATABASE_URL ?= sqlite:///./calculator.db
DOCKER_DATABASE_URL ?= sqlite:////tmp/calculator.db

.PHONY: help install dev test lint check build run up start stop restart logs status health shell clean

help:
	@printf '%s\n' 'make install     Install local dependencies' 'make dev         Run locally without Docker' 'make test        Run automated tests' 'make lint        Run lint checks' 'make check       Run quality checks' 'make build       Build Docker image' 'make run         Replace local Docker container' 'make up          Build and replace local container' 'make start       Start existing container' 'make stop        Stop container' 'make restart     Restart container' 'make logs        Follow container logs' 'make status      Show container status' 'make health      Check HTTP endpoint' 'make shell       Enter running container' 'make clean       Remove local container (local SQLite history is lost)'

install:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -e ".[dev]"

dev:
	APP_ENV=development DATABASE_URL="$(DATABASE_URL)" .venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port "$(PORT)"

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/python -m ruff check .

check:
	$(MAKE) lint
	$(MAKE) test

build:
	docker build -t "$(IMAGE)" .

run:
	@docker info >/dev/null
	@if docker container inspect "$(CONTAINER)" >/dev/null 2>&1; then \
	  echo "Replacing existing container $(CONTAINER)"; \
	  docker rm -f "$(CONTAINER)"; \
	fi
	docker run -d --name "$(CONTAINER)" -p "127.0.0.1:$(PORT):8000" -e APP_ENV=development -e "DATABASE_URL=$(DOCKER_DATABASE_URL)" "$(IMAGE)"

up:
	$(MAKE) build
	$(MAKE) run

start:
	docker start "$(CONTAINER)"

stop:
	docker stop "$(CONTAINER)"

restart:
	docker restart "$(CONTAINER)"

logs:
	docker logs -f "$(CONTAINER)"

status:
	docker ps -a --filter "name=^/$(CONTAINER)$$"

health:
	curl -fsS "http://localhost:$(PORT)/health/ready"

shell:
	docker exec -it "$(CONTAINER)" sh

clean:
	@docker info >/dev/null
	@if docker container inspect "$(CONTAINER)" >/dev/null 2>&1; then docker rm -f "$(CONTAINER)"; fi
