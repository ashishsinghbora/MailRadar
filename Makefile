.PHONY: help cli web install dev-backend dev-frontend test lint clean docker-up docker-down

help:
	@echo "MailRadar Commands:"
	@echo "  ./mailradar-web     Start the full Web Dashboard and API (or 'make web')"
	@echo "  ./mailradar-cli     Run the Linux CLI (or 'make cli')"
	@echo "  make test           Run Pytest test suite"
	@echo "  make docker-up      Spin up stack with Docker Compose"
	@echo "  make docker-down    Tear down Docker Compose containers"

cli:
	./mailradar-cli --help

web:
	./mailradar-web

install:
	pip install -e .[dev]
	cd apps/web && npm install

dev-backend:
	uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd apps/web && npm run dev

test:
	pytest -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down
