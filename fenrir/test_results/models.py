"""Test result data models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TestResultType(str, Enum):
    """Type of test execution."""
    UNIT = "unit"
    E2E = "e2e"
    UI = "ui"
    INTEGRATION = "integration"


class TestResultStatus(str, Enum):
    """Overall status of the test run."""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class TestResultCreate(BaseModel):
    """Request body for submitting a test result."""
    service: str = Field(..., description="Service name, e.g. 'muninn', 'mimir'")
    test_type: TestResultType = Field(..., description="Type of test: unit, e2e, ui")
    suite_name: Optional[str] = Field(None, description="Test suite name, e.g. 'cargo test'")

    # Counts
    total: int = Field(0, ge=0)
    passed: int = Field(0, ge=0)
    failed: int = Field(0, ge=0)
    skipped: int = Field(0, ge=0)
    errors: int = Field(0, ge=0)

    # Coverage (optional)
    coverage_pct: Optional[float] = Field(None, ge=0, le=100, description="Line coverage %")
    coverage_lines_total: Optional[int] = Field(None, ge=0)
    coverage_lines_covered: Optional[int] = Field(None, ge=0)
    coverage_branches_total: Optional[int] = Field(None, ge=0)
    coverage_branches_covered: Optional[int] = Field(None, ge=0)

    # Metadata
    duration_ms: Optional[int] = Field(None, ge=0, description="Total test duration in ms")
    git_commit: Optional[str] = Field(None, max_length=40)
    git_branch: Optional[str] = Field(None, max_length=255)
    ci_job_id: Optional[str] = Field(None, description="CI/CD job identifier")

    # Raw output (for detail drill-down)
    raw_output: Optional[str] = Field(None, description="Raw test output or JUnit XML")
    test_cases: Optional[list[dict]] = Field(None, description="Individual test case results")


class TestResult(BaseModel):
    """Stored test result with generated fields."""
    id: int
    service: str
    test_type: TestResultType
    suite_name: Optional[str]
    status: TestResultStatus

    total: int
    passed: int
    failed: int
    skipped: int
    errors: int

    coverage_pct: Optional[float]
    coverage_lines_total: Optional[int]
    coverage_lines_covered: Optional[int]
    coverage_branches_total: Optional[int]
    coverage_branches_covered: Optional[int]

    duration_ms: Optional[int]
    git_commit: Optional[str]
    git_branch: Optional[str]
    ci_job_id: Optional[str]

    created_at: datetime


class TestSummary(BaseModel):
    """Aggregated test summary for a service."""
    service: str
    latest_unit: Optional[TestResult] = None
    latest_e2e: Optional[TestResult] = None
    latest_ui: Optional[TestResult] = None
    total_runs: int = 0
    pass_rate: float = 0.0
    avg_coverage: Optional[float] = None


class CoverageTrend(BaseModel):
    """Coverage data point for trend charts."""
    date: str
    coverage_pct: float
    git_branch: Optional[str]
    git_commit: Optional[str]
