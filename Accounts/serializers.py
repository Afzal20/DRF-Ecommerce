from datetime import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile
from django.contrib.auth import authenticate
from django.core.mail import send_mail as send_email
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

# create a custom user serializer for user registration
class UserRegistratioinSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    

# create a custom user serializer for user login
class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        email = data.get("email", None)
        password = data.get("password", None)
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password is not found.'
            )

        return {
            'user': user,
        }


# create a custom user profile serializer
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, write_only=True)
    new_password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        fields = ('old_password', 'new_password')

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError("Old password is not correct")
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ('email',)

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
    
        # generate the OTP 
        user.generate_otp()

        send_email(
            "Password Reset OTP",
            f"Your OTP for password reset is {user.OTP}. It is valid for 10 minutes.",
            "afzalhossen2019@gmail.com",
            [user.email],
            fail_silently=False,
        )

        return value
    
class OtpVarificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    class Meta:
        fields = ('email', 'otp')

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        if user.OTP != data['otp'] or user.OTP_expiry < timezone.now():
            raise serializers.ValidationError("Invalid or expired OTP.")
        
        user.is_OTP_varified = True
        user.save()
        
        return data
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        fields = ('email', 'new_password')

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        if not user.is_OTP_varified:
            raise serializers.ValidationError("OTP is not verified.")
        
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.OTP = None
        user.OTP_expiry = None
        user.is_OTP_varified = False
        user.save()

        return user
    
class TokenVerificationSerializer(serializers.Serializer):
    """
    Serializer for verifying access tokens from cookies
    """
    def validate_token(self, access_token):
        """
        Validates the access token and returns user info if valid
        """
        try:
            # Validate the token
            UntypedToken(access_token)
            
            # If we reach here, token is valid
            return {
                'valid': True,
                'message': 'Token is valid'
            }
        except (InvalidToken, TokenError) as e:
            return {
                'valid': False,
                'message': 'Invalid or expired token'
            }

