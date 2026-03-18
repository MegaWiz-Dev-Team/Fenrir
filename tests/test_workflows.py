"""🐺 Fenrir — TDD Tests for OpenEMR Workflows.

Tests patient registration, vitals recording, clinical reports,
Mimir indexing, and REST API endpoints.

Run: cd /Users/mimir/Developer/Fenrir && python -m pytest tests/test_workflows.py -v
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fenrir.openemr.models import (
    PatientFormData,
    VitalsFormData,
    WorkflowResult,
)


# ═══════════════════════════════════════════
# 1. Model Validation
# ═══════════════════════════════════════════


def test_patient_form_data_validation():
    """PatientFormData accepts required and optional fields."""
    patient = PatientFormData(
        first_name="Somchai",
        last_name="Jaidee",
        dob="1990-05-15",
        gender="Male",
        phone="0812345678",
    )
    assert patient.first_name == "Somchai"
    assert patient.last_name == "Jaidee"
    assert patient.dob == "1990-05-15"
    assert patient.gender == "Male"
    assert patient.phone == "0812345678"
    # Defaults
    assert patient.email == ""
    assert patient.language == "English"


def test_patient_form_data_requires_name():
    """PatientFormData requires first_name and last_name."""
    with pytest.raises(Exception):
        PatientFormData()  # type: ignore


def test_vitals_form_data_validation():
    """VitalsFormData accepts vitals measurements."""
    vitals = VitalsFormData(
        patient_id="P001",
        systolic="120",
        diastolic="80",
        pulse="72",
        temperature="98.6",
    )
    assert vitals.patient_id == "P001"
    assert vitals.systolic == "120"
    assert vitals.diastolic == "80"


def test_workflow_result_model():
    """WorkflowResult captures success/failure with optional screenshot."""
    result = WorkflowResult(
        success=True,
        workflow="register_patient",
        message="Patient registered",
        screenshot="base64data",
        session_id="abc-123",
    )
    assert result.success is True
    assert result.workflow == "register_patient"
    assert result.screenshot == "base64data"
    assert result.error is None
    assert result.fallback_used is False


# ═══════════════════════════════════════════
# 2. Workflows — Action Chain Building
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_register_patient_builds_actions():
    """register_patient_form should build correct Ratatoskr action chain."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
    )

    patient = PatientFormData(first_name="Somchai", last_name="Jaidee", dob="1990-05-15")
    actions = wf._build_patient_actions(patient)

    # Should have fill actions for name fields
    fill_actions = [a for a in actions if a["type"] == "fill"]
    assert len(fill_actions) >= 2  # at minimum first_name and last_name

    # Should end with screenshot
    assert actions[-1]["type"] == "screenshot"


@pytest.mark.asyncio
async def test_register_patient_success():
    """register_patient_form with mock Ratatoskr returns success."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
    )

    mock_response = {
        "session_id": "test-session",
        "url": "http://localhost:80/interface/new/new.php",
        "title": "New Patient",
        "actions_completed": 5,
        "actions_total": 5,
        "screenshot": "iVBORw0KGgo=",
        "error": None,
    }

    with patch("fenrir.openemr.workflows.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        patient = PatientFormData(first_name="Somchai", last_name="Jaidee")
        result = await wf.register_patient_form(patient)

        assert result.success is True
        assert result.workflow == "register_patient"
        assert result.screenshot == "iVBORw0KGgo="
        assert result.session_id == "test-session"


@pytest.mark.asyncio
async def test_register_patient_ratatoskr_down():
    """When Ratatoskr is down, should fallback to FHIR API."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
        fhir_url="http://test:80/apis/default/fhir",
    )

    import httpx

    with patch("fenrir.openemr.workflows.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        # First call (interact) fails with ConnectError
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        patient = PatientFormData(first_name="Somchai", last_name="Jaidee")
        result = await wf.register_patient_form(patient)

        # Should still succeed via fallback
        assert result.fallback_used is True
        assert result.workflow == "register_patient"


# ═══════════════════════════════════════════
# 3. Vitals Workflow
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_record_vitals_builds_actions():
    """record_vitals_form should build correct action chain."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
    )

    vitals = VitalsFormData(
        patient_id="P001", systolic="120", diastolic="80", pulse="72"
    )
    actions = wf._build_vitals_actions(vitals)

    fill_actions = [a for a in actions if a["type"] == "fill"]
    assert len(fill_actions) >= 3  # systolic, diastolic, pulse


@pytest.mark.asyncio
async def test_record_vitals_success():
    """record_vitals_form with mock Ratatoskr returns success."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
    )

    mock_response = {
        "session_id": "vitals-session",
        "url": "http://localhost:80/interface/forms/vitals",
        "title": "Vitals",
        "actions_completed": 4,
        "actions_total": 4,
        "screenshot": "iVBORw0KGgo=",
        "error": None,
    }

    with patch("fenrir.openemr.workflows.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        vitals = VitalsFormData(patient_id="P001", systolic="120", diastolic="80")
        result = await wf.record_vitals_form(vitals)

        assert result.success is True
        assert result.workflow == "record_vitals"


# ═══════════════════════════════════════════
# 4. Clinical Report
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_generate_report_success():
    """generate_clinical_report navigates to report page and screenshots."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
    )

    mock_response = {
        "session_id": "report-session",
        "url": "http://localhost:80/interface/patient_file/report",
        "title": "Clinical Report",
        "text": "Patient: Somchai Jaidee\nDiagnosis: Hypertension",
        "actions_completed": 3,
        "actions_total": 3,
        "screenshot": "iVBORw0KGgoAAAANS==",
        "error": None,
    }

    with patch("fenrir.openemr.workflows.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        result = await wf.generate_clinical_report("P001")

        assert result.success is True
        assert result.workflow == "clinical_report"
        assert result.screenshot is not None
        assert result.text is not None


@pytest.mark.asyncio
async def test_generate_report_includes_screenshot():
    """Report result must include base64 screenshot."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
    )

    mock_response = {
        "session_id": "rpt",
        "url": "http://localhost:80/report",
        "title": "Report",
        "text": "Summary",
        "actions_completed": 3,
        "actions_total": 3,
        "screenshot": "iVBORw0KGgoAAAANSUhEUgAA",
        "error": None,
    }

    with patch("fenrir.openemr.workflows.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        result = await wf.generate_clinical_report("P001")

        assert result.screenshot is not None
        assert len(result.screenshot) > 10


# ═══════════════════════════════════════════
# 5. Mimir Indexing
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_mimir_indexing():
    """Message + AI response should be sent to Mimir for indexing."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
        mimir_url="http://test:4200",
    )

    with patch("fenrir.openemr.workflows.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"status": "indexed"}
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        result = await wf.index_to_mimir(
            message="Patient asks about medication",
            response="Take aspirin 81mg daily",
            patient_id="P001",
        )

        assert result is True
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_mimir_indexing_failure_no_crash():
    """If Mimir is down, indexing should warn but not crash."""
    from fenrir.openemr.workflows import OpenEMRWorkflows

    wf = OpenEMRWorkflows(
        openemr_url="http://localhost:80",
        ratatoskr_url="http://test:9200",
        mimir_url="http://test:4200",
    )

    import httpx

    with patch("fenrir.openemr.workflows.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Mimir down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client

        result = await wf.index_to_mimir(
            message="Test", response="Test response", patient_id="P001"
        )

        assert result is False  # Failed but no exception raised


# ═══════════════════════════════════════════
# 6. REST API Endpoints
# ═══════════════════════════════════════════


@pytest.mark.asyncio
async def test_workflow_api_register():
    """POST /api/workflows/register-patient returns WorkflowResult."""
    from fenrir.config import settings
    settings.auth_enabled = False

    from httpx import ASGITransport, AsyncClient
    from fenrir.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/workflows/register-patient", json={
            "first_name": "Test",
            "last_name": "Patient",
            "dob": "2000-01-01",
        })
        # Should return 200 (even if Ratatoskr is down, fallback works)
        assert resp.status_code == 200
        data = resp.json()
        assert "workflow" in data
        assert data["workflow"] == "register_patient"


@pytest.mark.asyncio
async def test_workflow_api_vitals():
    """POST /api/workflows/record-vitals returns WorkflowResult."""
    from fenrir.config import settings
    settings.auth_enabled = False

    from httpx import ASGITransport, AsyncClient
    from fenrir.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/workflows/record-vitals", json={
            "patient_id": "P001",
            "systolic": "120",
            "diastolic": "80",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow"] == "record_vitals"


@pytest.mark.asyncio
async def test_workflow_api_report():
    """POST /api/workflows/clinical-report returns WorkflowResult."""
    from fenrir.config import settings
    settings.auth_enabled = False

    from httpx import ASGITransport, AsyncClient
    from fenrir.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/workflows/clinical-report", json={
            "patient_id": "P001",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow"] == "clinical_report"
