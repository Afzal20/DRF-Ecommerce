from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView

# create a custom user login view and save the login credentials in cookies
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from Accounts.serializers import (
    ChangePasswordSerializer,
    GoogleLoginSerializer,
    LogoutSerializer,
    OtpVarificationSerializer,
    PasswordResetSerializer,
    ResetPasswordRequestSerializer,
    TokenVerificationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistratioinSerializer,
)


@method_decorator(csrf_exempt, name="dispatch")
class UserRegistrationView(generics.CreateAPIView):
    """
    View to handle user registration.
    """

    serializer_class = UserRegistratioinSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [throttling.ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_exempt, name="dispatch")
class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [throttling.ScopedRateThrottle]
    throttle_scope = "auth"

    @swagger_auto_schema(
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "message": "Login successful",
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                        },
                    }
                },
            ),
            400: "Invalid credentials",
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        response = Response(
            {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "access_token": str(access_token),
                "refresh_token": str(refresh),
            },
            status=status.HTTP_200_OK,
        )

        # # Set tokens in HTTP-only cookies
        # response.set_cookie(
        #     key='access_token',
        #     value=str(access_token),
        #     httponly=True,
        #     secure=True,
        #     samesite='None',
        #     path='/',
        # )

        # response.set_cookie(
        #     key='refresh_token',
        #     value=str(refresh),
        #     httponly=True,
        #     secure=True,
        #     samesite='None',
        #     path='/',
        # )

        return response


@method_decorator(csrf_exempt, name="dispatch")
class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_token_jwt = serializer.validated_data["id_token"]

        import requests
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            # use the access_token to fetch user info from Google
            response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {id_token_jwt}"},
            )

            if not response.ok:
                return Response(
                    {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                )

            idinfo = response.json()

            email = idinfo["email"]
            first_name = idinfo.get("given_name", "")
            last_name = idinfo.get("family_name", "")

            # Check if user exists, else create
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if created:
                # Set unusable password since they use Google
                user.set_unusable_password()
                user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response(
                {
                    "message": "Login successful",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "access_token": str(access_token),
                    "refresh_token": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        except ValueError:
            # Invalid token
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

    # get is for retrieving the user profile
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    # put is for updating the user profile
    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Reads refresh token from HTTP-only cookie, refreshes access and refresh tokens,
    and sets them back as cookies in the response.
    """

    def post(self, request, *args, **kwargs):
        # Try to get refresh token from cookie or request body
        refresh_token = (
            request.COOKIES.get("refresh_token")
            or request.data.get("refresh")
            or request.data.get("refresh_token")
        )

        if not refresh_token:
            return Response(
                {"detail": "Refresh token not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Create data dict for serializer
        data = {"refresh": refresh_token}

        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get("access")
        new_refresh_token = serializer.validated_data.get(
            "refresh", refresh_token
        )  # use new if provided

        user_data = None
        try:
            from django.contrib.auth import get_user_model
            from rest_framework_simplejwt.tokens import RefreshToken

            token = RefreshToken(refresh_token)
            user = get_user_model().objects.get(id=token["user_id"])
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        except Exception:
            pass

        response = Response(
            {
                "message": "Login successful",
                "user": user_data,
                "access_token": str(access_token),
                "new_refresh_token": str(new_refresh_token),
            },
            status=status.HTTP_200_OK,
        )

        # Set tokens in HTTP-only cookies
        # response.set_cookie(
        #     key='access_token',
        #     value=access_token,
        #     httponly=True,
        #     secure=True,  # Only over HTTPS in production
        #     samesite='Lax',
        #     max_age=60 * 5,  # adjust to match your access token lifetime
        # )

        # response.set_cookie(
        #     key='refresh_token',
        #     value=new_refresh_token,
        #     httponly=True,
        #     secure=True,
        #     samesite='Lax',
        #     max_age=60 * 60 * 24 * 7,  # adjust to match your refresh token lifetime
        # )

        return response


class CustomTokenVerifyView(TokenVerifyView):
    """
    it should read tokens from HTTP-only cookies and verify them.
    If the token is valid, it returns a success response
    """

    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get("access_token")

        if not access_token:
            return Response(
                {"detail": "Access token not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = {"token": access_token}
        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"detail": "Invalid or expired access token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({"detail": "token_is_valid"}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    View to handle user logout. It blacklists the refresh token and deletes the access and refresh tokens from cookies.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = LogoutSerializer

    @swagger_auto_schema(
        request_body=LogoutSerializer,
        responses={
            200: openapi.Response(
                description="Logged out successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            )
        },
    )
    def post(self, request, *args, **kwargs):
        refresh_token = (
            request.data.get("refresh")
            or request.data.get("refresh_token")
            or request.COOKIES.get("refresh_token")
        )

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass

        response = Response(
            {"detail": "Logged out successfully"}, status=status.HTTP_200_OK
        )
        # Clear cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response


class ChangePasswordAPIView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]  # Since you need to check old_password

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()  # This handles set_password and user.save()

        return Response(
            {"detail": "Password changed successfully."}, status=status.HTTP_200_OK
        )


class ResetPasswordRequestAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordRequestSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp"

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {
                    "Success": True,
                    "message": "OTP sent to your email. Please check your mail inbox.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"Success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class OtpVerificationAPIView(generics.GenericAPIView):
    serializer_class = OtpVarificationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp"

    def post(self, request, *args, **kwargs):
        serializer = OtpVarificationSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {
                    "Success": True,
                    "message": "OTP verified successfully. You can now reset your password.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"Success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PasswordResetAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            return Response(
                {"Success": True, "message": "Password reset successfully."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"Success": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


@method_decorator(csrf_exempt, name="dispatch")
class TokenVerificationView(APIView):
    """
    View to verify access token from cookies.
    If token is valid, responds with success.
    If token is invalid, responds with error message.
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Token verification result",
                examples={
                    "application/json": {"valid": True, "message": "Token is valid"}
                },
            ),
            401: openapi.Response(
                description="Token invalid or not provided",
                examples={
                    "application/json": {
                        "valid": False,
                        "message": "Invalid or expired token",
                    }
                },
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        # Get access token from cookies
        access_token = request.COOKIES.get("access_token")

        if not access_token:
            return Response(
                {"valid": False, "message": "Access token not provided in cookies"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Use serializer to validate token
        serializer = TokenVerificationSerializer()
        result = serializer.validate_token(access_token)

        if result["valid"]:
            return Response(
                {"valid": True, "message": "Token is valid"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"valid": False, "message": result["message"]},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    def get(self, request, *args, **kwargs):
        """
        GET method for token verification - same functionality as POST
        """
        return self.post(request, *args, **kwargs)
