"""Tests for fenrir.api.mcp — MCP JSON-RPC 2.0 endpoint."""

import pytest
from unittest.mock import patch
from httpx import ASGITransport, AsyncClient

from fenrir.api.mcp import TOOL_DEFINITIONS, JsonRpcRequest, JsonRpcResponse


@pytest.fixture
def client():
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
        test_app = create_app()
        transport = ASGITransport(app=test_app)
        yield AsyncClient(transport=transport, base_url="http://test")


class TestMCP:
    """MCP endpoint tests."""

    async def test_initialize(self, client):
        """initialize should return server info."""
        async with client as c:
            resp = await c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["serverInfo"]["name"] == "fenrir"

    async def test_tools_list(self, client):
        """tools/list should return all tool definitions."""
        async with client as c:
            resp = await c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 2,
                "method": "tools/list", "params": {},
            })
        assert resp.status_code == 200
        data = resp.json()
        tools = data["result"]["tools"]
        assert len(tools) == 5
        names = [t["name"] for t in tools]
        assert "browser_navigate" in names
        assert "fhir_search_patient" in names
        assert "fhir_create_patient" in names

    async def test_method_not_found(self, client):
        """Unknown method should return error -32601."""
        async with client as c:
            resp = await c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 3,
                "method": "nonexistent/method", "params": {},
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"]["code"] == -32601

    def test_tool_definitions_have_schemas(self):
        """All tools should have inputSchema."""
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    def test_jsonrpc_request_model(self):
        """JsonRpcRequest model should parse correctly."""
        req = JsonRpcRequest(method="tools/list", id=1)
        assert req.jsonrpc == "2.0"
        assert req.method == "tools/list"
        assert req.params == {}
