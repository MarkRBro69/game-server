from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from users_app.models import CustomUserModel


class UserRegistrationTestCase(APITestCase):
    """
    Test case for the user registration API.
    """

    def setUp(self):
        """
        Method that runs before each test.
        """
        self.url = reverse('register_user')  # Specify the correct URL for registration

    def test_register_user_success(self):
        """
        Test for successful user registration.
        """
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Qecz1357',
            'password2': 'Qecz1357',
        }

        # Perform a POST request to the API with registration data
        response = self.client.post(self.url, data, format='json')

        # Check the response status code
        with self.subTest("Status code check"):
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify that the response contains the correct message
        with self.subTest("Message exists check"):
            self.assertIn('message', response.data)

        # Ensure that the response includes the user ID
        with self.subTest("User id exists check"):
            self.assertIn('user_id', response.data)

        with self.subTest("User in database check"):
            # Verify that the user exists in the database
            user = CustomUserModel.objects.get(username='testuser')  # Look up the user by username
            self.assertEqual(user.email, 'test@example.com')  # Check that the email is correct

    def test_register_user_empty_data(self):
        """
        Test for handling completely empty data during user registration.
        This test simulates a case where the user provides empty values for required fields,
        and checks if the appropriate validation error messages are returned by the API.
        """
        # Data with empty values for all required fields
        data = {
            'username': '',
            'email': '',
            'password1': '',
            'password2': '',
        }

        # Sending a POST request with the empty data
        response = self.client.post(self.url, data, format='json')

        # Checking that the status code is 400 (Bad Request) due to validation errors
        with self.subTest("Status code check"):
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Checking that the response contains an 'errors' field
        with self.subTest("Errors exists check"):
            self.assertIn('errors', response.data)

        # Checking that the errors are of type ValidationError
        with self.subTest("ValidationError check"):
            self.assertIsInstance(response.data['errors'], ValidationError)

        # Checking that the 'errors' field contains errors for each required field
        required_fields = ['username', 'email', 'password1', 'password2']
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, response.data['errors'].error_dict)

        # Checking that each error is a list and that it contains at least one error message
        for field, errors in response.data['errors'].error_dict.items():
            with self.subTest(field=field):
                self.assertIsInstance(errors, list)  # Checking that each error is a list
                self.assertGreater(len(errors), 0)  # Ensure there is at least one error

    def test_register_user_validation_error(self):
        """
        Test for user registration with validation errors. This test ensures that
        when invalid data is provided during registration, appropriate validation
        errors are returned with the correct status code and error messages.
        """

        # Perform a POST request to the API with registration data (valid case)
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Qecz1357',
            'password2': 'Qecz1357',
        }
        self.client.post(self.url, data, format='json')

        # Perform a POST request to the API with invalid registration data (validation error case)
        data = {
            'username': 'testuser',  # Duplicate username should cause error
            'email': 'test1@example.com',  # Email field is correct
            'password1': '12345',  # Weak password
            'password2': '12345',  # Weak password confirmation
        }
        response = self.client.post(self.url, data, format='json')

        # Checking that the status code is 400 (Bad Request) due to validation errors
        with self.subTest("Status code check"):
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Checking that the response contains an 'errors' field
        with self.subTest("Errors exists check"):
            self.assertIn('errors', response.data)

        # Checking that the errors are of type ValidationError
        with self.subTest("ValidationError check"):
            self.assertIsInstance(response.data['errors'], ValidationError)

        # Checking that the 'errors' field contains errors for each required field
        required_fields = ['username', 'password1']
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, response.data['errors'].error_dict)

        # Checking that each error is a list and that it contains at least one error message
        for field, errors in response.data['errors'].error_dict.items():
            with self.subTest(field=field):
                self.assertIsInstance(errors, list)  # Checking that each error is a list
                self.assertGreater(len(errors), 0)  # Ensure there is at least one error message
