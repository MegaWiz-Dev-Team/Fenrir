"""Tests for the OpenEMR Message Poller."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fenrir.openemr.message_poller import MessagePoller
from fenrir.openemr.models import OpenEMRMessage
from fenrir.openemr.openemr_client import OpenEMRClient


@pytest.fixture
def mock_client():
    """Create a mock OpenEMR client."""
    client = MagicMock(spec=OpenEMRClient)
    client.get_messages = AsyncMock(return_value=[])
    client.send_reply = AsyncMock(return_value={"id": 99})
    client.update_message_status = AsyncMock(return_value=True)
    return client


@pytest.fixture
def poller(mock_client):
    """Create a poller with mocked dependencies."""
    return MessagePoller(
        client=mock_client,
        poll_interval=5,
        fenrir_username="fenrir-ai",
        bifrost_url="http://bifrost:8100",
    )


def _make_message(
    msg_id: int = 1,
    body: str = "Hello Fenrir",
    from_user: str = "doctor1",
    patient_id: str = "42",
) -> OpenEMRMessage:
    """Helper to create an OpenEMRMessage."""
    return OpenEMRMessage.model_validate({
        "id": msg_id,
        "body": body,
        "from": from_user,
        "to": "fenrir-ai",
        "pid": patient_id,
        "message_status": "New",
        "type": "AI Query",
        "date": "2026-03-14",
        "title": "Test message",
    })


class TestMessagePoller:
    def test_poller_initial_status(self, poller):
        status = poller.status
        assert status.running is False
        assert status.messages_processed == 0
        assert status.errors == 0

    @pytest.mark.asyncio
    async def test_poller_handles_empty_inbox(self, poller, mock_client):
        mock_client.get_messages.return_value = []
        await poller._poll_once()
        assert poller.status.messages_processed == 0
        mock_client.send_reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_poller_skips_already_processed(self, poller, mock_client):
        msg = _make_message(msg_id=1)
        mock_client.get_messages.return_value = [msg]

        # Pre-mark as processed
        poller._processed_ids.add(1)

        await poller._poll_once()

        # Should not have sent a reply
        mock_client.send_reply.assert_not_called()
        assert poller.status.messages_processed == 0

    @pytest.mark.asyncio
    async def test_poller_processes_new_message(self, poller, mock_client):
        msg = _make_message(msg_id=5, body="สรุป clinical summary")
        mock_client.get_messages.return_value = [msg]

        with patch.object(
            poller, "_forward_to_bifrost", new_callable=AsyncMock
        ) as mock_fwd:
            mock_fwd.return_value = "Clinical summary: Patient is stable."
            await poller._poll_once()

        # Should have forwarded to Bifrost
        mock_fwd.assert_called_once_with(
            message="สรุป clinical summary",
            patient_id="42",
            from_user="doctor1",
        )

        # Should have sent reply
        mock_client.send_reply.assert_called_once()
        reply = mock_client.send_reply.call_args[0][0]
        assert reply.body == "Clinical summary: Patient is stable."
        assert reply.reply_mail_id == 5
        assert reply.pid == "42"

        # Should have marked as read
        mock_client.update_message_status.assert_called_once_with(5, "Read")

        # Should be tracked
        assert 5 in poller._processed_ids
        assert poller.status.messages_processed == 1

    @pytest.mark.asyncio
    async def test_poller_extracts_patient_context(self, poller, mock_client):
        msg = _make_message(
            msg_id=10,
            body="Check drug interactions",
            patient_id="99",
            from_user="nurse_a",
        )
        mock_client.get_messages.return_value = [msg]

        with patch.object(
            poller, "_forward_to_bifrost", new_callable=AsyncMock
        ) as mock_fwd:
            mock_fwd.return_value = "No interactions found."
            await poller._poll_once()

        mock_fwd.assert_called_once_with(
            message="Check drug interactions",
            patient_id="99",
            from_user="nurse_a",
        )

    @pytest.mark.asyncio
    async def test_poller_caps_processed_ids(self, poller, mock_client):
        # Fill with > 10000 IDs
        poller._processed_ids = set(range(10001))
        msg = _make_message(msg_id=99999)
        mock_client.get_messages.return_value = [msg]

        with patch.object(
            poller, "_forward_to_bifrost", new_callable=AsyncMock
        ) as mock_fwd:
            mock_fwd.return_value = "Response"
            await poller._poll_once()

        # Should have been trimmed to ~5001
        assert len(poller._processed_ids) <= 5002

    @pytest.mark.asyncio
    async def test_poller_forward_to_bifrost(self, poller):
        import httpx

        mock_response = httpx.Response(
            200,
            json={"response": "AI says hello"},
            request=httpx.Request("POST", "http://fake"),
        )

        with patch(
            "httpx.AsyncClient.post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response
            result = await poller._forward_to_bifrost(
                message="Hello",
                patient_id="1",
                from_user="doc",
            )

        assert result == "AI says hello"

    @pytest.mark.asyncio
    async def test_poller_bifrost_error_returns_fallback(self, poller):
        import httpx

        with patch(
            "httpx.AsyncClient.post",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Bifrost down"),
        ):
            result = await poller._forward_to_bifrost(
                message="Hello",
            )

        assert "ขออภัย" in result
        assert "Bifrost" in result


class TestPollerStatus:
    def test_status_updates_on_process(self, poller):
        assert poller.status.messages_processed == 0
        poller._status.messages_processed = 5
        assert poller.status.messages_processed == 5

    @pytest.mark.asyncio
    async def test_status_tracks_last_poll_time(self, poller, mock_client):
        mock_client.get_messages.return_value = []
        await poller._poll_once()
        assert poller.status.last_poll_time is not None
