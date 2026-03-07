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
