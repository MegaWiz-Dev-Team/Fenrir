"""TDD tests for JWT auth middleware — written BEFORE implementation.

Tests Yggdrasil JWT integration as FastAPI middleware for Fenrir.
Following ISO/IEC 29110 test-first development.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# === Fixtures ===

@pytest.fixture
def auth_enabled_client():
    """Client with auth ENABLED (production mode)."""
    with patch("fenrir.config.settings") as mock_settings:
        mock_settings.fenrir_host = "127.0.0.1"
        mock_settings.fenrir_port = 8200
        mock_settings.log_level = "WARNING"
        mock_settings.openemr_url = "http://localhost:80"
        mock_settings.openemr_fhir_url = "http://localhost:80/apis/default/fhir"
        mock_settings.openemr_auth_token = ""
        mock_settings.heimdall_url = "http://localhost:8080"
        mock_settings.browser_headless = True
        mock_settings.message_enabled = False
        mock_settings.auth_enabled = True
        mock_settings.zitadel_issuer = "http://localhost:8085"
        mock_settings.jwt_audience = ""

        from fenrir.main import create_app
        app = create_app()
        with TestClient(app) as c:
            yield c


@pytest.fixture
def auth_disabled_client():
    """Client with auth DISABLED (dev mode)."""
    with patch("fenrir.config.settings") as mock_settings:
        mock_settings.fenrir_host = "127.0.0.1"
        mock_settings.fenrir_port = 8200
        mock_settings.log_level = "WARNING"
        mock_settings.openemr_url = "http://localhost:80"
        mock_settings.openemr_fhir_url = "http://localhost:80/apis/default/fhir"
        mock_settings.openemr_auth_token = ""
        mock_settings.heimdall_url = "http://localhost:8080"
        mock_settings.browser_headless = True
        mock_settings.message_enabled = False
        mock_settings.auth_enabled = False
        mock_settings.zitadel_issuer = ""
        mock_settings.jwt_audience = ""

        from fenrir.main import create_app
        app = create_app()
        with TestClient(app) as c:
            yield c


# === Public endpoints (always accessible) ===

class TestPublicEndpoints:
    """Health and docs should always remain open."""

    def test_healthz_no_auth(self, auth_enabled_client):
        response = auth_enabled_client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_docs_no_auth(self, auth_enabled_client):
        response = auth_enabled_client.get("/docs")
        assert response.status_code == 200


# === Protected endpoints need JWT ===

class TestProtectedEndpoints:
    """API endpoints should require JWT when auth is enabled."""

    def test_mcp_endpoint_requires_auth(self, auth_enabled_client):
        """POST /mcp should return 401 without token."""
        response = auth_enabled_client.post("/mcp", json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "1",
        })
        assert response.status_code == 401

    def test_messages_status_requires_auth(self, auth_enabled_client):
        """GET /api/messages/status should return 401 without token."""
        response = auth_enabled_client.get("/api/messages/status")
        assert response.status_code == 401


# === Auth disabled mode ===

class TestAuthDisabled:
    """When auth_enabled=False, all endpoints work without tokens."""

    def test_healthz_works(self, auth_disabled_client):
        response = auth_disabled_client.get("/healthz")
        assert response.status_code == 200

    def test_messages_status_works(self, auth_disabled_client):
        """Message status should work without auth in dev mode."""
        response = auth_disabled_client.get("/api/messages/status")
        assert response.status_code == 200


# === Valid token ===

class TestValidToken:
    """Requests with valid JWT should succeed."""

    @patch("fenrir.middleware.auth.validate_jwt")
    def test_valid_token_allows_mcp(self, mock_validate, auth_enabled_client):
        """Valid JWT should allow MCP endpoint access."""
        from yggdrasil.models import TokenClaims
        mock_validate.return_value = TokenClaims(
            sub="user-123", iss="http://localhost:8085", org_id="org-1"
        )

        response = auth_enabled_client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": "1"},
            headers={"Authorization": "Bearer valid-jwt-token"},
        )
        # Should not be 401 (may be other status depending on MCP handler)
        assert response.status_code != 401


# === Invalid token ===

class TestInvalidToken:
    """Invalid JWTs should be rejected."""

    @patch("fenrir.middleware.auth.validate_jwt")
    def test_expired_token_rejected(self, mock_validate, auth_enabled_client):
        import jwt as pyjwt
        mock_validate.side_effect = pyjwt.ExpiredSignatureError("Token expired")

        response = auth_enabled_client.get(
            "/api/messages/status",
            headers={"Authorization": "Bearer expired-token"},
        )
        assert response.status_code == 401
