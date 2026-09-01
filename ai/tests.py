from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from ai.models import AICallLog

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
