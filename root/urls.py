from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls.i18n import i18n_patterns
from .views import health_check, language_test_view
from frontend_proxy import frontend_fallback_view


# setuping schema
schema_view = get_schema_view (
    openapi.Info (
        title="Django Rest Framework", 
        default_version="0.0.1", 
        description="This API is for Ecommerce App Backend",
    ),
    public=True, 
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
    patterns=[
        path('accounts/', include('Accounts.urls')),
        path('shop/', include('shop.urls')),
    ],
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),  # Add health check
    path('language-test/', language_test_view, name='language_test'),  # Add language test view
    # re_path(r'docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='docs'),
    re_path(r'^docs/$', csrf_exempt(schema_view.with_ui('swagger', cache_timeout=0)), name='docs'),
    path('accounts/', include('Accounts.urls'), name='account_users'),
    path('shop/', include('shop.urls'), name='shop_urls'),
    path("i18n/", include("django.conf.urls.i18n")),
    
    # Frontend proxy routes - these should be last to catch all other routes
    re_path(r'^(?!api|admin|docs|accounts|shop|media|static|health|language-test|i18n).*$', frontend_fallback_view, name='frontend_fallback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += i18n_patterns(path("admin/", admin.site.urls))


    