"""OpenEMR REST API client — handles messaging and OAuth2 authentication."""

import logging
from typing import Any

import httpx

from fenrir.openemr.models import MessageReply, OpenEMRMessage

logger = logging.getLogger("fenrir.openemr")


class OpenEMRClient:
    """Async HTTP client for OpenEMR Standard REST API (non-FHIR).

    Handles OAuth2 token management and message CRUD operations.
    """

    def __init__(
        self,
        base_url: str,
        client_id: str = "",
        client_secret: str = "",
        auth_token: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = auth_token
        self._token_expires_at: float = 0

    def _headers(self) -> dict[str, str]:
        """Build request headers with Bearer token."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Agent": "fenrir",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def refresh_token(self) -> bool:
        """Refresh OAuth2 access token using client credentials.

        Returns True if token was refreshed successfully.
        """
        if not self.client_id or not self.client_secret:
            logger.debug("No OAuth2 credentials configured, skipping token refresh")
            return bool(self._token)

        token_url = f"{self.base_url}/oauth2/default/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(token_url, data=payload)
                resp.raise_for_status()
                data = resp.json()
                self._token = data.get("access_token", "")
                logger.info("OAuth2 token refreshed successfully")
                return True
        except httpx.HTTPError as e:
            logger.error(f"OAuth2 token refresh failed: {e}")
            return False

    async def get_messages(
        self,
        recipient: str = "",
        status: str = "New",
    ) -> list[OpenEMRMessage]:
        """Fetch messages from OpenEMR Message Center.

        Args:
            recipient: Filter by recipient username (e.g., 'fenrir-ai')
            status: Filter by message status ('New', 'Read', etc.)

        Returns:
            List of OpenEMRMessage objects.
        """
        url = f"{self.base_url}/api/messages"
        params: dict[str, str] = {}
        if status:
            params["message_status"] = status

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()

            # OpenEMR returns {"data": [...]} or a list directly
            raw_messages = data if isinstance(data, list) else data.get("data", [])

            messages = []
            for item in raw_messages:
                try:
                    msg = OpenEMRMessage.model_validate(item)
                    # Filter by recipient if specified
                    if recipient and msg.to_user != recipient:
                        continue
                    messages.append(msg)
                except Exception as e:
                    logger.warning(f"Failed to parse message: {e}")
                    continue

            logger.info(
                f"Fetched {len(messages)} messages"
                + (f" for {recipient}" if recipient else "")
            )
            return messages

        except httpx.HTTPStatusError as e:
            logger.warning(f"OpenEMR API error: {e.response.status_code}")
            return []
        except httpx.HTTPError as e:
            logger.error(f"OpenEMR connection error: {e}")
            return []

    async def send_reply(self, reply: MessageReply) -> dict[str, Any]:
        """Send a reply message in OpenEMR Message Center.

        Args:
            reply: MessageReply with body, reply_mail_id, and metadata.

        Returns:
            API response dict.
        """
        url = f"{self.base_url}/api/messages"
        payload = reply.model_dump(by_alias=False)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url, json=payload, headers=self._headers()
                )
                resp.raise_for_status()
                logger.info(
                    f"Reply sent to message #{reply.reply_mail_id}"
                )
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to send reply: {e.response.status_code} "
                f"{e.response.text}"
            )
            return {"error": f"HTTP {e.response.status_code}"}
        except httpx.HTTPError as e:
            logger.error(f"Connection error sending reply: {e}")
            return {"error": str(e)}

    async def update_message_status(
        self, message_id: int, status: str = "Read"
    ) -> bool:
        """Update the status of a message (e.g., mark as Read).

        Returns True if update was successful.
        """
        url = f"{self.base_url}/api/messages/{message_id}"
        payload = {"message_status": status}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.put(
                    url, json=payload, headers=self._headers()
                )
                resp.raise_for_status()
                logger.info(f"Message #{message_id} status → {status}")
                return True
        except httpx.HTTPError as e:
            logger.warning(f"Failed to update message #{message_id}: {e}")
            return False
