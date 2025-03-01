from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

CustomUserModel = get_user_model()


class GetUserTestCase(APITestCase):
    """
    Test cases for the get_user view.
    """

    def setUp(self):
        """Register a test user and generate JWT tokens."""
        self.url_register = reverse('register_user')
        self.url_get_user = reverse('get_user')

        # Register a new user
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Qecz1357',
            'password2': 'Qecz1357',
        }
        self.client.post(self.url_register, data, format='json')

        # Login to get JWT tokens
        login_data = {
            'username': 'testuser',
            'password': 'Qecz1357',
        }
        response = self.client.post(reverse('login'), login_data, format='json')

        self.access = response.data['access']
        self.refresh = response.data['refresh']
        self.user = response.data['user']

    def test_get_user_valid_access_token(self):
        """
        Test retrieving user data with a valid access token.
        Expected: 200 OK and user data.
        """
        self.client.cookies.clear()
        response = self.client.post(self.url_get_user, {'access': self.access}, format='json')

        with self.subTest('Check response status'):
            assert response.status_code == status.HTTP_200_OK

        with self.subTest('Check response data'):
            assert 'user' in response.data
            assert response.data['user']['username'] == self.user.get('username')

    def test_get_user_valid_access_token_in_cookies(self):
        """
        Test retrieving user data with a valid access token stored in cookies.
        Expected: 200 OK and user data.
        """
        self.client.cookies.clear()
        self.client.cookies['uat'] = self.access
        response = self.client.post(self.url_get_user, {}, format='json')

        with self.subTest('Check response status'):
            assert response.status_code == status.HTTP_200_OK

        with self.subTest('Check response data'):
            assert 'user' in response.data
            assert response.data['user']['username'] == self.user.get('username')

    def test_get_user_invalid_access_but_valid_refresh(self):
        """
        Test token refresh when the access token is invalid but the refresh token is valid.
        Expected: 200 OK, new access and refresh tokens, and user data.
        """
        self.client.cookies.clear()
        response = self.client.post(self.url_get_user, {'access': 'invalid', 'refresh': self.refresh}, format='json')

        with self.subTest('Check response status'):
            assert response.status_code == status.HTTP_200_OK

        with self.subTest('Check new tokens'):
            assert 'access' in response.data
            assert 'refresh' in response.data
            assert response.data['access'] is not None
            assert response.data['refresh'] is not None

        with self.subTest('Check response data'):
            assert 'user' in response.data
            assert response.data['user']['username'] == self.user.get('username')

    def test_get_user_invalid_tokens(self):
        """
        Test request with invalid access and refresh tokens.
        Expected: 401 Unauthorized.
        """
        self.client.cookies.clear()
        response = self.client.post(self.url_get_user, {'access': 'invalid', 'refresh': 'invalid'}, format='json')

        with self.subTest('Check response status'):
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        with self.subTest('Check error message'):
            assert response.data.get('error') == 'Invalid or expired token'

    def test_get_user_no_tokens(self):
        """
        Test request without any tokens.
        Expected: 401 Unauthorized.
        """
        self.client.cookies.clear()
        response = self.client.post(self.url_get_user, {}, format='json')

        with self.subTest('Check response status'):
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        with self.subTest('Check error message'):
            assert response.data.get('error') == 'Invalid or expired token'
