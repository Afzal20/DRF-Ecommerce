import requests
from django.http import HttpResponse, HttpResponseNotFound, StreamingHttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class FrontendProxyView(View):
    """
    Proxy view that forwards requests to Next.js frontend
    """
    
    def get_frontend_url(self, path=''):
        return f"{settings.FRONTEND_URL}{path}"
    
    def proxy_request(self, request, path=''):
        """
        Proxy the request to the Next.js frontend
        """
        try:
            frontend_url = self.get_frontend_url(f"/{path}")
            
            # Forward query parameters
            if request.GET:
                query_string = request.GET.urlencode()
                frontend_url += f"?{query_string}"
            
            # Make request to Next.js server
            response = requests.get(
                frontend_url,
                headers={
                    'User-Agent': request.META.get('HTTP_USER_AGENT', ''),
                    'Accept': request.META.get('HTTP_ACCEPT', '*/*'),
                    'Accept-Language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
                    'Accept-Encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
                },
                stream=True,
                timeout=30
            )
            
            # Create Django response
            django_response = StreamingHttpResponse(
                response.iter_content(chunk_size=8192),
                content_type=response.headers.get('content-type', 'text/html'),
                status=response.status_code
            )
            
            # Forward relevant headers
            for header_name, header_value in response.headers.items():
                if header_name.lower() not in ['content-encoding', 'content-length', 'transfer-encoding']:
                    django_response[header_name] = header_value
            
            return django_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Frontend proxy error: {e}")
            return HttpResponseNotFound("Frontend service unavailable")
    
    def get(self, request, path=''):
        return self.proxy_request(request, path)
    
    def post(self, request, path=''):
        return self.proxy_request(request, path)


def frontend_fallback_view(request, path=''):
    """
    Fallback view for frontend routes
    """
    proxy_view = FrontendProxyView()
    return proxy_view.get(request, path)
