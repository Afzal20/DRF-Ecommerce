from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user(user_id):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTCookieAuthMiddleware(BaseMiddleware):
    """
    Authenticates WebSocket connections using the same ``access_token``
    httpOnly cookie that ``Accounts.authentication.JWTAuthenticationWithCookies``
    uses for the REST API, so the storefront can reuse its auth session.
    """

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope["user"] = await self._resolve_user(scope)
        return await super().__call__(scope, receive, send)

    async def _resolve_user(self, scope):
        # 1) access_token cookie (same-origin browser clients)
        headers = dict(scope.get("headers", []))
        raw_cookies = headers.get(b"cookie", b"").decode("latin-1")
        cookies = {}
        for part in raw_cookies.split(";"):
            name, _, value = part.partition("=")
            if name.strip():
                cookies[name.strip()] = value.strip()
        token = cookies.get("access_token")

        # 2) ?token=<jwt> query param (cross-origin storefront clients whose
        #    httpOnly cookies live on a different host, e.g. Next.js proxy)
        if not token:
            query = scope.get("query_string", b"").decode("latin-1")
            for part in query.split("&"):
                name, _, value = part.partition("=")
                if name == "token" and value:
                    from urllib.parse import unquote

                    token = unquote(value)
                    break

        if not token:
            return AnonymousUser()

        try:
            validated_token = AccessToken(token)
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except TokenError:
            return AnonymousUser()

        return await _get_user(user_id)
