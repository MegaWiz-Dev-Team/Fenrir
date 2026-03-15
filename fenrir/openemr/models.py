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
