from django.urls import path

from Accounts.serializers import OtpVarificationSerializer
from Accounts.views import (
    CustomTokenRefreshView, 
    CustomTokenVerifyView, 
    LogoutView,
    ChangePasswordAPIView,
    OtpVerificationAPIView,
    PasswordResetAPIView,
    ResetPasswordRequestAPIView, 
    TokenVerificationView,
    UserLoginView, 
    UserProfileView, 
    UserRegistrationView
) 



urlpatterns = [
    path('user/register/', UserRegistrationView.as_view(), name='user_register'),
    path('user/login/', UserLoginView.as_view(), name='user_login'),
    path('user/profile/', UserProfileView.as_view(), name='user_profile'),
    path('password/change/', ChangePasswordAPIView.as_view(), name='password_change'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    path('token/verify-access/', TokenVerificationView.as_view(), name='token_verify_access'),
    path('logout/', LogoutView.as_view(), name='user_logout'),

    path('password-reset/request/', ResetPasswordRequestAPIView.as_view(), name='password_reset_request'),
    path('password-reset/enterOtp/', OtpVerificationAPIView.as_view(), name='otp_verification'),
    path('password-reset/set_new_password/', PasswordResetAPIView.as_view(), name='set_new_password'),
]