from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Set security headers for every response."""

    def process_response(self, request, response):
        # Content Security Policy (allow inline styles/scripts for Django admin)
        if request.path.startswith("/admin/"):
            csp = (
                "default-src 'self'; "
                "img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; "
                "style-src-attr 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; "
                "script-src-attr 'unsafe-inline'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'"
            )
        else:
            csp = (
                "default-src 'self'; "
                "img-src 'self' data:; "
                "style-src 'self'; "
                "style-src-attr 'none'; "
                "script-src 'self'; "
                "script-src-attr 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'"
            )
        response.headers.setdefault("Content-Security-Policy", csp)

        # Additional hardening headers (only set if missing)
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")

        # Send a generic value so development servers don't add version details.
        response.headers["Server"] = "WebServer"
        response.headers.pop("X-Powered-By", None)

        return response
