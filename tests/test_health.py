"""Tests for fenrir.api.health."""

import pytest
from httpx import ASGITransport, AsyncClient

from fenrir.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealth:
    """Health endpoint tests."""

    async def test_healthz(self, client):
        """GET /healthz should return ok."""
        async with client as c:
            resp = await c.get("/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "fenrir"
        assert data["version"] == "0.1.0"

    async def test_readyz_format(self, client):
        """GET /readyz should return proper format (even if checks fail)."""
        async with client as c:
            resp = await c.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "checks" in data
        assert "heimdall" in data["checks"]
        assert "openemr" in data["checks"]
