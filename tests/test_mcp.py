"""Tests for fenrir.api.mcp — MCP JSON-RPC 2.0 endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from fenrir.main import app
from fenrir.api.mcp import TOOL_DEFINITIONS, JsonRpcRequest, JsonRpcResponse


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


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
