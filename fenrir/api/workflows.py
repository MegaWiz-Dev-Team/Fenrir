"""Workflows API — REST endpoints for OpenEMR clinical automation."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from fenrir.config import settings
from fenrir.openemr.models import PatientFormData, VitalsFormData, WorkflowResult
from fenrir.openemr.workflows import OpenEMRWorkflows

logger = logging.getLogger("fenrir.api.workflows")

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _get_workflows() -> OpenEMRWorkflows:
    """Create workflow engine from settings."""
    return OpenEMRWorkflows(
        openemr_url=settings.openemr_url,
        ratatoskr_url=settings.ratatoskr_url,
        mimir_url=settings.mimir_url,
    )


class ReportRequest(BaseModel):
    """Request body for clinical report generation."""
    patient_id: str


@router.post("/register-patient", response_model=WorkflowResult)
async def register_patient(data: PatientFormData):
    """Register a patient via OpenEMR form fill (Ratatoskr)."""
    wf = _get_workflows()
    result = await wf.register_patient_form(data)
    return result


@router.post("/record-vitals", response_model=WorkflowResult)
async def record_vitals(data: VitalsFormData):
    """Record patient vitals via OpenEMR form fill (Ratatoskr)."""
    wf = _get_workflows()
    result = await wf.record_vitals_form(data)
    return result


@router.post("/clinical-report", response_model=WorkflowResult)
async def clinical_report(req: ReportRequest):
    """Generate clinical report for a patient."""
    wf = _get_workflows()
    result = await wf.generate_clinical_report(req.patient_id)
    return result


@router.get("/status")
async def workflow_status():
    """Get workflow engine status."""
    return {
        "status": "ok",
        "ratatoskr_url": settings.ratatoskr_url,
        "mimir_url": settings.mimir_url,
        "openemr_url": settings.openemr_url,
    }
