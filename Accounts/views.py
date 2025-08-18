from django.shortcuts import render
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from Accounts.serializers import (
    ChangePasswordSerializer,
    OtpVarificationSerializer,
    PasswordResetSerializer,
    ResetPasswordRequestSerializer,
    TokenVerificationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistratioinSerializer,
)

from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from Accounts.models import CustomUserModel, UserProfile

# create a custom user login view and save the login credentials in cookies
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationView(generics.CreateAPIView):
    """
    View to handle user registration.
    """
    serializer_class = UserRegistratioinSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

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
                            "last_name": "Doe"
                        }
                    }
                }
            ),
            400: "Invalid credentials"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        response = Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'access_token': str(access_token),
            'refresh_token': str(refresh)
        }, status=status.HTTP_200_OK)

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

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get user profile",
        responses={
            200: UserProfileSerializer,
            401: "Authentication credentials were not provided",
            404: "User profile not found"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update user profile (full update)",
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: "Invalid data provided",
            401: "Authentication credentials were not provided",
            404: "User profile not found"
        },
        security=[{'Bearer': []}]
    )
    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Partially update user profile (including profile image)",
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: "Invalid data provided",
            401: "Authentication credentials were not provided",
            404: "User profile not found"
        },
        security=[{'Bearer': []}]
    )
    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get_object(self):
        return self.request.user.profile

class CustomTokenRefreshView(TokenRefreshView):
    """
    Reads refresh token from HTTP-only cookie, refreshes access and refresh tokens,
    and sets them back as cookies in the response.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                refresh_token = auth_header.split(' ', 1)[1].strip()
        if not refresh_token:
            return Response({'detail': 'Refresh token not provided in request.'}, status=status.HTTP_400_BAD_REQUEST)
        data = {'refresh': refresh_token}

        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'detail': 'Invalid or expired refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get('access')
        new_refresh_token = serializer.validated_data.get('refresh', refresh_token)  # use new if provided

        response = Response({
            'message': 'Token refreshed successfully',
            # 'user': {
            #     'id': user.id,
            #     'email': user.email,
            #     'first_name': user.first_name,
            #     'last_name': user.last_name,
            # },  # Disabled: no user context here
            'access_token': str(access_token),
            'refresh_token': str(new_refresh_token)
        }, status=status.HTTP_200_OK)

    # Set tokens in HTTP-only cookies (DISABLED - handled by frontend via js-cookie)
    # response.set_cookie(...)

        return response
    
class CustomTokenVerifyView(TokenVerifyView):
    """
    it should read tokens from HTTP-only cookies and verify them.
    If the token is valid, it returns a success response
    """
    def post(self, request, *args, **kwargs):
        # access_token = request.COOKIES.get('access_token')  # DISABLED - expect token from header/body
        access_token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ', 1)[1].strip()
        if not access_token:
            access_token = request.data.get('token')
        if not access_token:
            return Response({'detail': 'Access token not provided (expected in Authorization header or body).'}, status=status.HTTP_401_UNAUTHORIZED)

        data = {'token': access_token}
        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'detail': 'Invalid or expired access token.'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({'detail': 'token_is_valid'}, status=status.HTTP_200_OK)
    
class LogoutView(APIView):
    """
    View to handle user logout. it should delete the access and refresh tokens from cookies.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):

        response = Response({'detail': 'Logged out successfully'}, status=status.HTTP_200_OK)
    # Clear cookies (DISABLED - tokens handled on client via js-cookie)
    # response.delete_cookie('access_token')
    # response.delete_cookie('refresh_token')

        return response
    
class ChangePasswordAPIView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]  # Since you need to check old_password

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()  # This handles set_password and user.save()
        
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)

class ResetPasswordRequestAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                'Success': True,
                'message': 'OTP sent to your email. Please check your mail inbox.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'Success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
class OtpVerificationAPIView(generics.GenericAPIView):
    serializer_class = OtpVarificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = OtpVarificationSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                'Success': True,
                'message': 'OTP verified successfully. You can now reset your password.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'Success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
class PasswordResetAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            return Response({
                'Success': True,
                'message': 'Password reset successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'Success': False,
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
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
                    "application/json": {
                        "valid": True,
                        "message": "Token is valid"
                    }
                }
            ),
            401: openapi.Response(
                description="Token invalid or not provided",
                examples={
                    "application/json": {
                        "valid": False,
                        "message": "Invalid or expired token"
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        # Get access token from cookies (DISABLED - expect in header/body)
        # access_token = request.COOKIES.get('access_token')
        access_token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ', 1)[1].strip()
        if not access_token:
            access_token = request.data.get('token')
        if not access_token:
            return Response({
                'valid': False,
                'message': 'Access token not provided (expected in Authorization header or in request body as "token")'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Use serializer to validate token
        serializer = TokenVerificationSerializer()
        result = serializer.validate_token(access_token)
        
        if result['valid']:
            return Response({
                'valid': True,
                'message': 'Token is valid'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'valid': False,
                'message': result['message']
            }, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, *args, **kwargs):
        """
        GET method for token verification - same functionality as POST
        """
        return self.post(request, *args, **kwargs)