"""Pydantic models for OpenEMR messages."""

from pydantic import BaseModel, Field


class OpenEMRMessage(BaseModel):
    """Represents a message from OpenEMR's Message Center."""

    id: int
    body: str = ""
    date: str = ""
    from_user: str = Field("", alias="from")
    to_user: str = Field("", alias="to")
    patient_id: str = Field("", alias="pid")
    message_status: str = Field("New", alias="message_status")
    msg_type: str = Field("", alias="type")
    title: str = ""
    # Thread tracking
    reply_to_id: int | None = Field(None, alias="reply_mail_id")

    model_config = {"populate_by_name": True}


class MessageReply(BaseModel):
    """Request body for replying to an OpenEMR message."""

    body: str
    groupname: str = "Default"
    # Reference to the original message
    reply_mail_id: int
    # Sender info
    sender_id: str = "fenrir-ai"
    # Inherit patient, type, title from original
    pid: str = ""
    msg_type: str = "AI Response"
    title: str = ""


class PollerStatus(BaseModel):
    """Status of the message poller background task."""

    enabled: bool = False
    running: bool = False
    last_poll_time: str | None = None
    messages_processed: int = 0
    poll_interval_secs: int = 15
    errors: int = 0
    last_error: str | None = None


# ── Workflow Models ──


class PatientFormData(BaseModel):
    """Data for registering a patient via OpenEMR web form."""

    first_name: str
    last_name: str
    dob: str = ""  # YYYY-MM-DD
    gender: str = "Male"  # Male, Female, Other
    phone: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    ssn: str = ""  # Optional — sensitive
    language: str = "English"


class VitalsFormData(BaseModel):
    """Data for recording patient vitals via OpenEMR web form."""

    patient_id: str
    systolic: str = ""  # mmHg
    diastolic: str = ""  # mmHg
    pulse: str = ""  # bpm
    temperature: str = ""  # °F or °C
    weight: str = ""  # kg or lbs
    height: str = ""  # cm or in
    oxygen_saturation: str = ""  # %
    respiration: str = ""  # /min
    notes: str = ""


class WorkflowResult(BaseModel):
    """Result from an OpenEMR workflow execution."""

    success: bool
    workflow: str  # e.g. "register_patient", "record_vitals", "clinical_report"
    message: str = ""
    screenshot: str | None = None  # base64 PNG
    session_id: str | None = None  # Ratatoskr session for follow-up
    text: str | None = None  # Extracted page text
    error: str | None = None
    fallback_used: bool = False  # True if fell back to FHIR API
