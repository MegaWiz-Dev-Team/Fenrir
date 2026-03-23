"""Tests for fenrir.api.mcp — MCP JSON-RPC 2.0 endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
        mock_settings.yggdrasil_issuer = ""
        mock_settings.jwt_audience = ""
        mock_settings.forseti_url = "http://forseti:5555"

        from fenrir.main import create_app
        test_app = create_app()
        transport = ASGITransport(app=test_app)
        yield AsyncClient(transport=transport, base_url="http://test")


class TestMCP:
    """MCP endpoint tests."""

    async def test_initialize(self, client):
        """TC_FN_MCP_01 — initialize returns server info."""
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
        """TC_FN_MCP_02 — tools/list returns all 7 tool definitions."""
        async with client as c:
            resp = await c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 2,
                "method": "tools/list", "params": {},
            })
        assert resp.status_code == 200
        data = resp.json()
        tools = data["result"]["tools"]
        assert len(tools) == 7  # 5 original + run_e2e + get_test_results
        names = [t["name"] for t in tools]
        assert "browser_navigate" in names
        assert "fhir_search_patient" in names
        assert "fhir_create_patient" in names
        assert "run_e2e" in names
        assert "get_test_results" in names

    async def test_method_not_found(self, client):
        """TC_FN_MCP_03 — unknown method returns error -32601."""
        async with client as c:
            resp = await c.post("/mcp", json={
                "jsonrpc": "2.0", "id": 3,
                "method": "nonexistent/method", "params": {},
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"]["code"] == -32601

    def test_tool_definitions_have_schemas(self):
        """TC_FN_MCP_04 — all tools have valid inputSchema."""
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    def test_jsonrpc_request_model(self):
        """TC_FN_MCP_05 — JsonRpcRequest parses correctly."""
        req = JsonRpcRequest(method="tools/list", id=1)
        assert req.jsonrpc == "2.0"
        assert req.method == "tools/list"
        assert req.params == {}

    async def test_run_e2e_tool(self, client):
        """TC_FN_MCP_06 — run_e2e calls Forseti /api/run and returns result."""
        mock_resp = MagicMock()
        mock_resp.text = '{"passed": 5, "failed": 0}'

        async def mock_post(*args, **kwargs):
            return mock_resp

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            async with client as c:
                resp = await c.post("/mcp", json={
                    "jsonrpc": "2.0", "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "run_e2e",
                        "arguments": {"project": "eir-gateway"},
                    },
                })
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        content = data["result"]["content"]
        assert len(content) > 0

    async def test_get_test_results_tool(self, client):
        """TC_FN_MCP_07 — get_test_results calls Forseti /api/results and returns list."""
        mock_resp = MagicMock()
        mock_resp.text = '[{"id": 1, "status": "pass"}]'

        async def mock_get(*args, **kwargs):
            return mock_resp

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            async with client as c:
                resp = await c.post("/mcp", json={
                    "jsonrpc": "2.0", "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "get_test_results",
                        "arguments": {"project": "eir-gateway", "limit": 5},
                    },
                })
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        content = data["result"]["content"]
        assert len(content) > 0


