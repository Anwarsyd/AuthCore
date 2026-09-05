from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, ChangePasswordSerializer, ProfileUpdateSerializer, LoginSerializer, ForgotPasswordSerializer,ResetPasswordSerializer

from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken


from .models import User
from django.contrib.auth.tokens import default_token_generator

# send verification email 
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework_simplejwt.views import TokenObtainPairView

class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            
            # for seding email verfication
            send_verification_email(user)

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

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            user = request.user

            user.set_password(
                serializer.validated_data["new_password"]
            )

            user.save()

            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
        
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        serializer = ProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "message": "Profile updated successfully",
                    "user": serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
        
class VerifyEmailView(APIView):

    def get(self, request, user_id, token):

        print("TOKEN RECEIVED:", token)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid verification link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        print("USER:", user.email)
        print("IS VERIFIED:", user.is_verified)
        print("TOKEN VALID:", default_token_generator.check_token(user, token))

        if user.is_verified:
            return Response(
                {"message": "Email already verified"},
                status=status.HTTP_200_OK
            )

        if default_token_generator.check_token(user, token):

            user.is_verified = True
            user.save(update_fields=["is_verified"])

            return Response(
                {"message": "Email verified successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"error": "Invalid or expired verification link"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
def send_verification_email(user):

    token = default_token_generator.make_token(user)

    verification_url = (
        "http://127.0.0.1:8000"
        + reverse(
            "verify_email",
            kwargs={
                "user_id": user.id,
                "token": token,
            }
        )
    )

    print("\n========================================")
    print("VERIFICATION URL:")
    print(verification_url)
    print("========================================\n")

    send_mail(
        subject="Verify your AuthCore account",
        message=(
            f"Hello {user.first_name},\n\n"
            "Please verify your email address by clicking the link below:\n\n"
            f"{verification_url}\n\n"
            "If you did not create this account, you can ignore this email."
        ),
        from_email="noreply@authcore.com",
        recipient_list=[user.email],
    )
    
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    
class ForgotPasswordView(APIView):

    def post(self, request):

        serializer = ForgotPasswordSerializer(
            data=request.data
        )

        if serializer.is_valid():

            email = serializer.validated_data["email"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {
                        "message": "If an account exists with this email, a password reset link has been sent."
                    },
                    status=status.HTTP_200_OK
                )

            token = default_token_generator.make_token(user)

            reset_url = (
                "http://127.0.0.1:8000"
                + reverse(
                    "reset_password",
                    kwargs={
                        "user_id": user.id,
                        "token": token,
                    },
                )
            )

            print("\n========================================")
            print("PASSWORD RESET URL:")
            print(reset_url)
            print("========================================\n")

            send_mail(
                subject="Reset your AuthCore password",
                message=(
                    f"Hello {user.first_name},\n\n"
                    "You requested a password reset.\n\n"
                    f"Reset your password using this link:\n\n"
                    f"{reset_url}\n\n"
                    "If you did not request this, you can ignore this email."
                ),
                from_email="noreply@authcore.com",
                recipient_list=[user.email],
            )

            return Response(
                {
                    "message": "If an account exists with this email, a password reset link has been sent."
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
        
class ResetPasswordView(APIView):

    def post(self, request, user_id, token):

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid password reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired password reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ResetPasswordSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user.set_password(
                serializer.validated_data["new_password"]
            )

            user.save()

            return Response(
                {"message": "Password reset successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )