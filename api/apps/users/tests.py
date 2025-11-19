import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.apps.users.models import ActiveSession

User = get_user_model()


class UserRegisterViewTests(TestCase):
    """
    Test user registration: buyer and seller roles, invalid data.
    """
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("create_user")
        self.payload = {
            "username": "testuser",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }

    def test_register_valid_buyer(self):
        """Test registering a buyer with valid data"""
        self.payload["role"] = "buyer"
        response = self.client.post(
            self.register_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'username': 'testuser', 'role': 'buyer'})

        # Check that user was created
        self.assertTrue(User.objects.filter(username="testuser").exists())
        self.assertTrue(User.objects.get(username="testuser").role, "buyer")

    def test_register_valid_seller(self):
        """Test registering a seller with valid data"""
        self.payload["role"] = "seller"
        response = self.client.post(
            self.register_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'username': 'testuser', 'role': 'seller'})

        # Check that user was created
        self.assertTrue(User.objects.filter(username="testuser").exists())
        self.assertTrue(User.objects.get(username="testuser").role, "seller")

    def test_register_invalid_username(self):
        """Test registering with invalid username format"""
        self.payload["username"] = "invalid username!"
        self.payload["role"] = "buyer"

        response = self.client.post(
            self.register_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("username" in response.data)

    def test_register_invalid_role(self):
        self.payload["role"] = "admin"
        response = self.client.post(
            self.register_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_required_fields(self):
        """Test registering without required fields"""
        # Test missing role
        response = self.client.post(
            self.register_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("role" in response.data)

    def test_register_duplicate_username(self):
        """Test registering with a username that already exists"""
        User.objects.create_user(
            username="testuser",
            password="password123",  # noqa: S106
        )
        response = self.client.post(
            self.register_url, data=json.dumps(self.payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("username" in response.data)


class UserAuthTests(TestCase):
    """
    Test user authentication: login, token refresh, logout, logout all sessions.
    """
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")
        self.logout_all_url = reverse("logout_all")

        self.user = User.objects.create_user(
            username="testuser",
            password="StrongPassword123!",  # noqa: S106
            role="buyer"
        )

    def test_login_valid_credentials(self):
        """Test logging in with valid credentials"""
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        response = self.client.post(
            self.login_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_active_session(self):
        """Test active session"""
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        self.client.post(
            self.login_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(self.user.active_sessions.all().count(), 1)

    def test_login_invalid_credentials(self):
        """Test logging in with invalid credentials"""
        payload = {
            "username": "testuser",
            "password": "WrongPassword!"
        }
        response = self.client.post(
            self.login_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_refresh(self):
        """Test refreshing the access token"""
        login_payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        login_response = self.client.post(
            self.login_url, data=json.dumps(login_payload), content_type="application/json"
        )
        refresh_token = login_response.data["refresh"]

        refresh_payload = {
            "refresh": refresh_token
        }
        refresh_response = self.client.post(
            self.refresh_url, data=json.dumps(refresh_payload), content_type="application/json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)  

    def test_logout(self):
        """Test logging out from current session"""
        login_payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        login_response = self.client.post(
            self.login_url, data=json.dumps(login_payload), content_type="application/json"
        )
        access_token = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_response = self.client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertIn(logout_response.data["detail"], "Logged out successfully.")
    
    def test_logout_all(self):
        """Test logging out from all sessions"""
        login_payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        login_response = self.client.post(
            self.login_url, data=json.dumps(login_payload), content_type="application/json"
        )
        access_token = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_all_response = self.client.post(self.logout_all_url)
        self.assertEqual(logout_all_response.status_code, status.HTTP_200_OK)
        self.assertIn(logout_all_response.data["detail"], "Logged out from all sessions successfully.")

    def test_login_exceeds_max_sessions(self):
        """Test that logging in exceeds max active sessions"""
        max_sessions = settings.MAX_USER_SESSIONS
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }

        for _ in range(max_sessions):
            response = self.client.post(
                self.login_url, data=json.dumps(payload), content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.login_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("There is already an active session using your account.", response.data["detail"])

    def test_invalid_auth_token(self):
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        response = self.client.post(
            self.login_url, data=json.dumps(payload), content_type="application/json"
        )
        access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}ab')

        user_response = self.client.post(reverse("user_view"))
        self.assertEqual(user_response.status_code, status.HTTP_401_UNAUTHORIZED)



    def test_expired_active_session(self):
        payload = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        response = self.client.post(
            self.login_url, data=json.dumps(payload), content_type="application/json"
        )
        access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        ActiveSession.objects.all().delete()

        user_response = self.client.post(reverse("user_view"))
        self.assertEqual(user_response.status_code, status.HTTP_401_UNAUTHORIZED)



class UserDepositTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.deposit_url = reverse("deposit")
        self.user = User.objects.create_user(
            username="buyeruser",
            password="StrongPassword123!",  # noqa: S106
            role="buyer"
        )
        login_payload = {
            "username": "buyeruser",
            "password": "StrongPassword123!"
        }
        login_response = self.client.post(
            reverse("token_obtain_pair"),
            data=json.dumps(login_payload),
            content_type="application/json"
        )
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def test_deposit_valid_amount(self):
        """Test depositing a valid amount"""
        payload = {
            "amount": 100
        }
        response = self.client.post(
            self.deposit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("100 cents deposited successfully.", response.data["message"])
        self.assertEqual(response.data["current_deposit"], 100)

    def test_deposit_invalid_amount(self):
        """Test depositing an invalid amount"""
        payload = {
            "amount": 30
        }
        response = self.client.post(
            self.deposit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)
    
    def test_deposit_negative_amount(self):
        """Test depositing a negative amount"""
        payload = {
            "amount": -50
        }
        response = self.client.post(
            self.deposit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_seller_deposit_attempt(self):
        """Test that a seller cannot deposit"""
        User.objects.create_user(
            username="selleruser",
            password="StrongPassword123!",  # noqa: S106
            role="seller"
        )
        login_payload = {
            "username": "selleruser",
            "password": "StrongPassword123!"
        }
        login_response = self.client.post(
            reverse("token_obtain_pair"),
            data=json.dumps(login_payload),
            content_type="application/json"
        )
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        payload = {
            "amount": 100
        }
        response = self.client.post(
            self.deposit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ResetDepositViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.reset_deposit_url = reverse("reset_deposit")
        self.user = User.objects.create_user(
            username="buyeruser",
            password="StrongPassword123!",  # noqa: S106
            role="buyer",
            deposit=250
        )
        login_payload = {
            "username": "buyeruser",
            "password": "StrongPassword123!"
        }
        login_response = self.client.post(
            reverse("token_obtain_pair"),
            data=json.dumps(login_payload),
            content_type="application/json"
        )
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def test_reset_deposit(self):
        """Test resetting the deposit to zero"""
        response = self.client.post(self.reset_deposit_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Deposit reset successfully.", response.data["message"])
        self.assertEqual(response.data["previous_deposit"], 250)
        self.assertEqual(response.data["current_deposit"], 0)