# MailRadar — Developer Guide

This guide covers local setup, test execution, database operations, and development conventions for MailRadar.

---

## 1. Prerequisites

- **Python**: 3.12, 3.13, or 3.14
- **Node.js**: v20+ with npm
- **Docker & Docker Compose**: (Optional for local containerized deployment)
- **Git**: For version control

---

## 2. Quickstart: Local Development

### 2.1. Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   ```

4. Run the API server:
   ```bash
   uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

The Swagger API documentation will be available at:
`http://localhost:8000/docs`

### 2.2. Frontend Setup

1. Change directory to web app:
   ```bash
   cd apps/web
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

The dashboard will be available at:
`http://localhost:3000`

### 2.3. CLI Setup

You can run the CLI directly from the virtual environment:
```bash
mailradar --help
mailradar doctor
mailradar config init
```

---

## 3. Running with Docker Compose

To spin up the complete stack with PostgreSQL, Redis, Celery Worker, Backend API, and Frontend:

```bash
docker compose up --build
```

Services:
- **Web Dashboard**: `http://localhost:3000`
- **Backend API & Swagger**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## 4. Running Tests

Run backend unit, integration, and security test suites:
```bash
pytest
```

Run test suite with verbose output:
```bash
pytest -v -s
```

Run specific test modules:
```bash
pytest tests/unit/test_ssrf.py
pytest tests/unit/test_extractor.py
pytest tests/integration/test_campaigns.py
```

---

## 5. Database Migrations

MailRadar uses SQLAlchemy 2.0 with Alembic:

- Generate a new migration:
  ```bash
  alembic revision --autogenerate -m "describe changes"
  ```
- Upgrade database to head:
  ```bash
  alembic upgrade head
  ```
- Downgrade one revision:
  ```bash
  alembic downgrade -1
  ```

---

## 6. Code Style & Standards

- **Python**: PEP 8 compliance, formatted with Black/Ruff standards, strict type annotations with Pydantic v2.
- **TypeScript**: Strict mode enabled in `tsconfig.json`, ESLint + Tailwind CSS formatting.
- **Security**: All HTTP outbound calls must use `validate_url_ssrf_safe()` before dispatch.
