"""OpenEMR Workflows — clinical automation via Ratatoskr interact API.

Provides form-based patient registration, vitals recording, and clinical
report generation using browser automation (Ratatoskr /api/v1/interact).
Falls back to FHIR API when Ratatoskr is unavailable.
"""

import logging
from typing import Any

import httpx

from fenrir.openemr.models import PatientFormData, VitalsFormData, WorkflowResult

logger = logging.getLogger("fenrir.openemr.workflows")


class OpenEMRWorkflows:
    """Clinical workflow automation engine."""

    def __init__(
        self,
        openemr_url: str = "http://localhost:80",
        ratatoskr_url: str = "http://localhost:9200",
        fhir_url: str = "",
        mimir_url: str = "",
    ):
        self.openemr_url = openemr_url.rstrip("/")
        self.ratatoskr_url = ratatoskr_url.rstrip("/")
        self.fhir_url = fhir_url.rstrip("/") if fhir_url else f"{self.openemr_url}/apis/default/fhir"
        self.mimir_url = mimir_url.rstrip("/") if mimir_url else ""

    # ── Action Chain Builders ──

    def _build_patient_actions(self, patient: PatientFormData) -> list[dict[str, Any]]:
        """Build Ratatoskr action chain for patient registration form."""
        actions: list[dict[str, Any]] = []

        # OpenEMR new patient form fields
        field_map = {
            "#form_fname": patient.first_name,
            "#form_lname": patient.last_name,
            "#form_DOB": patient.dob,
            "#form_phone_home": patient.phone,
            "#form_email": patient.email,
            "#form_street": patient.address,
            "#form_city": patient.city,
            "#form_state": patient.state,
            "#form_postal_code": patient.zip_code,
        }

        for selector, value in field_map.items():
            if value:
                actions.append({"type": "fill", "selector": selector, "value": value})

        # Gender selection
        if patient.gender:
            actions.append({
                "type": "select", "selector": "#form_sex", "value": patient.gender,
            })

        # Language selection
        if patient.language:
            actions.append({
                "type": "select", "selector": "#form_language", "value": patient.language,
            })

        # Screenshot for verification
        actions.append({"type": "screenshot"})

        return actions

    def _build_vitals_actions(self, vitals: VitalsFormData) -> list[dict[str, Any]]:
        """Build Ratatoskr action chain for vitals recording form."""
        actions: list[dict[str, Any]] = []

        field_map = {
            "#form_bps": vitals.systolic,
            "#form_bpd": vitals.diastolic,
            "#form_pulse": vitals.pulse,
            "#form_temperature": vitals.temperature,
            "#form_weight": vitals.weight,
            "#form_height": vitals.height,
            "#form_oxygen_saturation": vitals.oxygen_saturation,
            "#form_respiration": vitals.respiration,
            "#form_note": vitals.notes,
        }

        for selector, value in field_map.items():
            if value:
                actions.append({"type": "fill", "selector": selector, "value": value})

        # Screenshot for verification
        actions.append({"type": "screenshot"})

        return actions

    # ── Workflow Executors ──

    async def register_patient_form(self, patient: PatientFormData) -> WorkflowResult:
        """Register patient via OpenEMR web form using Ratatoskr."""
        actions = self._build_patient_actions(patient)
        form_url = f"{self.openemr_url}/interface/new/new_comprehensive.php"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ratatoskr_url}/api/v1/interact",
                    json={"url": form_url, "actions": actions},
                )
                resp.raise_for_status()
                data = resp.json()

                error = data.get("error")
                return WorkflowResult(
                    success=error is None,
                    workflow="register_patient",
                    message=f"Filled {data.get('actions_completed', 0)}/{data.get('actions_total', 0)} fields",
                    screenshot=data.get("screenshot"),
                    session_id=data.get("session_id"),
                    text=data.get("text"),
                    error=error,
                )
        except httpx.ConnectError:
            logger.warning("Ratatoskr unavailable — falling back to FHIR API")
            return await self._fhir_create_patient(patient)
        except Exception as e:
            return WorkflowResult(
                success=False,
                workflow="register_patient",
                error=str(e),
            )

    async def record_vitals_form(self, vitals: VitalsFormData) -> WorkflowResult:
        """Record patient vitals via OpenEMR web form using Ratatoskr."""
        actions = self._build_vitals_actions(vitals)
        form_url = f"{self.openemr_url}/interface/forms/vitals/new.php?pid={vitals.patient_id}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ratatoskr_url}/api/v1/interact",
                    json={"url": form_url, "actions": actions},
                )
                resp.raise_for_status()
                data = resp.json()

                error = data.get("error")
                return WorkflowResult(
                    success=error is None,
                    workflow="record_vitals",
                    message=f"Recorded {data.get('actions_completed', 0)}/{data.get('actions_total', 0)} vitals",
                    screenshot=data.get("screenshot"),
                    session_id=data.get("session_id"),
                    error=error,
                )
        except httpx.ConnectError:
            return WorkflowResult(
                success=False,
                workflow="record_vitals",
                error="Ratatoskr unavailable",
            )
        except Exception as e:
            return WorkflowResult(
                success=False,
                workflow="record_vitals",
                error=str(e),
            )

    async def generate_clinical_report(self, patient_id: str) -> WorkflowResult:
        """Generate clinical report for a patient via OpenEMR UI."""
        report_url = f"{self.openemr_url}/interface/patient_file/report/pat_report.php?pid={patient_id}"

        actions = [
            {"type": "wait", "selector": "body"},
            {"type": "text", "selector": "body"},
            {"type": "screenshot"},
        ]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ratatoskr_url}/api/v1/interact",
                    json={"url": report_url, "actions": actions},
                )
                resp.raise_for_status()
                data = resp.json()

                return WorkflowResult(
                    success=data.get("error") is None,
                    workflow="clinical_report",
                    message=f"Report generated for patient {patient_id}",
                    screenshot=data.get("screenshot"),
                    session_id=data.get("session_id"),
                    text=data.get("text"),
                    error=data.get("error"),
                )
        except Exception as e:
            return WorkflowResult(
                success=False,
                workflow="clinical_report",
                error=str(e),
            )

    # ── FHIR Fallback ──

    async def _fhir_create_patient(self, patient: PatientFormData) -> WorkflowResult:
        """Fallback: create patient via FHIR API when Ratatoskr is down."""
        resource = {
            "resourceType": "Patient",
            "name": [{"use": "official", "family": patient.last_name, "given": [patient.first_name]}],
            "gender": patient.gender.lower() if patient.gender else "unknown",
        }
        if patient.dob:
            resource["birthDate"] = patient.dob

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.fhir_url}/Patient",
                    json=resource,
                    headers={"Content-Type": "application/fhir+json"},
                )
                resp.raise_for_status()
                return WorkflowResult(
                    success=True,
                    workflow="register_patient",
                    message="Patient created via FHIR API (fallback)",
                    fallback_used=True,
                )
        except Exception as e:
            return WorkflowResult(
                success=False,
                workflow="register_patient",
                error=f"Both Ratatoskr and FHIR failed: {e}",
                fallback_used=True,
            )

    # ── Mimir Integration ──

    async def index_to_mimir(
        self, message: str, response: str, patient_id: str = ""
    ) -> bool:
        """Index message and AI response to Mimir knowledge base."""
        if not self.mimir_url:
            logger.debug("Mimir URL not configured, skipping indexing")
            return False

        payload = {
            "tenant": "fenrir",
            "documents": [
                {
                    "content": f"Message: {message}\n\nAI Response: {response}",
                    "metadata": {
                        "source": "openemr_message_center",
                        "patient_id": patient_id,
                        "type": "message_exchange",
                    },
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.mimir_url}/api/tenants/fenrir/ingest",
                    json=payload,
                )
                resp.raise_for_status()
                logger.info(f"Indexed message to Mimir (patient={patient_id})")
                return True
        except httpx.ConnectError:
            logger.warning("Mimir unavailable — skipping indexing")
            return False
        except Exception as e:
            logger.warning(f"Mimir indexing failed: {e}")
            return False
