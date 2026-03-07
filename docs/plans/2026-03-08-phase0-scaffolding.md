# Phase 0: Project Scaffolding — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up the aligned repo with backend (FastAPI/FastREST), frontend (Vue/TypeScript), strict type checking (mypy, vue-tsc), testing (pytest, Playwright), and CI (GitHub Actions) — all wired together and passing before any feature code is written.

**Architecture:** Monorepo with `backend/` (Python 3.12, FastREST) and `frontend/` (Vue 3, TypeScript). Backend uses async SQLAlchemy with Alembic migrations. Pre-commit hooks enforce mypy strict + ruff on every commit. GitHub Actions CI enforces the same on every PR.

**Tech Stack:** Python 3.12, FastAPI, FastREST, SQLAlchemy async, Alembic, Pydantic, mypy, ruff, pytest, Playwright, Vue 3, TypeScript, Vite, Pinia, Node 22

---

### Task 1: Create Python venv and backend pyproject.toml

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/aligned/__init__.py`
- Create: `backend/aligned/py.typed`

**Step 1: Create directory structure and venv**

```bash
cd /home/corrin/src/aligned
mkdir -p backend/aligned
python3.12 -m venv backend/.venv
```

**Step 2: Create `backend/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "aligned"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.100",
    "fastrest[sqlalchemy]",
    "uvicorn[standard]",
    "sqlalchemy[asyncio]>=2.0",
    "aiomysql",
    "aiosqlite",
    "pydantic>=2.0",
    "pydantic-settings",
    "python-dotenv",
    "pyjwt[crypto]",
    "httpx",
    "litellm",
    "todoist-api-python",
    "O365",
    "msal",
    "google-api-python-client",
    "google-auth-oauthlib",
    "alembic",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-playwright",
    "playwright",
    "mypy",
    "ruff",
    "pre-commit",
]

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = [
    "E", "W",
    "F",
    "I",
    "UP",
    "B",
    "SIM",
    "TCH",
    "ANN",
    "RUF",
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ANN"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
strict_markers = true
```

**Step 3: Create `backend/aligned/__init__.py`**

```python
"""Aligned — intelligent task and calendar management."""
```

**Step 4: Create `backend/aligned/py.typed`**

Empty file (PEP 561 marker).

**Step 5: Install in dev mode**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
pip install -e ".[dev]"
```

**Step 6: Verify**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
python -c "import aligned; print('OK')"
mypy --version
ruff --version
pytest --version
```

Expected: All commands succeed.

**Step 7: Commit**

```bash
git add backend/pyproject.toml backend/aligned/__init__.py backend/aligned/py.typed
git commit -m "feat: backend project scaffolding with pyproject.toml and venv"
```

---

### Task 2: App factory and config

**Files:**
- Create: `backend/aligned/app.py`
- Create: `backend/aligned/config.py`
- Create: `backend/.env.example`
- Create: `backend/.env`

**Step 1: Create `backend/aligned/config.py`**

```python
"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration. Values loaded from .env file or environment."""

    database_url: str = "sqlite+aiosqlite:///aligned.db"
    jwt_secret_key: str = "change-me-in-production"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""
    o365_client_id: str = ""
    o365_client_secret: str = ""
    o365_redirect_uri: str = ""
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Return application settings (cached by pydantic-settings)."""
    return Settings()
```

**Step 2: Create `backend/aligned/app.py`**

```python
"""FastAPI application factory."""

from fastapi import FastAPI

from aligned.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Aligned",
        description="Intelligent task and calendar management",
        version="0.1.0",
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
```

**Step 3: Create `backend/.env.example`**

```env
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/aligned
JWT_SECRET_KEY=change-me-in-production
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
O365_CLIENT_ID=
O365_CLIENT_SECRET=
O365_REDIRECT_URI=
```

**Step 4: Create `backend/.env`**

Copy from .env.example with sqlite default for local dev:

```env
DATABASE_URL=sqlite+aiosqlite:///aligned.db
JWT_SECRET_KEY=local-dev-secret
```

**Step 5: Add `.env` to `.gitignore`**

Create/update `backend/.gitignore`:

```
.venv/
.env
*.db
__pycache__/
*.pyc
.mypy_cache/
.ruff_cache/
*.egg-info/
```

**Step 6: Verify mypy passes**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
mypy aligned --strict
ruff check aligned
```

Expected: Zero errors.

**Step 7: Commit**

```bash
git add backend/aligned/app.py backend/aligned/config.py backend/.env.example backend/.gitignore
git commit -m "feat: app factory with config and health endpoint"
```

---

### Task 3: Database setup with async SQLAlchemy and Alembic

**Files:**
- Create: `backend/aligned/models/__init__.py`
- Create: `backend/aligned/models/base.py`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`

**Step 1: Create `backend/aligned/models/base.py`**

```python
"""SQLAlchemy async base and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from aligned.config import get_settings


class Base:
    """Import DeclarativeBase at usage site to avoid circular imports."""


# These will be initialized by init_db()
_engine = None
_session_factory = None


def init_db(database_url: str | None = None) -> None:
    """Initialize the async engine and session factory."""
    global _engine, _session_factory
    url = database_url or get_settings().database_url
    _engine = create_async_engine(url, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (for use as a FastAPI dependency)."""
    if _session_factory is None:
        init_db()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session
```

**Step 2: Create `backend/aligned/models/__init__.py`**

```python
"""Database models package."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
```

**Step 3: Initialize Alembic**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
alembic init -t async migrations
```

**Step 4: Edit `backend/alembic.ini`**

Set `sqlalchemy.url` to empty (we'll override from env in env.py):

```ini
sqlalchemy.url =
```

**Step 5: Edit `backend/migrations/env.py`**

Replace the generated env.py with one that imports our Base and reads DATABASE_URL from settings:

```python
"""Alembic migration environment."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from aligned.config import get_settings
from aligned.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_settings().database_url
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    """Run migrations using a connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 6: Verify Alembic works**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
alembic upgrade head
```

Expected: Runs without error (no migrations yet, just confirms setup).

**Step 7: Verify mypy + ruff**

```bash
mypy aligned --strict
ruff check aligned
```

Expected: Zero errors. (Note: the `do_run_migrations` has a `# type: ignore` because Alembic's `run_sync` callback isn't cleanly typed — this is acceptable for migration plumbing.)

**Step 8: Commit**

```bash
git add backend/aligned/models/ backend/alembic.ini backend/migrations/
git commit -m "feat: async SQLAlchemy base and Alembic migration setup"
```

---

### Task 4: Test infrastructure

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/unit/__init__.py`
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/e2e/__init__.py`

**Step 1: Create test directory structure**

```bash
mkdir -p backend/tests/unit backend/tests/integration backend/tests/e2e
touch backend/tests/__init__.py backend/tests/unit/__init__.py backend/tests/integration/__init__.py backend/tests/e2e/__init__.py
```

**Step 2: Create `backend/tests/conftest.py`**

```python
"""Shared test fixtures."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from aligned.app import create_app
from aligned.config import Settings
from aligned.models import Base
from aligned.models.base import get_session


@pytest.fixture
def test_settings() -> Settings:
    """Settings for testing — uses in-memory SQLite."""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret_key="test-secret",
    )


@pytest.fixture
async def db_session(test_settings: Settings) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory database and yield a session."""
    engine = create_async_engine(test_settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(test_settings: Settings, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the test app."""
    app = create_app(settings=test_settings)

    # Override the session dependency
    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

**Step 3: Verify empty test run**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
pytest -v
```

Expected: "no tests ran" or similar — no errors.

**Step 4: Commit**

```bash
git add backend/tests/
git commit -m "feat: test infrastructure with async fixtures"
```

---

### Task 5: Smoke tests — backend

**Files:**
- Create: `backend/tests/integration/test_health.py`

**Step 1: Write the failing test**

Create `backend/tests/integration/test_health.py`:

```python
"""Smoke test — verify the app starts and health endpoint works."""

from httpx import AsyncClient


async def test_health_endpoint(client: AsyncClient) -> None:
    """GET /api/health returns 200 with status ok."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run the test**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
pytest tests/integration/test_health.py -v
```

Expected: PASS.

**Step 3: Verify mypy + ruff on tests too**

```bash
mypy aligned --strict
ruff check aligned tests
```

Expected: Zero errors.

**Step 4: Commit**

```bash
git add backend/tests/integration/test_health.py
git commit -m "test: backend smoke test for health endpoint"
```

---

### Task 6: Pre-commit hooks

**Files:**
- Create: `backend/.pre-commit-config.yaml`

**Step 1: Create `backend/.pre-commit-config.yaml`**

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: ruff check --fix
        language: system
        types: [python]
      - id: ruff-format
        name: ruff format
        entry: ruff format
        language: system
        types: [python]
      - id: mypy
        name: mypy
        entry: bash -c 'cd backend && source .venv/bin/activate && mypy aligned --strict'
        language: system
        types: [python]
        pass_filenames: false
```

**Step 2: Install pre-commit hooks**

```bash
cd /home/corrin/src/aligned
source backend/.venv/bin/activate
pre-commit install
```

**Step 3: Verify hooks work**

```bash
pre-commit run --all-files
```

Expected: All hooks pass.

**Step 4: Commit**

```bash
git add backend/.pre-commit-config.yaml
git commit -m "feat: pre-commit hooks for ruff and mypy"
```

---

### Task 7: Verify the gate catches errors

**Step 1: Create a deliberately broken file**

Create `backend/aligned/broken.py`:

```python
def bad_function(x):
    return x + 1
```

**Step 2: Verify mypy catches it**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
mypy aligned --strict
```

Expected: Error about missing type annotations on `bad_function`.

**Step 3: Verify ruff catches it**

```bash
ruff check aligned
```

Expected: ANN error about missing type annotations.

**Step 4: Verify git commit is blocked**

```bash
cd /home/corrin/src/aligned
git add backend/aligned/broken.py
git commit -m "this should fail"
```

Expected: Pre-commit hooks fail, commit is blocked.

**Step 5: Clean up**

```bash
rm backend/aligned/broken.py
git reset HEAD backend/aligned/broken.py
```

**Step 6: No commit needed — this was a verification step.**

---

### Task 8: Frontend setup (Vue + TypeScript)

**Files:**
- Create: `frontend/` (via create-vue)
- Modify: `frontend/vite.config.ts` (add API proxy)

**Step 1: Scaffold Vue project**

```bash
cd /home/corrin/src/aligned
npm create vue@latest frontend -- --typescript --router --pinia
cd frontend
npm install
npm install axios
```

**Step 2: Add API proxy to `frontend/vite.config.ts`**

Edit to add proxy:

```typescript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

**Step 3: Verify TypeScript strict is enabled**

Check `frontend/tsconfig.json` — `create-vue` enables strict by default. Verify `"strict": true` is present.

**Step 4: Verify frontend builds**

```bash
cd /home/corrin/src/aligned/frontend
npm run build
npx vue-tsc --noEmit
```

Expected: Both pass.

**Step 5: Commit**

```bash
cd /home/corrin/src/aligned
git add frontend/
git commit -m "feat: Vue 3 frontend with TypeScript strict and API proxy"
```

---

### Task 9: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -e ".[dev]"
      - name: mypy
        run: |
          source .venv/bin/activate
          mypy aligned --strict
      - name: ruff check
        run: |
          source .venv/bin/activate
          ruff check aligned
      - name: ruff format
        run: |
          source .venv/bin/activate
          ruff format --check aligned
      - name: pytest
        run: |
          source .venv/bin/activate
          pytest -v
        env:
          DATABASE_URL: sqlite+aiosqlite:///:memory:
          JWT_SECRET_KEY: test-secret

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - name: Install dependencies
        run: npm ci
      - name: Type check
        run: npx vue-tsc --noEmit
      - name: Lint
        run: npm run lint
      - name: Build
        run: npm run build
```

**Step 2: Commit and push**

```bash
cd /home/corrin/src/aligned
git add .github/workflows/ci.yml
git commit -m "ci: GitHub Actions for backend (mypy, ruff, pytest) and frontend (vue-tsc, lint)"
git push
```

**Step 3: Verify CI passes**

```bash
gh run watch
```

Expected: Both backend and frontend jobs pass.

**Step 4: Configure branch protection**

```bash
gh api repos/corrin/aligned/branches/main/protection \
  -X PUT \
  -F "required_status_checks[strict]=true" \
  -F "required_status_checks[contexts][]=backend" \
  -F "required_status_checks[contexts][]=frontend" \
  -F "enforce_admins=false" \
  -F "required_pull_request_reviews=null" \
  -F "restrictions=null"
```

---

### Task 10: Playwright e2e smoke test

**Files:**
- Create: `backend/tests/e2e/test_smoke.py`
- Create: `backend/tests/e2e/conftest.py`

**Step 1: Install Playwright browsers**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
playwright install chromium
```

**Step 2: Create `backend/tests/e2e/conftest.py`**

```python
"""Playwright e2e test fixtures."""

import subprocess
import time
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def backend_server() -> Generator[str, None, None]:
    """Start the backend server for e2e tests."""
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "aligned.app:create_app", "--factory", "--port", "8000"],
        cwd="/home/corrin/src/aligned/backend",
        env={
            "PATH": "/home/corrin/src/aligned/backend/.venv/bin:/usr/bin:/bin",
            "DATABASE_URL": "sqlite+aiosqlite:///test_e2e.db",
            "JWT_SECRET_KEY": "test-secret",
        },
    )
    time.sleep(2)  # Wait for server to start
    yield "http://localhost:8000"
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def frontend_server() -> Generator[str, None, None]:
    """Start the frontend dev server for e2e tests."""
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", "5173"],
        cwd="/home/corrin/src/aligned/frontend",
    )
    time.sleep(3)  # Wait for Vite to start
    yield "http://localhost:5173"
    proc.terminate()
    proc.wait()
```

**Step 3: Create `backend/tests/e2e/test_smoke.py`**

```python
"""E2E smoke test — verify frontend and backend are wired together."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_frontend_loads(frontend_server: str, page: Page) -> None:
    """Vue app loads and shows the page title."""
    page.goto(frontend_server)
    assert page.title() != ""


@pytest.mark.e2e
def test_api_proxy_works(frontend_server: str, backend_server: str, page: Page) -> None:
    """Frontend can reach backend through Vite proxy."""
    response = page.request.get(f"{backend_server}/api/health")
    assert response.status == 200
    assert response.json()["status"] == "ok"
```

**Step 4: Run e2e tests**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
pytest tests/e2e/ -v -m e2e
```

Expected: Tests pass (or we iterate on the fixture setup).

**Step 5: Commit**

```bash
cd /home/corrin/src/aligned
git add backend/tests/e2e/
git commit -m "test: Playwright e2e smoke tests"
```

---

### Task 11: Final verification and push

**Step 1: Run all quality gates**

```bash
cd /home/corrin/src/aligned/backend
source .venv/bin/activate
mypy aligned --strict
ruff check aligned
ruff format --check aligned
pytest -v

cd /home/corrin/src/aligned/frontend
npx vue-tsc --noEmit
npm run lint
npm run build
```

Expected: Everything passes.

**Step 2: Push and verify CI**

```bash
cd /home/corrin/src/aligned
git push
gh run watch
```

Expected: CI passes.

**Phase 0 is complete when all acceptance criteria from the design doc are met.**
