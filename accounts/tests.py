from django.urls import reverse
from rest_framework.test import APITestCase
from .models import User

from django.contrib.auth.tokens import default_token_generator

class RegistrationTests(APITestCase):

    def test_user_registration(self):

        url = reverse("register")

        data = {
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

        response = self.client.post(
            url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 201)

    def test_registration_with_duplicate_email(self):

        data = {
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

        self.client.post(
            reverse("register"),
            data,
            format="json"
        )

        response = self.client.post(
            reverse("register"),
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_registration_with_weak_password(self):

        data = {
            "email": "weakuser@example.com",
            "password": "123",
            "first_name": "Weak",
            "last_name": "User",
        }

        response = self.client.post(
            reverse("register"),
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        
class LoginTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="login@example.com",
            password="StrongPassword123!",
            is_verified=True
        )

    def test_user_login(self):

        response = self.client.post(
            reverse("login"),
            {
                "email": "login@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
    
    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse("login"),
            {
                "email": "login@example.com",
                "password": "WrongPassword123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 401)
        
    def test_login_with_unverified_email(self):

        self.user.is_verified = False
        self.user.save()

        response = self.client.post(
            reverse("login"),
            {
                "email": "login@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        
    def test_refresh_token(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "login@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh_token
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        
    def test_old_refresh_token_is_blacklisted(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "login@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        refresh_token = login_response.data["refresh"]

        # First refresh
        response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh_token
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        # Try using the old refresh token again
        response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh_token
            },
            format="json"
        )

        self.assertEqual(response.status_code, 401)
        
class ProfileTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="StrongPassword123!",
            is_verified=True
        )

    def test_profile_requires_authentication(self):

        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(response.status_code, 401)
        
    def test_authenticated_user_can_access_profile(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["email"],
            "profile@example.com"
        )
        
    def test_user_can_update_profile(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.patch(
            reverse("profile_update"),
            {
                "first_name": "Updated",
                "last_name": "Name"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        
    def test_user_can_change_password(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            reverse("change_password"),
            {
                "old_password": "StrongPassword123!",
                "new_password": "NewPassword456!",
                "refresh": refresh_token
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewPassword456!")
        )
        
    def test_old_password_no_longer_works(self):

        self.user.set_password("NewPassword456!")
        self.user.save()

        response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 401)
        
    def test_user_can_logout(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            reverse("logout"),
            {
                "refresh": refresh_token
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        
    def test_blacklisted_refresh_token_cannot_be_used(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        refresh_token = login_response.data["refresh"]

        # Logout → blacklist the refresh token
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        logout_response = self.client.post(
            reverse("logout"),
            {
                "refresh": refresh_token
            },
            format="json"
        )

        self.assertEqual(logout_response.status_code, 200)

        # Try using the blacklisted token
        response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh_token
            },
            format="json"
        )

        self.assertEqual(response.status_code, 401)
        
        
    #last
    def test_change_password_with_wrong_old_password(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            reverse("change_password"),
            {
                "old_password": "WrongPassword123!",
                "new_password": "NewPassword456!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        
    def test_old_access_token_is_invalid_after_password_change(self):

        login_response = self.client.post(
            reverse("login"),
            {
                "email": "profile@example.com",
                "password": "StrongPassword123!"
            },
            format="json"
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        # Change password
        response = self.client.post(
            reverse("change_password"),
            {
                "old_password": "StrongPassword123!",
                "new_password": "NewPassword456!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        # Try using the OLD access token
        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(response.status_code, 401)
        
    def test_profile_with_invalid_token(self):

        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid-token"
        )

        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(response.status_code, 401)        
# test email verification
class EmailVerificationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="verify@example.com",
            password="StrongPassword123!",
            is_verified=False
        )

    def test_user_can_verify_email(self):

        token = default_token_generator.make_token(self.user)

        response = self.client.get(
            reverse(
                "verify_email",
                kwargs={
                    "user_id": self.user.id,
                    "token": token
                }
            )
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertTrue(self.user.is_verified)
        
    def test_invalid_verification_token(self):

        response = self.client.get(
            reverse(
                "verify_email",
                kwargs={
                    "user_id": self.user.id,
                    "token": "invalid-token"
                }
            )
        )

        self.assertEqual(response.status_code, 400)

        self.user.refresh_from_db()

        self.assertFalse(self.user.is_verified)
        
class ForgotPasswordTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="forgot@example.com",
            password="StrongPassword123!",
            is_verified=True
        )

    def test_forgot_password(self):

        response = self.client.post(
            reverse("forgot_password"),
            {
                "email": "forgot@example.com"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        
    def test_forgot_password_with_unknown_email(self):

        response = self.client.post(
            reverse("forgot_password"),
            {
                "email": "unknown@example.com"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["message"],
            "If an account exists with this email, a password reset link has been sent."
        )
        
    def test_reset_password(self):

        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse(
                "reset_password",
                kwargs={
                    "user_id": self.user.id,
                    "token": token
                }
            ),
            {
                "new_password": "NewPassword456!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewPassword456!")
        )
        
    def test_reset_password_with_invalid_token(self):

        response = self.client.post(
            reverse(
                "reset_password",
                kwargs={
                    "user_id": self.user.id,
                    "token": "invalid-token"
                }
            ),
            {
                "new_password": "NewPassword456!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("StrongPassword123!")
        )
    
    