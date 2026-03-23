"""MCP Server — Official Anthropic SDK implementation.

Implements the Model Context Protocol (MCP) using FastMCP
so Bifrost can discover and call Fenrir's tools via SSE transport.
"""

import logging
from typing import Optional, Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

logger = logging.getLogger("fenrir.mcp")

mcp_server = FastMCP("fenrir")


@mcp_server.tool()
async def browser_navigate(url: str) -> str:
    """Navigate the browser to a URL and return the page content."""
    from fenrir.browser.agent import BrowserAgent
    from fenrir.config import settings
    logger.info(f"MCP tool call: browser_navigate with {url}")
    agent = BrowserAgent(headless=settings.browser_headless)
    return await agent.navigate(url)


@mcp_server.tool()
async def browser_extract(selector: str) -> str:
    """Extract text content from the current page using a CSS selector."""
    from fenrir.browser.agent import BrowserAgent
    from fenrir.config import settings
    logger.info(f"MCP tool call: browser_extract with {selector}")
    agent = BrowserAgent(headless=settings.browser_headless)
    return await agent.extract(selector)


@mcp_server.tool()
async def fhir_search_patient(name: Optional[str] = None, birthdate: Optional[str] = None, identifier: Optional[str] = None) -> str:
    """Search for patients in OpenEMR by name, birthdate, or identifier."""
    from fenrir.fhir.client import FHIRClient
    from fenrir.config import settings
    logger.info(f"MCP tool call: fhir_search_patient")
    client = FHIRClient(settings.openemr_fhir_url, settings.openemr_auth_token)
    result = await client.search_patient(name=name, birthdate=birthdate, identifier=identifier)
    return str(result)


@mcp_server.tool()
async def fhir_get_patient(patient_id: str) -> str:
    """Get a specific patient record from OpenEMR by ID."""
    from fenrir.fhir.client import FHIRClient
    from fenrir.config import settings
    logger.info(f"MCP tool call: fhir_get_patient with {patient_id}")
    client = FHIRClient(settings.openemr_fhir_url, settings.openemr_auth_token)
    result = await client.get_patient(patient_id)
    return str(result)


@mcp_server.tool()
async def fhir_create_patient(family_name: str, given_name: str, birthdate: Optional[str] = None, gender: Optional[str] = None) -> str:
    """Create a new patient record in OpenEMR."""
    from fenrir.fhir.client import FHIRClient
    from fenrir.config import settings
    logger.info(f"MCP tool call: fhir_create_patient with {family_name}")
    client = FHIRClient(settings.openemr_fhir_url, settings.openemr_auth_token)
    result = await client.create_patient(family_name=family_name, given_name=given_name, birthdate=birthdate, gender=gender)
    return str(result)


@mcp_server.tool()
async def run_e2e(project: str, suite: Optional[str] = None) -> str:
    """Trigger a Forseti E2E test suite by project name. Returns run results summary."""
    import httpx
    from fenrir.config import settings
    logger.info(f"MCP tool call: run_e2e with {project}")
    forseti_url = settings.forseti_url if hasattr(settings, "forseti_url") else "http://forseti:5555"
    payload = {"project": project}
    if suite:
        payload["suite"] = suite
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(f"{forseti_url}/api/run", json=payload)
    return resp.text


@mcp_server.tool()
async def get_test_results(project: Optional[str] = None, limit: int = 10) -> str:
    """Retrieve recent E2E test results from the Forseti dashboard."""
    import httpx
    from fenrir.config import settings
    logger.info(f"MCP tool call: get_test_results for {project}")
    forseti_url = settings.forseti_url if hasattr(settings, "forseti_url") else "http://forseti:5555"
    params: dict[str, Any] = {"limit": limit}
    if project:
        params["project"] = project
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{forseti_url}/api/results", params=params)
    return resp.text
