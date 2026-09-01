from django.urls import path

from .views import AdminTriageSummaryView, ProductDescriptionGenerateView

urlpatterns = [
    path(
        "product-description/",
        ProductDescriptionGenerateView.as_view(),
        name="ai_product_description",
    ),
    path(
        "admin-triage/",
        AdminTriageSummaryView.as_view(),
        name="ai_admin_triage",
    ),
]
