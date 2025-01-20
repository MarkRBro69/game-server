from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class UserLoginTestCase(APITestCase):
    def setUp(self):
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
        data = {
            'username': 'testuser',
            'password': 'Qecz1357',
        }

        response = self.client.post(self.url_login, data, format='json')

        with self.subTest('Status code check'):
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_wrong_password(self):
        data = {
            'username': 'testuser',
            'password': 'Qecz13579',
        }

        response = self.client.post(self.url_login, data, format='json')

        with self.subTest('Status code check'):
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

