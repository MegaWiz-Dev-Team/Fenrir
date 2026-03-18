"""Test results REST API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response

from fenrir.test_results import models, storage, parsers

logger = logging.getLogger("fenrir.test_results.api")

router = APIRouter(prefix="/api/test-results", tags=["test-results"])
badge_router = APIRouter(prefix="/api/badges", tags=["badges"])


# ── Submit ────────────────────────────────────────────

@router.post("", status_code=201)
async def submit_test_result(data: models.TestResultCreate):
    """Submit a test result.

    Accepts JSON with test counts, optional coverage, and metadata.
    """
    result = storage.insert_result(data)
    logger.info(
        f"📊 Test result #{result.id}: {result.service}/{result.test_type.value} "
        f"— {result.passed}/{result.total} passed, "
        f"coverage={result.coverage_pct or 'N/A'}%"
    )
    return result


@router.post("/junit", status_code=201)
async def submit_junit_xml(
    service: str = Query(..., description="Service name"),
    test_type: str = Query("unit", description="Test type: unit, e2e, ui"),
    body: str = "",
):
    """Submit test results as JUnit XML.

    Send raw XML in request body with Content-Type: application/xml.
    """
    if not body:
        raise HTTPException(400, "Empty JUnit XML body")

    try:
        tt = models.TestResultType(test_type)
    except ValueError:
        raise HTTPException(400, f"Invalid test_type: {test_type}")

    parsed = parsers.parse_junit_xml(body, service, tt)
    result = storage.insert_result(parsed)
    return result


@router.post("/cargo-test", status_code=201)
async def submit_cargo_test(
    service: str = Query(..., description="Service name"),
    body: str = "",
):
    """Submit raw `cargo test` output.

    Parses 'test result: ok. N passed; M failed; ...' lines.
    """
    if not body:
        raise HTTPException(400, "Empty cargo test output")

    parsed = parsers.parse_cargo_test_output(body, service)
    result = storage.insert_result(parsed)
    return result


# ── List / Query ──────────────────────────────────────

@router.get("")
async def list_test_results(
    service: Optional[str] = Query(None),
    test_type: Optional[str] = Query(None),
    git_branch: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List test results with optional filters."""
    return storage.list_results(service, test_type, git_branch, limit, offset)


@router.get("/summary")
async def test_results_summary():
    """Get aggregated summary for all services.

    Returns pass rate, coverage average, and latest results per test type.
    """
    return storage.get_summary()


@router.get("/coverage/{service}")
async def coverage_trend(
    service: str,
    limit: int = Query(30, ge=1, le=100),
):
    """Get coverage trend data for a service (for charts)."""
    return storage.get_coverage_trend(service, limit)


@router.get("/{result_id}")
async def get_test_result(result_id: int):
    """Get a single test result by ID."""
    result = storage.get_result(result_id)
    if not result:
        raise HTTPException(404, f"Test result #{result_id} not found")
    return result


@router.delete("/{result_id}")
async def delete_test_result(result_id: int):
    """Delete a test result."""
    if not storage.delete_result(result_id):
        raise HTTPException(404, f"Test result #{result_id} not found")
    return {"deleted": result_id}


# ── Coverage Badge ────────────────────────────────────

@badge_router.get("/coverage/{service}")
async def coverage_badge(service: str):
    """Generate an SVG coverage badge for a service.

    Usage in README: ![coverage](http://fenrir:8200/api/badges/coverage/muninn)
    """
    trend = storage.get_coverage_trend(service, limit=1)
    if not trend:
        pct = None
        color = "#9e9e9e"
        label = "N/A"
    else:
        pct = trend[0].coverage_pct
        label = f"{pct:.0f}%"
        if pct >= 80:
            color = "#4caf50"   # green
        elif pct >= 60:
            color = "#ff9800"   # orange
        else:
            color = "#f44336"   # red

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="106" height="20">
  <linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="106" height="20" fill="#555"/>
  <rect rx="3" x="62" width="44" height="20" fill="{color}"/>
  <rect rx="3" width="106" height="20" fill="url(#a)"/>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="11">
    <text x="32" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="32" y="14">coverage</text>
    <text x="83" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="83" y="14">{label}</text>
  </g>
</svg>"""

    return Response(content=svg, media_type="image/svg+xml")
