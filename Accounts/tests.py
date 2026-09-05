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
    response = api_client.post(url, data={}, secure=True)
    # just checking the endpoint exists and returns a validation error (400) or similar
    assert response.status_code in [400, 422]


@pytest.mark.django_db
def test_logout_blacklists_refresh_token_from_body(api_client):
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
    from rest_framework_simplejwt.tokens import RefreshToken

    user = UserFactory()
    refresh = RefreshToken.for_user(user)
    refresh_str = str(refresh)

    url = reverse("user_logout")
    response = api_client.post(url, data={"refresh": refresh_str}, format="json")
    assert response.status_code == 200
    assert response.data["detail"] == "Logged out successfully"

    # Token must be blacklisted in DB
    assert BlacklistedToken.objects.filter(token__token=refresh_str).exists()

    # Attempting to refresh should be rejected
    refresh_url = reverse("token_refresh")
    refresh_response = api_client.post(
        refresh_url, data={"refresh": refresh_str}, format="json"
    )
    assert refresh_response.status_code == 401


@pytest.mark.django_db
def test_logout_blacklists_refresh_token_from_cookies(api_client):
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
    from rest_framework_simplejwt.tokens import RefreshToken

    user = UserFactory()
    refresh = RefreshToken.for_user(user)
    refresh_str = str(refresh)

    api_client.cookies["refresh_token"] = refresh_str
    url = reverse("user_logout")
    response = api_client.post(url)
    assert response.status_code == 200
    assert BlacklistedToken.objects.filter(token__token=refresh_str).exists()
