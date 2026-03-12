"""FHIR R4 Client — async HTTP client for OpenEMR FHIR endpoints."""

import logging
from typing import Any

import httpx

logger = logging.getLogger("fenrir.fhir")


class FHIRClient:
    """Async FHIR R4 client for OpenEMR."""

    def __init__(self, base_url: str, auth_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
            "X-Agent": "fenrir",
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _build_url(self, resource: str, resource_id: str = "") -> str:
        """Build FHIR resource URL."""
        if resource_id:
            return f"{self.base_url}/{resource}/{resource_id}"
        return f"{self.base_url}/{resource}"

    async def search_patient(
        self,
        name: str = "",
        birthdate: str = "",
        identifier: str = "",
    ) -> dict[str, Any]:
        """Search for patients by name, birthdate, or identifier."""
        params: dict[str, str] = {}
        if name:
            params["name"] = name
        if birthdate:
            params["birthdate"] = birthdate
        if identifier:
            params["identifier"] = identifier
        if not params:
            params["_count"] = "20"

        url = self._build_url("Patient")
        logger.info(f"FHIR search patient: {url} params={params}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"FHIR search error: {e.response.status_code}")
            return {"error": f"FHIR error: {e.response.status_code}", "status": e.response.status_code}
        except httpx.HTTPError as e:
            logger.error(f"FHIR connection error: {e}")
            return {"error": f"Connection error: {e}"}

    async def get_patient(self, patient_id: str) -> dict[str, Any]:
        """Get a specific patient by ID."""
        url = self._build_url("Patient", patient_id)
        logger.info(f"FHIR get patient: {url}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"FHIR error: {e.response.status_code}", "status": e.response.status_code}
        except httpx.HTTPError as e:
            return {"error": f"Connection error: {e}"}

    async def create_patient(
        self,
        family_name: str,
        given_name: str,
        birthdate: str = "",
        gender: str = "unknown",
    ) -> dict[str, Any]:
        """Create a new patient resource."""
        resource = {
            "resourceType": "Patient",
            "name": [
                {
                    "use": "official",
                    "family": family_name,
                    "given": [given_name],
                }
            ],
            "gender": gender,
        }
        if birthdate:
            resource["birthDate"] = birthdate

        url = self._build_url("Patient")
        logger.info(f"FHIR create patient: {url}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=resource, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"FHIR error: {e.response.status_code}", "status": e.response.status_code}
        except httpx.HTTPError as e:
            return {"error": f"Connection error: {e}"}

    async def get_observations(self, patient_id: str) -> dict[str, Any]:
        """Get observations for a patient."""
        url = self._build_url("Observation")
        params = {"patient": patient_id}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"FHIR error: {e.response.status_code}", "status": e.response.status_code}
        except httpx.HTTPError as e:
            return {"error": f"Connection error: {e}"}
