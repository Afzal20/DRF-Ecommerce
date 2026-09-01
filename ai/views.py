from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.gateway import AIGateway, AIGatewayError
from shop.models import ContactMessage, Refund


class ProductDescriptionGenerateView(APIView):
    """
    Generates an SEO-friendly product description using Groq.
    Accessible to authenticated users (vendors).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        title = request.data.get("title")
        brand = request.data.get("brand_name")

        if not title:
            return Response(
                {"error": "Product title is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = f"Product Title: {title}\nBrand: {brand or 'Generic'}\nGenerate a professional, SEO-friendly e-commerce product description in 2 paragraphs."
        system_prompt = "You are an expert e-commerce copywriter. Write compelling, concise, and SEO-friendly product descriptions. Do not output anything other than the description itself (no conversational filler)."

        gateway = AIGateway()
        try:
            description = gateway.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                feature_name="product-description",
                user=request.user,
            )
            return Response({"description": description}, status=status.HTTP_200_OK)
        except AIGatewayError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class AdminTriageSummaryView(APIView):
    """
    Summarizes pending customer support and refund requests for admins.
    Accessible to admin users only.
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        messages = ContactMessage.objects.filter(status="Pending")[:10]
        refunds = Refund.objects.filter(accepted=False)[:10]

        if not messages and not refunds:
            return Response(
                {"summary": "No pending messages or refunds to summarize."},
                status=status.HTTP_200_OK,
            )

        prompt = "Here is the raw data for pending customer issues:\n\n"
        prompt += "--- Pending Messages ---\n"
        for msg in messages:
            prompt += f"Subject: {msg.subject}\nDetails: {msg.details}\n\n"

        prompt += "--- Pending Refunds ---\n"
        for refund in refunds:
            prompt += f"Order ID: {refund.order.id}\nReason: {refund.reason}\n\n"

        prompt += "Please provide a concise summary of the key themes in these issues and suggest which ones should be prioritized. Format your output with clear headings."

        system_prompt = "You are a customer support triage assistant for an e-commerce platform. Provide clear, actionable summaries of pending issues for the admin team."

        gateway = AIGateway()
        try:
            summary = gateway.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                feature_name="admin-triage",
                user=request.user,
            )
            return Response({"summary": summary}, status=status.HTTP_200_OK)
        except AIGatewayError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
