"""FHIR R4 Models — Pydantic models for FHIR resources."""

from pydantic import BaseModel


class HumanName(BaseModel):
    """FHIR HumanName."""
    use: str = "official"
    family: str = ""
    given: list[str] = []


class PatientResource(BaseModel):
    """FHIR Patient resource."""
    resourceType: str = "Patient"
    id: str = ""
    name: list[HumanName] = []
    gender: str = "unknown"
    birthDate: str = ""


class ObservationResource(BaseModel):
    """FHIR Observation resource (simplified)."""
    resourceType: str = "Observation"
    id: str = ""
    status: str = "final"
    code: dict = {}
    value: dict = {}
    subject: dict = {}


class BundleEntry(BaseModel):
    """FHIR Bundle entry."""
    resource: dict = {}


class BundleResource(BaseModel):
    """FHIR Bundle (search result)."""
    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int = 0
    entry: list[BundleEntry] = []
