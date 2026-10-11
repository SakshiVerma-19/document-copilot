# Document Copilot — Backend Service

FastAPI backend service powering the Document Copilot RAG assistant.

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package and project manager)
- Python 3.12+
- Supabase project (Auth + PostgreSQL database)

---

## Setup

1. **Environment Configuration**
   Ensure `.env` exists in the `backend/` directory (copied and populated from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. **Install Dependencies**
   ```bash
   uv sync
   ```

---

## Running the API

### Development Server (with Auto-Reload)

From the `backend/` directory:
```bash
uv run uvicorn app.main:app --reload
```

Or run directly with Python:
```bash
uv run python app/main.py
```

### Key Endpoints & Documentation

- **Health check:** [http://localhost:8000/health](http://localhost:8000/health) (`{"status": "ok"}`)
- **Swagger UI (Interactive API docs):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Database Migrations (Alembic)

Database schema changes are tracked with Alembic and applied to Supabase:

- **Apply all pending migrations:**
  ```bash
  uv run alembic upgrade head
  ```

- **Generate a new migration from model changes:**
  ```bash
  uv run alembic revision --autogenerate -m "describe_changes"
  ```

- **Check current database revision:**
  ```bash
  uv run alembic current
  ```

---

## Managing Dependencies

Use `uv` rather than raw `pip` to keep `pyproject.toml` and `uv.lock` in sync:

- **Add a runtime dependency:**
  ```bash
  uv add <package_name>
  ```

- **Add a development/testing dependency:**
  ```bash
  uv add --dev <package_name>
  ```

- **Remove a package:**
  ```bash
  uv remove <package_name>
  ```

---

## Testing & Code Quality

- **Run unit tests:**
  ```bash
  uv run pytest
  ```

- **Run linter / formatter checks:**
  ```bash
  uv run ruff check .
  uv run ruff format .
  ```
