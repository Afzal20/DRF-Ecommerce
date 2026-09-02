import logging

import stripe
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Order, Payment

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateStripeCheckoutSessionView(APIView):
    """
    Creates a Stripe Checkout Session for a specific Order.
    Requires Authentication.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Set the API key per-request so it reflects the current settings
        # (the module-level assignment is cached once at import time).
        stripe.api_key = settings.STRIPE_SECRET_KEY

        if not stripe.api_key:
            return Response(
                {"error": "Stripe API key is not configured on the server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        order_id = request.data.get("order_id")
        if not order_id:
            return Response(
                {"error": "order_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Fetch the order (ensure it belongs to the requesting user)
            order = Order.objects.get(id=order_id, user=request.user)

            if order.ordered:
                return Response(
                    {"error": "This order has already been paid for."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(
                                order.total_price * 100
                            ),  # Stripe expects amounts in cents
                            "product_data": {
                                "name": f"Order #{order.id}",
                            },
                        },
                        "quantity": 1,
                    },
                ],
                mode="payment",
                # Pass the internal order ID as metadata so we can identify it in the webhook
                client_reference_id=str(order.id),
                metadata={
                    "order_id": order.id,
                    "user_id": request.user.id,
                },
                success_url=request.data.get(
                    "success_url", request.build_absolute_uri("/payment-success/")
                ),
                cancel_url=request.data.get(
                    "cancel_url", request.build_absolute_uri("/payment-cancel/")
                ),
            )

            # Store the session ID in the order transaction_id
            order.transaction_id = checkout_session.id
            order.save()

            return Response(
                {"id": checkout_session.id, "url": checkout_session.url},
                status=status.HTTP_200_OK,
            )

        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StripeWebhookView(APIView):
    """
    Handles Stripe Webhook events.
    Does not require Authentication.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        if not sig_header:
            return Response(
                {"error": "Missing Stripe signature header"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event = None

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            # Invalid payload
            logger.error("Invalid Stripe payload")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            logger.error("Invalid Stripe signature")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Handle the checkout.session.completed event
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            self._handle_checkout_session(session)

        return Response(status=status.HTTP_200_OK)

    def _handle_checkout_session(self, session):
        order_id = session.get("metadata", {}).get("order_id")
        user_id = session.get("metadata", {}).get("user_id")

        if not order_id or not user_id:
            logger.error("Order ID or User ID missing in session metadata.")
            return

        try:
            order = Order.objects.get(id=order_id)

            # Mark order as ordered
            order.ordered = True
            order.save()

            # Create a corresponding Payment record
            Payment.objects.create(
                user_id=user_id,
                amount=session.get("amount_total", 0) / 100.0,
                payment_method="stripe",
                charge_id=session.get("payment_intent", session.get("id")),
                success=True,
            )

            logger.info(f"Payment successful for Order #{order.id}")

        except Order.DoesNotExist:
            logger.error(f"Order #{order_id} not found when processing webhook.")
        except Exception as e:
            logger.error(f"Error handling checkout session: {str(e)}")
