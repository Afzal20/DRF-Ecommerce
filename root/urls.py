from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# setuping schema
schema_view = get_schema_view(
    openapi.Info(
        title="Django Rest Framework",
        default_version="0.0.1",
        description="This API is for Ecommerce App Backend",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("Accounts.urls"), name="account_uers"),
    path("shop/", include("shop.urls"), name="shop_urls"),
    path("api/v1/ai/", include("ai.urls"), name="ai_urls"),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^docs/$",
            csrf_exempt(schema_view.with_ui("swagger", cache_timeout=0)),
            name="docs",
        )
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
