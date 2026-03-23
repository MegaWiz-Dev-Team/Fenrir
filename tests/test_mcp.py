"""Tests for fenrir.api.mcp — MCP Server."""

import pytest
from fenrir.api.mcp import mcp_server


def test_mcp_server_initialization():
    """Verify that FastMCP server is initialized with the correct name."""
    assert mcp_server.name == "fenrir"


@pytest.mark.asyncio
async def test_mcp_tools_registered():
    """Verify that all required tools are registered in the FastMCP server."""
    # FastMCP list_tools is an async method that returns a list of tools
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]
    
    assert len(tool_names) == 7
    assert "browser_navigate" in tool_names
    assert "browser_extract" in tool_names
    assert "fhir_search_patient" in tool_names
    assert "fhir_get_patient" in tool_names
    assert "fhir_create_patient" in tool_names
    assert "run_e2e" in tool_names
    assert "get_test_results" in tool_names
