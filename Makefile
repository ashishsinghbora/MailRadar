.PHONY: help install dev-backend dev-frontend test lint clean docker-up docker-down

help:
	@echo "MailRadar Development Commands:"
	@echo "  make install        Install backend and frontend dependencies"
	@echo "  make dev-backend    Start FastAPI backend server"
	@echo "  make dev-frontend   Start Next.js frontend dev server"
	@echo "  make test           Run Pytest test suite"
	@echo "  make docker-up      Spin up stack with Docker Compose"
	@echo "  make docker-down    Tear down Docker Compose containers"

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
