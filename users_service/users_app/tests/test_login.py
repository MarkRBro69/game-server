from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class UserLoginTestCase(APITestCase):
    """
    Test cases for the login view.
    """
    def setUp(self):
        """Set up test user before each test."""
        self.url_register = (reverse('register_user'))
        self.url_login = (reverse('login'))

        # Perform a POST request to the API with registration data (valid case)
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Qecz1357',
            'password2': 'Qecz1357',
        }
        self.client.post(self.url_register, data, format='json')

    def test_login_success(self):
        """
        Test successful login with valid credentials.
        Expected: 200 OK, access and refresh tokens in response and cookies.
        """
        self.client.cookies.clear()
        data = {
            'username': 'testuser',
            'password': 'Qecz1357',
        }

        response = self.client.post(self.url_login, data, format='json')

        with self.subTest("Check response status"):
            assert response.status_code == status.HTTP_200_OK

        with self.subTest("Check response data"):
            assert 'access' in response.data
            assert 'refresh' in response.data
            assert 'user' in response.data

        with self.subTest("Check cookies"):
            assert 'uat' in response.cookies
            assert 'urt' in response.cookies

    def test_login_wrong_password(self):
        """
        Test login with incorrect credentials.
        Expected: 400 Bad Request.
        """
        self.client.cookies.clear()
        data = {
            'username': 'testuser',
            'password': 'Qecz13579',
        }

        response = self.client.post(self.url_login, data, format='json')

        with self.subTest("Check response status"):
            assert response.status_code == status.HTTP_400_BAD_REQUEST

        with self.subTest("Check error message"):
            assert response.data.get('error') == 'Invalid credentials'

        with self.subTest("Check tokens are missing"):
            assert 'access' not in response.data
            assert 'refresh' not in response.data
            assert 'user' not in response.data

        with self.subTest("Check cookies"):
            assert 'uat' not in response.cookies
            assert 'urt' not in response.cookies

    def test_login_missing_fields(self):
        """
        Test login with missing fields in the request.
        Expected: 400 Bad Request.
        """
        self.client.cookies.clear()
        response = self.client.post(self.url_login, {}, format='json')

        with self.subTest("Check response status"):
            assert response.status_code == status.HTTP_400_BAD_REQUEST

        with self.subTest("Check error message"):
            assert response.data.get('error') == 'Invalid credentials'

        with self.subTest("Check tokens are missing"):
            assert 'access' not in response.data
            assert 'refresh' not in response.data
            assert 'user' not in response.data
