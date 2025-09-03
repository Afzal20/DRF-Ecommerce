from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



# Simple health check view
def health_check(request):
    return JsonResponse({
        'status': 'OK',
        'message': 'Django server is running',
        'method': request.method,
        'path': request.path
    })

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
    # re_path(r'docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='docs'),
    re_path(r'^docs/$', csrf_exempt(schema_view.with_ui('swagger', cache_timeout=0)), name='docs'),
    path('accounts/', include('Accounts.urls'), name='account_uers'), 
    path('shop/', include('shop.urls'), name='shop_urls'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    