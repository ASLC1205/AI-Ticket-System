
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken
)

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode
)
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ProfileSerializer,
    LogoutSerializer,
    ChangePasswordSerializer
)

from .password_reset_serializers import PasswordResetRequestSerializer


User = get_user_model()


# Revoke all refresh tokens belonging to a user
def revoke_user_tokens(user):
    tokens = OutstandingToken.objects.filter(user=user)

    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)


# 1. User Registration
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


# 2. User Login
class LoginAPIView(TokenObtainPairView):
    serializer_class = LoginSerializer


# 3. View User Profile
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


# 4. User Logout
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK
        )


# 5. Change Password
class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Revoke existing refresh tokens
        revoke_user_tokens(request.user)

        return Response(
            {"message": "Password changed successfully. Please log in again."},
            status=status.HTTP_200_OK
        )


# 6. Password Reset Request
class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        user = User.objects.filter(
            email__iexact=email,
            is_active=True
        ).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            message = (
                f"Hello {user.username},\n\n"
                "You requested a password reset.\n"
                f"Your user ID: {uid}\n"
                f"Your reset token: {token}\n\n"
                "Use these values with the password reset confirmation API."
            )

            send_mail(
                subject="AI SupportHub - Password Reset",
                message=message,
                from_email=None,
                recipient_list=[email],
            )

        return Response(
            {
                "message": (
                    "If an account exists with this email, "
                    "password reset instructions will be sent."
                )
            },
            status=status.HTTP_200_OK
        )


# 7. Password Reset Confirmation
class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not uid or not token or not new_password:
            return Response(
                {"error": "UID, token and new password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid password reset link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired password reset token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)

        except ValidationError as error:
            return Response(
                {"error": error.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        # Revoke existing refresh tokens
        revoke_user_tokens(user)

        return Response(
            {"message": "Password reset successful. Please log in again."},
            status=status.HTTP_200_OK
        )


# 8. Google Login
class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get('credential')

        if not credential:
            return Response(
                {"error": "Google credential is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {"error": "Google login is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            google_user = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            email = google_user.get('email')
            email_verified = google_user.get('email_verified')

            if not email or not email_verified:
                return Response(
                    {"error": "Google email is not verified."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'role': 'CUSTOMER',
                    'is_active': True
                }
            )

            if not user.is_active:
                return Response(
                    {"error": "This account is inactive."},
                    status=status.HTTP_403_FORBIDDEN
                )

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Google login successful.",
                "created": created,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }, status=status.HTTP_200_OK)

        except ValueError:
            return Response(
                {"error": "Invalid Google credential."},
                status=status.HTTP_401_UNAUTHORIZED
            )
