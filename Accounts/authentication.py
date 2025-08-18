from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationWithCookies(JWTAuthentication):
    def authenticate(self, request):
        # access_token = request.COOKIES.get('access_token')  # DISABLED: tokens are managed client-side via js-cookie
        access_token = None

        # Prefer Authorization header: "Bearer <token>"
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ', 1)[1].strip()

        # Optional fallback: allow token in request body (e.g., for simple POST verifications)
        if not access_token:
            try:
                access_token = request.data.get('token')  # may not exist on GET
            except Exception:
                access_token = None

        if not access_token:
            return None

        validated_token = self.get_validated_token(access_token)

        try:
            user = self.get_user(validated_token)

        except Exception as e:
            return None
        
        return (user, validated_token)
    
    