from unittest.mock import MagicMock, patch

import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from ai.models import AICallLog
from root.asgi import application

User = get_user_model()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser("admin@example.com", "password123")


@pytest.fixture
def normal_user():
    return User.objects.create_user("user@example.com", "password123")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@patch("ai.gateway.Groq")
@patch("ai.gateway.os.getenv", return_value="dummy_key")
def test_product_description_generate_view(
    mock_getenv, mock_groq_class, api_client, normal_user
):
    # Setup mock Groq response
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "This is a great product description."
    mock_completion.usage.prompt_tokens = 50
    mock_completion.usage.completion_tokens = 100
    mock_client.chat.completions.create.return_value = mock_completion

    api_client.force_authenticate(user=normal_user)
    url = reverse("ai_product_description")

    response = api_client.post(
        url, {"title": "Cool Shoes", "brand_name": "Nike"}, secure=True
    )

    assert response.status_code == 200
    assert response.data["description"] == "This is a great product description."

    # Verify AICallLog was created
    log = AICallLog.objects.first()
    assert log is not None
    assert log.feature_name == "product-description"
    assert log.prompt_tokens == 50
    assert log.completion_tokens == 100


@pytest.mark.django_db
@patch("ai.gateway.Groq")
@patch("ai.gateway.os.getenv", return_value="dummy_key")
def test_admin_triage_summary_view(
    mock_getenv, mock_groq_class, api_client, admin_user
):
    # Setup mock Groq response
    from shop.models import ContactMessage

    ContactMessage.objects.create(
        email="test@example.com", subject="Help", details="Broken"
    )

    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "Summary of pending issues."
    mock_completion.usage.prompt_tokens = 150
    mock_completion.usage.completion_tokens = 50
    mock_client.chat.completions.create.return_value = mock_completion

    api_client.force_authenticate(user=admin_user)
    url = reverse("ai_admin_triage")

    response = api_client.get(url, secure=True)

    assert response.status_code == 200
    assert response.data["summary"] == "Summary of pending issues."

    # Verify AICallLog was created
    log = AICallLog.objects.first()
    assert log is not None
    assert log.feature_name == "admin-triage"
    assert log.user == admin_user


@pytest.mark.django_db(transaction=True)
def test_unauthenticated_websocket_connection_rejected():
    async def _test():

        comm = WebsocketCommunicator(application, "/ws/ai/chat/")
        connected, code = await comm.connect()
        assert not connected
        assert code == 4401
        await comm.disconnect()

    import asyncio

    asyncio.run(_test())


@pytest.mark.django_db(transaction=True)
def test_authenticated_websocket_connection_and_greeting(normal_user):
    async def _test():
        from rest_framework_simplejwt.tokens import AccessToken

        token = str(AccessToken.for_user(normal_user))
        comm = WebsocketCommunicator(application, f"/ws/ai/chat/?token={token}")
        connected, _ = await comm.connect()
        assert connected

        greeting = await comm.receive_json_from()
        assert greeting["type"] == "connected"
        assert "greeting" in greeting
        await comm.disconnect()

    import asyncio

    asyncio.run(_test())


@pytest.mark.django_db(transaction=True)
def test_cookie_authenticated_websocket_connection(normal_user):
    async def _test():
        from rest_framework_simplejwt.tokens import AccessToken

        token = str(AccessToken.for_user(normal_user))
        headers = [(b"cookie", f"access_token={token}".encode("latin-1"))]
        comm = WebsocketCommunicator(application, "/ws/ai/chat/", headers=headers)
        connected, _ = await comm.connect()
        assert connected

        greeting = await comm.receive_json_from()
        assert greeting["type"] == "connected"
        await comm.disconnect()

    import asyncio

    asyncio.run(_test())


@pytest.mark.django_db(transaction=True)
def test_websocket_empty_message_validation(normal_user):
    async def _test():
        from rest_framework_simplejwt.tokens import AccessToken

        token = str(AccessToken.for_user(normal_user))
        comm = WebsocketCommunicator(application, f"/ws/ai/chat/?token={token}")
        connected, _ = await comm.connect()
        assert connected
        await comm.receive_json_from()  # consume greeting

        await comm.send_json_to({"type": "chat", "message": "   "})
        error_msg = await comm.receive_json_from()
        assert error_msg["type"] == "error"
        assert error_msg["message"] == "Message is required."
        await comm.disconnect()

    import asyncio

    asyncio.run(_test())


@pytest.mark.django_db(transaction=True)
def test_websocket_chat_streaming_flow(normal_user):
    async def _test():
        from rest_framework_simplejwt.tokens import AccessToken

        token = str(AccessToken.for_user(normal_user))
        comm = WebsocketCommunicator(application, f"/ws/ai/chat/?token={token}")
        connected, _ = await comm.connect()
        assert connected
        await comm.receive_json_from()  # consume greeting

        async def mock_stream(messages, user=None):
            yield "Hello "
            yield "there!"

        with patch("ai.consumers.stream_chat", side_effect=mock_stream):
            await comm.send_json_to(
                {"type": "chat", "message": "Help me choose", "history": []}
            )
            start_msg = await comm.receive_json_from()
            assert start_msg["type"] == "start"

            token1 = await comm.receive_json_from()
            assert token1 == {"type": "token", "text": "Hello "}

            token2 = await comm.receive_json_from()
            assert token2 == {"type": "token", "text": "there!"}

            done_msg = await comm.receive_json_from()
            assert done_msg["type"] == "done"

        await comm.disconnect()

    import asyncio

    asyncio.run(_test())


def test_sanitize_history():
    from ai.consumers import ShoppingAssistantConsumer

    raw = [
        {"role": "system", "content": "I am system"},
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
        {"role": "invalid", "content": "bad"},
        "not a dict",
    ]
    cleaned = ShoppingAssistantConsumer._sanitize_history(raw)
    assert len(cleaned) == 2
    assert cleaned == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]


@pytest.mark.django_db
def test_build_catalog():
    from ai.assistant import build_catalog

    catalog = build_catalog(limit=5)
    assert isinstance(catalog, str)
    assert len(catalog) > 0


@pytest.mark.django_db(transaction=True)
def test_stream_chat_fallback_and_call_log(normal_user):
    async def _test():
        from unittest.mock import AsyncMock

        from ai.assistant import stream_chat
        from ai.models import AICallLog

        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="First "))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content="token"))]

        async def mock_generator():
            yield chunk1
            yield chunk2

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[
                Exception("Primary model rate limited"),
                mock_generator(),
            ]
        )

        with patch("ai.assistant._client", return_value=mock_client):
            deltas = []
            async for d in stream_chat(
                [{"role": "user", "content": "Hi"}], user=normal_user
            ):
                deltas.append(d)

            assert "".join(deltas) == "First token"

            log = await AICallLog.objects.filter(user=normal_user).alast()
            assert log is not None
            assert log.success is True

    import asyncio

    asyncio.run(_test())
