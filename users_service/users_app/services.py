from django.core.exceptions import ValidationError

from users_app.models import CustomUserModel


class UserService:
    @staticmethod
    def create_user(user_data):
        """
        Service method to create a new user.

        Args:
            user_data (dict): A dictionary containing user information required for creation.
                Expected keys:
                - 'username' (str): The username for the new user. Must be unique.
                - 'email' (str): The email address for the new user. Must be unique and in a valid email format.
                - 'password1' (str): The password for the new user. Must meet password strength requirements.
                - 'password2' (str): Confirmation of the password. Must match 'password1'.

        Returns:
            CustomUserModel: The created user instance.

        Raises:
            ValidationError: If validation errors occur during user creation, such as missing fields
            or failed uniqueness checks.
            Exception: For any other unexpected issues.
        """

        try:
            # Attempt to create a user using the custom manager
            return CustomUserModel.objects.create_user(user_data)

        except ValidationError as e:
            # Handle validation errors explicitly and return them as readable messages
            raise ValidationError(e.error_dict)

        except Exception as e:
            # Log or handle any unexpected exceptions
            raise Exception(f"An unexpected error occurred: {str(e)}")

    @staticmethod
    def add_win():
        pass

    @staticmethod
    def add_loss():
        pass

    @staticmethod
    def add_draw():
        pass

    @staticmethod
    def change_rating(rating):
        pass

    @staticmethod
    def get_rating():
        pass

    @staticmethod
    def get_profile():
        pass
