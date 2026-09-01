from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from shop.models import Order, Payment

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def normal_user():
    return User.objects.create_user("stripeuser@example.com", "password123")


@pytest.fixture
def order(normal_user):
    return Order.objects.create(
        user=normal_user,
        first_name="John",
        last_name="Doe",
        phone_number="+1234567890",
        district="Test District",
        upozila="Test Upozila",
        city="Test City",
        address="123 Test St",
        payment_method="card",
        phone_number_payment="+1234567890",
        ordered=False,
    )


@pytest.mark.django_db
@patch("shop.stripe_views.stripe.checkout.Session.create")
def test_create_checkout_session(mock_create, api_client, normal_user, order):
    mock_session = MagicMock()
    mock_session.id = "cs_test_123"
    mock_session.url = "https://checkout.stripe.com/test"
    mock_create.return_value = mock_session

    api_client.force_authenticate(user=normal_user)
    url = reverse("stripe-create-checkout")

    response = api_client.post(url, {"order_id": order.id}, secure=True)

    assert response.status_code == 200
    assert response.data["url"] == "https://checkout.stripe.com/test"

    order.refresh_from_db()
    assert order.transaction_id == "cs_test_123"


@pytest.mark.django_db
@patch("shop.stripe_views.stripe.Webhook.construct_event")
def test_stripe_webhook_view(mock_construct_event, api_client, normal_user, order):
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "payment_intent": "pi_test_123",
                "amount_total": 5000,  # $50.00
                "metadata": {
                    "order_id": str(order.id),
                    "user_id": str(normal_user.id),
                },
            }
        },
    }
    mock_construct_event.return_value = mock_event

    url = reverse("stripe-webhook")
    response = api_client.post(
        url,
        data="{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="dummy",
        secure=True,
    )

    assert response.status_code == 200

    order.refresh_from_db()
    assert order.ordered is True

    payment = Payment.objects.first()
    assert payment is not None
    assert payment.user == normal_user
    assert payment.amount == 50.0
    assert payment.charge_id == "pi_test_123"
    assert payment.success is True
