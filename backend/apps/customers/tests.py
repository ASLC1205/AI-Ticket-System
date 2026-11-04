from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class CustomerAuthorizationTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer", email="customer@example.com",
            password="SafePass!482", role="CUSTOMER",
        )
        self.agent = User.objects.create_user(
            username="agent", email="agent@example.com",
            password="SafePass!482", role="AGENT",
        )
        self.admin = User.objects.create_user(
            username="admin", email="admin@example.com",
            password="SafePass!482", role="ADMIN", is_staff=True,
        )
        self.role_only_admin = User.objects.create_user(
            username="roleonlyadmin", email="roleonlyadmin@example.com",
            password="SafePass!482", role="ADMIN", is_staff=False,
        )

    def test_customer_can_access_own_profile(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get("/api/customers/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.customer.email)

    def test_agent_cannot_access_customer_profile_endpoint(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get("/api/customers/profile/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_access_customer_profile_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/customers/profile/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_staff_admin_can_list_customers(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/customers/admin/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.role_only_admin)
        response = self.client.get("/api/customers/admin/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_and_agent_cannot_list_customers(self):
        for user in (self.customer, self.agent):
            with self.subTest(role=user.role):
                self.client.force_authenticate(user=user)
                response = self.client.get("/api/customers/admin/")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/customers/admin/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_staff_admin_can_change_customer_status(self):
        url = f"/api/customers/admin/{self.customer.pk}/status/"
        self.client.force_authenticate(user=self.customer)
        response = self.client.patch(url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_active)

    def test_customer_status_requires_boolean(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/customers/admin/{self.customer.pk}/status/",
            {"is_active": "false"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
