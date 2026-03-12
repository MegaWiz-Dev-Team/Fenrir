"""Task Router — determines API vs Browser path for clinical tasks.

Routes tasks to either the FHIR R4 API client (for data operations)
or the Browser Use agent (for UI-only workflows).
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("fenrir.tasks")


@dataclass
class TaskRouteResult:
    """Result of task routing."""
    method: str  # "fhir" or "browser"
    tool_name: str
    reason: str
    params: dict


# Task patterns that map to FHIR API operations
FHIR_PATTERNS: list[dict] = [
    {
        "keywords": ["register patient", "create patient", "add patient", "ลงทะเบียนคนไข้", "เพิ่มคนไข้"],
        "tool": "fhir_create_patient",
        "reason": "Patient registration is supported via FHIR Patient.create",
    },
    {
        "keywords": ["search patient", "find patient", "ค้นหาคนไข้", "หาคนไข้"],
        "tool": "fhir_search_patient",
        "reason": "Patient search is supported via FHIR Patient.search",
    },
    {
        "keywords": ["get patient", "patient detail", "ดูข้อมูลคนไข้"],
        "tool": "fhir_get_patient",
        "reason": "Patient retrieval is supported via FHIR Patient.read",
    },
    {
        "keywords": ["record vitals", "vital signs", "บันทึก bp", "บันทึกความดัน"],
        "tool": "fhir_create_observation",
        "reason": "Vital signs can be recorded via FHIR Observation.create",
    },
]

# Task patterns that require browser automation
BROWSER_PATTERNS: list[dict] = [
    {
        "keywords": ["fill form", "กรอกแบบฟอร์ม", "referral form", "ใบส่งตัว"],
        "tool": "browser_navigate",
        "reason": "Complex form filling requires browser automation",
    },
    {
        "keywords": ["print report", "generate report", "พิมพ์ใบ", "สรุปการรักษา"],
        "tool": "browser_navigate",
        "reason": "Report generation requires browser UI interaction",
    },
    {
        "keywords": ["screenshot", "capture screen", "จับภาพ"],
        "tool": "browser_navigate",
        "reason": "Screenshots require browser rendering",
    },
]


def route_task(task_description: str) -> TaskRouteResult:
    """Route a natural language task to the appropriate method.

    Args:
        task_description: Natural language description of the task

    Returns:
        TaskRouteResult with method, tool name, and reason
    """
    lower = task_description.lower()

    # Check FHIR patterns first (API is preferred when available)
    for pattern in FHIR_PATTERNS:
        for keyword in pattern["keywords"]:
            if keyword in lower:
                logger.info(f"Task routed to FHIR: {pattern['tool']} ({pattern['reason']})")
                return TaskRouteResult(
                    method="fhir",
                    tool_name=pattern["tool"],
                    reason=pattern["reason"],
                    params={"task": task_description},
                )

    # Check browser patterns
    for pattern in BROWSER_PATTERNS:
        for keyword in pattern["keywords"]:
            if keyword in lower:
                logger.info(f"Task routed to Browser: {pattern['tool']} ({pattern['reason']})")
                return TaskRouteResult(
                    method="browser",
                    tool_name=pattern["tool"],
                    reason=pattern["reason"],
                    params={"task": task_description},
                )

    # Fallback: try browser (can handle anything with LLM vision)
    logger.info("Task routed to Browser (fallback)")
    return TaskRouteResult(
        method="browser",
        tool_name="browser_navigate",
        reason="No specific API mapping found; falling back to browser automation",
        params={"task": task_description},
    )
