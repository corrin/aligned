"""Playwright e2e test fixtures."""

import subprocess
import time
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def backend_server() -> Generator[str, None, None]:
    """Start the backend server for e2e tests."""
    proc = subprocess.Popen(
        [".venv/bin/python", "-m", "uvicorn", "aligned.app:create_app", "--factory", "--port", "8001"],
        cwd="/home/corrin/src/aligned/backend",
        env={
            "PATH": "/home/corrin/src/aligned/backend/.venv/bin:/usr/bin:/bin",
            "DATABASE_URL": "sqlite+aiosqlite:///test_e2e.db",
            "JWT_SECRET_KEY": "test-secret",
        },
    )
    time.sleep(2)
    yield "http://localhost:8001"
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def frontend_server() -> Generator[str, None, None]:
    """Start the frontend dev server for e2e tests."""
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", "5174"],
        cwd="/home/corrin/src/aligned/frontend",
    )
    time.sleep(3)
    yield "http://localhost:5174"
    proc.terminate()
    proc.wait()
