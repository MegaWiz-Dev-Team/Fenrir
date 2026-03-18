"""SQLite storage for test results."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from fenrir.test_results.models import (
    CoverageTrend,
    TestResult,
    TestResultCreate,
    TestResultStatus,
    TestResultType,
    TestSummary,
)

logger = logging.getLogger("fenrir.test_results")

DB_PATH = Path(__file__).parent.parent.parent / "data" / "test_results.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            test_type TEXT NOT NULL,
            suite_name TEXT,
            status TEXT NOT NULL,
            total INTEGER DEFAULT 0,
            passed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            skipped INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            coverage_pct REAL,
            coverage_lines_total INTEGER,
            coverage_lines_covered INTEGER,
            coverage_branches_total INTEGER,
            coverage_branches_covered INTEGER,
            duration_ms INTEGER,
            git_commit TEXT,
            git_branch TEXT,
            ci_job_id TEXT,
            raw_output TEXT,
            test_cases TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_service ON test_results(service);
        CREATE INDEX IF NOT EXISTS idx_test_type ON test_results(test_type);
        CREATE INDEX IF NOT EXISTS idx_created_at ON test_results(created_at);
    """)
    conn.close()
    logger.info(f"📊 Test results DB initialized at {DB_PATH}")


def insert_result(data: TestResultCreate) -> TestResult:
    """Insert a test result and return the stored record."""
    status = TestResultStatus.PASSED if data.failed == 0 and data.errors == 0 else TestResultStatus.FAILED
    test_cases_json = json.dumps(data.test_cases) if data.test_cases else None

    conn = _get_conn()
    cursor = conn.execute(
        """INSERT INTO test_results
           (service, test_type, suite_name, status,
            total, passed, failed, skipped, errors,
            coverage_pct, coverage_lines_total, coverage_lines_covered,
            coverage_branches_total, coverage_branches_covered,
            duration_ms, git_commit, git_branch, ci_job_id,
            raw_output, test_cases)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.service, data.test_type.value, data.suite_name, status.value,
            data.total, data.passed, data.failed, data.skipped, data.errors,
            data.coverage_pct, data.coverage_lines_total, data.coverage_lines_covered,
            data.coverage_branches_total, data.coverage_branches_covered,
            data.duration_ms, data.git_commit, data.git_branch, data.ci_job_id,
            data.raw_output, test_cases_json,
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()

    return get_result(row_id)


def get_result(result_id: int) -> Optional[TestResult]:
    """Get a single test result by ID."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM test_results WHERE id = ?", (result_id,)
    ).fetchone()
    conn.close()
    return _row_to_model(row) if row else None


def list_results(
    service: Optional[str] = None,
    test_type: Optional[str] = None,
    git_branch: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TestResult]:
    """List test results with filters."""
    conditions = []
    params = []

    if service:
        conditions.append("service = ?")
        params.append(service)
    if test_type:
        conditions.append("test_type = ?")
        params.append(test_type)
    if git_branch:
        conditions.append("git_branch = ?")
        params.append(git_branch)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    conn = _get_conn()
    rows = conn.execute(
        f"SELECT * FROM test_results {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params,
    ).fetchall()
    conn.close()

    return [_row_to_model(r) for r in rows]


def get_summary() -> list[TestSummary]:
    """Get aggregated summary for all services."""
    conn = _get_conn()
    services = [
        r["service"]
        for r in conn.execute("SELECT DISTINCT service FROM test_results").fetchall()
    ]

    summaries = []
    for svc in services:
        total_runs = conn.execute(
            "SELECT COUNT(*) as cnt FROM test_results WHERE service = ?", (svc,)
        ).fetchone()["cnt"]

        passed_runs = conn.execute(
            "SELECT COUNT(*) as cnt FROM test_results WHERE service = ? AND status = 'passed'",
            (svc,),
        ).fetchone()["cnt"]

        avg_cov = conn.execute(
            "SELECT AVG(coverage_pct) as avg_cov FROM test_results WHERE service = ? AND coverage_pct IS NOT NULL",
            (svc,),
        ).fetchone()["avg_cov"]

        summary = TestSummary(
            service=svc,
            total_runs=total_runs,
            pass_rate=round(passed_runs / total_runs * 100, 1) if total_runs > 0 else 0,
            avg_coverage=round(avg_cov, 1) if avg_cov else None,
        )

        # Latest by type
        for ttype in ["unit", "e2e", "ui"]:
            row = conn.execute(
                "SELECT * FROM test_results WHERE service = ? AND test_type = ? ORDER BY created_at DESC LIMIT 1",
                (svc, ttype),
            ).fetchone()
            if row:
                setattr(summary, f"latest_{ttype}", _row_to_model(row))

        summaries.append(summary)

    conn.close()
    return summaries


def get_coverage_trend(service: str, limit: int = 30) -> list[CoverageTrend]:
    """Get coverage trend for a service."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT coverage_pct, created_at, git_branch, git_commit
           FROM test_results
           WHERE service = ? AND coverage_pct IS NOT NULL
           ORDER BY created_at DESC LIMIT ?""",
        (service, limit),
    ).fetchall()
    conn.close()

    return [
        CoverageTrend(
            date=r["created_at"][:10],
            coverage_pct=r["coverage_pct"],
            git_branch=r["git_branch"],
            git_commit=r["git_commit"],
        )
        for r in reversed(rows)
    ]


def delete_result(result_id: int) -> bool:
    """Delete a test result."""
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM test_results WHERE id = ?", (result_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def _row_to_model(row: sqlite3.Row) -> TestResult:
    """Convert a database row to a TestResult model."""
    return TestResult(
        id=row["id"],
        service=row["service"],
        test_type=TestResultType(row["test_type"]),
        suite_name=row["suite_name"],
        status=TestResultStatus(row["status"]),
        total=row["total"],
        passed=row["passed"],
        failed=row["failed"],
        skipped=row["skipped"],
        errors=row["errors"],
        coverage_pct=row["coverage_pct"],
        coverage_lines_total=row["coverage_lines_total"],
        coverage_lines_covered=row["coverage_lines_covered"],
        coverage_branches_total=row["coverage_branches_total"],
        coverage_branches_covered=row["coverage_branches_covered"],
        duration_ms=row["duration_ms"],
        git_commit=row["git_commit"],
        git_branch=row["git_branch"],
        ci_job_id=row["ci_job_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
