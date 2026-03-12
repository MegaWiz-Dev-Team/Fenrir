"""Health check endpoints."""

import httpx
from fastapi import APIRouter

from fenrir.config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz():
    """Liveness probe — returns OK if Fenrir is running."""
    return {
        "status": "ok",
        "service": "fenrir",
        "version": "0.1.0",
    }


@router.get("/readyz")
async def readyz():
    """Readiness probe — checks Heimdall + OpenEMR connectivity."""
    checks = {}

    # Check Heimdall
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.heimdall_url}/healthz")
            checks["heimdall"] = "reachable" if resp.status_code < 500 else "unhealthy"
    except httpx.HTTPError:
        checks["heimdall"] = "unreachable"

    # Check OpenEMR
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(settings.openemr_url)
            checks["openemr"] = "reachable" if resp.status_code < 500 else "unhealthy"
    except httpx.HTTPError:
        checks["openemr"] = "unreachable"

    all_ok = all(v == "reachable" for v in checks.values())

    return {
        "status": "ready" if all_ok else "degraded",
        "service": "fenrir",
        "checks": checks,
    }
