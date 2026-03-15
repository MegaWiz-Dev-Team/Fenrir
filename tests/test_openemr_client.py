"""Tests for OpenEMR REST API client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from fenrir.openemr.models import MessageReply, OpenEMRMessage
from fenrir.openemr.openemr_client import OpenEMRClient


@pytest.fixture
def client():
    """Create a test client with a pre-set token."""
    return OpenEMRClient(
        base_url="http://openemr:80/apis/default/api",
        auth_token="test-token-123",
    )


@pytest.fixture
def client_with_oauth():
    """Create a test client with OAuth2 credentials."""
    return OpenEMRClient(
        base_url="http://openemr:80/apis/default/api",
        client_id="test-client-id",
        client_secret="test-client-secret",
    )


class TestOpenEMRClient:
    def test_headers_include_bearer_token(self, client):
        headers = client._headers()
        assert headers["Authorization"] == "Bearer test-token-123"
        assert headers["Accept"] == "application/json"
        assert headers["X-Agent"] == "fenrir"

    def test_headers_without_token(self):
        client = OpenEMRClient(base_url="http://localhost/api")
        headers = client._headers()
        assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_get_messages_parses_response(self, client):
        mock_response = httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 1,
                        "body": "สรุป clinical summary ให้หน่อย",
                        "from": "doctor1",
                        "to": "fenrir-ai",
                        "pid": "42",
                        "message_status": "New",
                        "type": "AI Query",
                        "date": "2026-03-14",
                        "title": "Request",
                    }
                ]
            },
            request=httpx.Request("GET", "http://fake"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            messages = await client.get_messages()

        assert len(messages) == 1
        assert messages[0].id == 1
        assert messages[0].body == "สรุป clinical summary ให้หน่อย"
        assert messages[0].to_user == "fenrir-ai"
        assert messages[0].patient_id == "42"

    @pytest.mark.asyncio
    async def test_get_messages_filters_by_recipient(self, client):
        mock_response = httpx.Response(
            200,
            json={
                "data": [
                    {"id": 1, "body": "msg1", "from": "doc", "to": "fenrir-ai",
                     "pid": "", "message_status": "New", "type": "", "date": "", "title": ""},
                    {"id": 2, "body": "msg2", "from": "doc", "to": "nurse1",
                     "pid": "", "message_status": "New", "type": "", "date": "", "title": ""},
                ]
            },
            request=httpx.Request("GET", "http://fake"),
        )

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            messages = await client.get_messages(recipient="fenrir-ai")

        assert len(messages) == 1
        assert messages[0].to_user == "fenrir-ai"

    @pytest.mark.asyncio
    async def test_send_reply_constructs_correct_payload(self, client):
        mock_response = httpx.Response(
            201,
            json={"id": 10},
            request=httpx.Request("POST", "http://fake"),
        )

        reply = MessageReply(
            body="นี่คือ clinical summary ของผู้ป่วย",
            reply_mail_id=1,
            sender_id="fenrir-ai",
            pid="42",
            title="Re: Request",
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.send_reply(reply)

        assert "error" not in result
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["body"] == "นี่คือ clinical summary ของผู้ป่วย"
        assert payload["reply_mail_id"] == 1

    @pytest.mark.asyncio
    async def test_oauth2_token_refresh(self, client_with_oauth):
        mock_response = httpx.Response(
            200,
            json={"access_token": "new-token-xyz", "token_type": "bearer"},
            request=httpx.Request("POST", "http://fake"),
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            success = await client_with_oauth.refresh_token()

        assert success is True
        assert client_with_oauth._token == "new-token-xyz"

    @pytest.mark.asyncio
    async def test_handles_network_error_gracefully(self, client):
        with patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            messages = await client.get_messages()

        assert messages == []

    @pytest.mark.asyncio
    async def test_update_message_status(self, client):
        mock_response = httpx.Response(
            200,
            json={"message": "updated"},
            request=httpx.Request("PUT", "http://fake"),
        )

        with patch("httpx.AsyncClient.put", new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response
            result = await client.update_message_status(1, "Read")

        assert result is True


class TestModels:
    def test_openemr_message_from_dict(self):
        data = {
            "id": 5,
            "body": "Hello Fenrir",
            "from": "doctor1",
            "to": "fenrir-ai",
            "pid": "10",
            "message_status": "New",
            "type": "AI Query",
            "date": "2026-03-14",
            "title": "Test",
        }
        msg = OpenEMRMessage.model_validate(data)
        assert msg.id == 5
        assert msg.from_user == "doctor1"
        assert msg.to_user == "fenrir-ai"
        assert msg.patient_id == "10"

    def test_message_reply_defaults(self):
        reply = MessageReply(
            body="AI response text",
            reply_mail_id=1,
        )
        assert reply.sender_id == "fenrir-ai"
        assert reply.msg_type == "AI Response"
        assert reply.groupname == "Default"
