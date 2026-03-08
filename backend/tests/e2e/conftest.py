"""Playwright e2e test fixtures."""

import os
import subprocess
import time
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def backend_server() -> Generator[str, None, None]:
    """Start the backend server for e2e tests with TESTING=true."""
    backend_dir = os.path.join(os.path.dirname(__file__), "..", "..")
    proc = subprocess.Popen(
        [".venv/bin/python", "-m", "uvicorn", "aligned.app:create_app", "--factory", "--port", "8001"],
        cwd=backend_dir,
        env={
            **os.environ,
            "TESTING": "true",
        },
    )
    time.sleep(2)
    yield "http://localhost:8001"
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def frontend_server() -> Generator[str, None, None]:
    """Start the frontend dev server for e2e tests."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend")
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", "5174"],
        cwd=frontend_dir,
    )
    time.sleep(3)
    yield "http://localhost:5174"
    proc.terminate()
    proc.wait()


@pytest.fixture
def authenticated_page(backend_server: str, page: "pytest.Page") -> "pytest.Page":  # type: ignore[name-defined]
    """Page with a valid JWT token in localStorage, bypassing Google OAuth."""
    response = page.request.post(
        f"{backend_server}/api/auth/test-login",
        data={"email": "e2e-test@example.com"},
    )
    assert response.ok, f"test-login failed: {response.status}"
    token = response.json()["token"]
    page.goto("about:blank")
    page.evaluate(f"localStorage.setItem('token', '{token}')")
    return page
