import pytest
from django.urls import reverse

from .factories import UserFactory


@pytest.mark.django_db
def test_user_creation():
    user = UserFactory()
    assert user.email is not None
    assert user.check_password("password123")


@pytest.mark.django_db
def test_api_client_can_reach_register_endpoint(api_client):
    url = reverse("user_register")
    response = api_client.post(url, data={})
    # just checking the endpoint exists and returns a validation error (400) or similar
    assert response.status_code in [400, 422]
