from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationAndAuthenticationTests(APITestCase):
    def test_public_registration_always_creates_customer(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "newcustomer",
                "email": "newcustomer@example.com",
                "password": "SafePass!482",
                "phone": "9876543210",
                "role": "ADMIN",
                "is_staff": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newcustomer@example.com")
        self.assertEqual(user.role, "CUSTOMER")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password("SafePass!482"))

    def test_registration_rejects_weak_password(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "weakpassworduser",
                "email": "weak@example.com",
                "password": "12345678",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())

    def test_email_login_returns_jwt_tokens(self):
        User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="SafePass!482",
            role="CUSTOMER",
        )
        response = self.client.post(
            "/api/accounts/login/",
            {"email": "login@example.com", "password": "SafePass!482"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
