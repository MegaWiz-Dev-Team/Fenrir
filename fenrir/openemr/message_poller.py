"""Message Poller — background task that polls OpenEMR for incoming messages.

Runs as an asyncio task during Fenrir's lifespan. Polls the OpenEMR
Message Center for messages addressed to the `fenrir-ai` user, forwards
them to Bifrost for AI processing, and posts replies back.
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from fenrir.config import settings
from fenrir.openemr.models import MessageReply, PollerStatus
from fenrir.openemr.openemr_client import OpenEMRClient

logger = logging.getLogger("fenrir.openemr.poller")


class MessagePoller:
    """Background poller for OpenEMR Message Center messages."""

    def __init__(
        self,
        client: OpenEMRClient | None = None,
        poll_interval: int | None = None,
        fenrir_username: str | None = None,
        bifrost_url: str | None = None,
    ):
        self.client = client or OpenEMRClient(
            base_url=settings.openemr_api_url,
            client_id=settings.openemr_client_id,
            client_secret=settings.openemr_client_secret,
            auth_token=settings.openemr_auth_token,
        )
        self.poll_interval = poll_interval or settings.message_poll_interval
        self.fenrir_username = fenrir_username or settings.fenrir_username
        self.bifrost_url = bifrost_url or settings.heimdall_url.replace(
            ":8080", ":8100"
        )

        # State
        self._processed_ids: set[int] = set()
        self._running = False
        self._task: asyncio.Task | None = None
        self._status = PollerStatus(
            enabled=settings.message_enabled,
            poll_interval_secs=self.poll_interval,
        )

    @property
    def status(self) -> PollerStatus:
        """Current poller status."""
        return self._status

    async def start(self) -> None:
        """Start the polling loop as a background task."""
        if self._running:
            logger.warning("Poller already running")
            return

        self._running = True
        self._status.running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            f"Message poller started (interval={self.poll_interval}s, "
            f"user={self.fenrir_username})"
        )

    async def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        self._status.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Message poller stopped")

    async def _poll_loop(self) -> None:
        """Main polling loop — runs continuously until stopped."""
        while self._running:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._status.errors += 1
                self._status.last_error = str(e)
                logger.error(f"Poller error: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _poll_once(self) -> None:
        """Execute a single poll cycle."""
        self._status.last_poll_time = datetime.now(timezone.utc).isoformat()

        # Fetch new messages for fenrir-ai
        messages = await self.client.get_messages(
            recipient=self.fenrir_username,
            status="New",
        )

        for msg in messages:
            # Skip already processed
            if msg.id in self._processed_ids:
                continue

            logger.info(
                f"New message #{msg.id} from '{msg.from_user}': "
                f"{msg.body[:80]}..."
            )

            # Forward to Bifrost and get AI response
            ai_response = await self._forward_to_bifrost(
                message=msg.body,
                patient_id=msg.patient_id,
                from_user=msg.from_user,
            )

            # Send reply back via OpenEMR
            reply = MessageReply(
                body=ai_response,
                reply_mail_id=msg.id,
                sender_id=self.fenrir_username,
                pid=msg.patient_id,
                title=f"Re: {msg.title}" if msg.title else "Fenrir AI Response",
            )
            await self.client.send_reply(reply)

            # Mark original as read
            await self.client.update_message_status(msg.id, "Read")

            # Track as processed
            self._processed_ids.add(msg.id)
            self._status.messages_processed += 1

            # Cap processed IDs to prevent unbounded growth
            if len(self._processed_ids) > 10000:
                # Keep only the most recent 5000
                sorted_ids = sorted(self._processed_ids)
                self._processed_ids = set(sorted_ids[-5000:])

    async def _forward_to_bifrost(
        self,
        message: str,
        patient_id: str = "",
        from_user: str = "",
    ) -> str:
        """Forward a message to Bifrost for AI processing.

        Returns the AI-generated response text.
        """
        url = f"{self.bifrost_url}/agents/default/invoke"

        # Build context-rich prompt
        context_parts = [message]
        if patient_id:
            context_parts.append(f"[Patient ID: {patient_id}]")
        if from_user:
            context_parts.append(f"[From: {from_user}]")

        payload = {
            "message": "\n".join(context_parts),
            "metadata": {
                "source": "openemr_message_center",
                "patient_id": patient_id,
                "from_user": from_user,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Agent": "fenrir",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                # Extract response text from Bifrost response
                if isinstance(data, dict):
                    return (
                        data.get("response", "")
                        or data.get("text", "")
                        or data.get("message", "")
                        or str(data)
                    )
                return str(data)

        except httpx.HTTPError as e:
            logger.error(f"Bifrost error: {e}")
            return (
                f"⚠️ ขออภัย ไม่สามารถประมวลผลได้ในขณะนี้ "
                f"(Bifrost error: {type(e).__name__})"
            )


# Global poller instance
_poller: MessagePoller | None = None


def get_poller() -> MessagePoller:
    """Get or create the global poller instance."""
    global _poller
    if _poller is None:
        _poller = MessagePoller()
    return _poller
