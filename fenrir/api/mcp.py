"""MCP Server — JSON-RPC 2.0 endpoint for Bifrost integration.

Implements the Model Context Protocol (MCP) server interface so Bifrost
can discover and call Fenrir's tools via stdio or SSE transport.
"""

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("fenrir.mcp")

router = APIRouter(tags=["mcp"])


# === JSON-RPC Models ===

class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str
    params: dict[str, Any] = {}


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response."""
    jsonrpc: str = "2.0"
    id: int | str | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


# === Tool Definitions ===

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "browser_navigate",
        "description": "Navigate the browser to a URL and return the page content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "browser_extract",
        "description": "Extract text content from the current page using a CSS selector.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector to extract from"},
            },
            "required": ["selector"],
        },
    },
    {
        "name": "fhir_search_patient",
        "description": "Search for patients in OpenEMR by name, birthdate, or identifier.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Patient name (partial match)"},
                "birthdate": {"type": "string", "description": "Date of birth (YYYY-MM-DD)"},
                "identifier": {"type": "string", "description": "Patient identifier / MRN"},
            },
        },
    },
    {
        "name": "fhir_get_patient",
        "description": "Get a specific patient record from OpenEMR by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "FHIR Patient resource ID"},
            },
            "required": ["patient_id"],
        },
    },
    {
        "name": "fhir_create_patient",
        "description": "Create a new patient record in OpenEMR.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "family_name": {"type": "string", "description": "Patient family/last name"},
                "given_name": {"type": "string", "description": "Patient given/first name"},
                "birthdate": {"type": "string", "description": "Date of birth (YYYY-MM-DD)"},
                "gender": {"type": "string", "enum": ["male", "female", "other", "unknown"]},
            },
            "required": ["family_name", "given_name"],
        },
    },
]


# === JSON-RPC Dispatch ===

async def handle_initialize(params: dict) -> dict:
    """Handle MCP initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "serverInfo": {
            "name": "fenrir",
            "version": "0.1.0",
        },
    }


async def handle_tools_list(params: dict) -> dict:
    """Handle tools/list — return available tool definitions."""
    return {"tools": TOOL_DEFINITIONS}


async def handle_tools_call(params: dict) -> dict:
    """Handle tools/call — dispatch to appropriate tool handler."""
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    logger.info(f"MCP tool call: {tool_name} with {arguments}")

    # Import handlers lazily to avoid circular deps
    from fenrir.fhir.client import FHIRClient
    from fenrir.browser.agent import BrowserAgent
    from fenrir.config import settings

    if tool_name == "fhir_search_patient":
        client = FHIRClient(settings.openemr_fhir_url, settings.openemr_auth_token)
        result = await client.search_patient(**arguments)
        return {"content": [{"type": "text", "text": str(result)}]}

    elif tool_name == "fhir_get_patient":
        client = FHIRClient(settings.openemr_fhir_url, settings.openemr_auth_token)
        result = await client.get_patient(arguments["patient_id"])
        return {"content": [{"type": "text", "text": str(result)}]}

    elif tool_name == "fhir_create_patient":
        client = FHIRClient(settings.openemr_fhir_url, settings.openemr_auth_token)
        result = await client.create_patient(**arguments)
        return {"content": [{"type": "text", "text": str(result)}]}

    elif tool_name == "browser_navigate":
        agent = BrowserAgent(headless=settings.browser_headless)
        result = await agent.navigate(arguments["url"])
        return {"content": [{"type": "text", "text": result}]}

    elif tool_name == "browser_extract":
        agent = BrowserAgent(headless=settings.browser_headless)
        result = await agent.extract(arguments["selector"])
        return {"content": [{"type": "text", "text": result}]}

    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}


# Method dispatch table
METHOD_HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


@router.post("/mcp")
async def mcp_endpoint(request: JsonRpcRequest) -> JsonRpcResponse:
    """JSON-RPC 2.0 MCP endpoint.

    Supports: initialize, tools/list, tools/call
    """
    handler = METHOD_HANDLERS.get(request.method)

    if handler is None:
        return JsonRpcResponse(
            id=request.id,
            error={
                "code": -32601,
                "message": f"Method not found: {request.method}",
            },
        )

    try:
        result = await handler(request.params)
        return JsonRpcResponse(id=request.id, result=result)
    except Exception as e:
        logger.exception(f"MCP handler error: {request.method}")
        return JsonRpcResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": f"Internal error: {e}",
            },
        )
