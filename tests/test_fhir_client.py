"""Tests for fenrir.fhir.client — FHIR R4 client."""

from fenrir.fhir.client import FHIRClient
from fenrir.fhir.models import PatientResource, HumanName, BundleResource


class TestFHIRClient:
    """FHIR client unit tests."""

    def test_client_creation(self):
        """Client should store base URL and auth token."""
        client = FHIRClient("http://localhost/fhir", "test-token")
        assert client.base_url == "http://localhost/fhir"
        assert client.auth_token == "test-token"

    def test_url_trailing_slash(self):
        """Should strip trailing slash from base URL."""
        client = FHIRClient("http://localhost/fhir/")
        assert client.base_url == "http://localhost/fhir"

    def test_build_url_resource(self):
        """Should build resource URL."""
        client = FHIRClient("http://localhost/fhir")
        assert client._build_url("Patient") == "http://localhost/fhir/Patient"

    def test_build_url_resource_id(self):
        """Should build resource URL with ID."""
        client = FHIRClient("http://localhost/fhir")
        url = client._build_url("Patient", "123")
        assert url == "http://localhost/fhir/Patient/123"

    def test_headers_with_auth(self):
        """Headers should include Bearer token when set."""
        client = FHIRClient("http://localhost/fhir", "my-token")
        headers = client._headers()
        assert headers["Authorization"] == "Bearer my-token"
        assert headers["Accept"] == "application/fhir+json"

    def test_headers_without_auth(self):
        """Headers should not include Authorization when empty."""
        client = FHIRClient("http://localhost/fhir")
        headers = client._headers()
        assert "Authorization" not in headers


class TestFHIRModels:
    """FHIR model tests."""

    def test_patient_model(self):
        """PatientResource should serialize correctly."""
        patient = PatientResource(
            id="123",
            name=[HumanName(family="Smith", given=["John"])],
            gender="male",
            birthDate="1990-01-01",
        )
        data = patient.model_dump()
        assert data["resourceType"] == "Patient"
        assert data["name"][0]["family"] == "Smith"

    def test_bundle_model(self):
        """BundleResource should have defaults."""
        bundle = BundleResource()
        assert bundle.resourceType == "Bundle"
        assert bundle.type == "searchset"
        assert bundle.total == 0
        assert bundle.entry == []
