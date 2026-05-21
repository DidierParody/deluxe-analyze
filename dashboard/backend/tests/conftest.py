"""Pytest fixtures with mocked Neo4j layer so tests don't hit production."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Required env BEFORE importing app modules
os.environ.setdefault("NEO4J_PASSWORD", "test-pass")
os.environ.setdefault("DASHBOARD_API_KEY", "test-api-key-1234567890abcdef")

API_KEY = os.environ["DASHBOARD_API_KEY"]


@pytest.fixture
def client(monkeypatch):
    """TestClient with all Neo4j helpers patched out."""
    # Patch the neo4j_client functions used by main.py
    with patch("app.main.get_driver") as mock_driver, \
         patch("app.main.ensure_projection") as mock_ensure, \
         patch("app.main.user_exists") as mock_exists, \
         patch("app.main.get_username") as mock_username, \
         patch("app.main.run_query") as mock_run:

        mock_driver.return_value = object()
        mock_ensure.return_value = None
        mock_exists.return_value = True
        mock_username.return_value = "TestUser"

        # Default rows; individual tests override mock_run.return_value
        mock_run.return_value = []

        from app.main import app  # noqa: E402

        with TestClient(app) as c:
            c.mock_run = mock_run  # type: ignore[attr-defined]
            c.mock_exists = mock_exists  # type: ignore[attr-defined]
            yield c


@pytest.fixture
def auth_headers():
    return {"X-API-Key": API_KEY}
