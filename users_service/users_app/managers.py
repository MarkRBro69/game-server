from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


class CustomUserManager(BaseUserManager):
    """
    CustomUserManager
    =================
    Custom manager for handling user creation in a system where 'username' is the unique identifier.

    Methods:
    - create_user: Creates and returns a regular user instance with given fields.
    - create_superuser: Creates and returns a superuser with elevated privileges.

    Raises:
    - ValidationError: When required fields are missing or validation fails.
    """

    def create_user(self, user_data, **extra_fields):
        """
        Create and return a regular user.

        Args:
            user_data (dict): A dictionary containing:
                - 'username': Required string, unique username for the user.
                - 'email': Required string, email of the user.
                - 'password1' and 'password2': Password confirmation fields.
            **extra_fields: Additional attributes for the user model (e.g., 'is_active').

        Returns:
            user (CustomUserModel): The newly created user instance.

        Raises:
            ValidationError: If any required fields are missing or validation fails (e.g., duplicate username or email).
        """

        # Validate input data using the utility function
        errors = validate_user_data(self, user_data)
        if errors:
            raise ValidationError(errors)

        # Extract individual fields from the input dictionary
        username = user_data.get('username')
        email = user_data.get('email')
        password = user_data.get('password1')

        # Normalize email to ensure consistent storage
        normalized_email = self.normalize_email(email)

        # Create user instance with provided data and additional fields
        user = self.model(username=username, email=normalized_email, **extra_fields)

        # Set the hashed password for security
        user.set_password(password)

        # Save the user to the database
        user.save(using=self._db)

        # Return the created user
        return user

    def create_superuser(self, user_data, **extra_fields):
        """
        Create and return a superuser with elevated privileges.

        Superuser flags:
        - 'is_staff': Always set to True.
        - 'is_superuser': Always set to True.

        Args:
            user_data (dict): A dictionary containing:
                - 'username': Required string, unique username for the superuser.
                - 'email': Required string, email of the superuser.
                - 'password1' and 'password2': Password confirmation fields.
            **extra_fields: Additional attributes for the superuser model.

        Returns:
            user (CustomUserModel): The newly created superuser instance.

        Raises:
            ValidationError: If required fields are missing or validation fails.
        """

        # Set 'is_staff' and 'is_superuser' flags for superuser
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True

        # Use create_user method to create the superuser
        return self.create_user(user_data, **extra_fields)


def validate_user_data(manager, user_data):
    """
    Validate user data for creating or updating a user.

    Args:
        manager (BaseManager): A manager instance (e.g., User.objects) used to query the database for validation.
        user_data (dict): Dictionary containing the following keys:
            - 'username': Required, must be unique.
            - 'email': Required, must be a valid email format and unique.
            - 'password1': Required, must meet password validation requirements.
            - 'password2': Required, must match 'password1'.

    Returns:
        dict: A dictionary of validation errors. Keys represent field names, and values are error messages.
        If no errors are found, the dictionary is empty.

    Example:
        errors = validate_user_data(User.objects, user_data)
        if errors:
            raise ValidationError(errors)
    """

    errors = {}

    # Validate username
    if not user_data.get('username'):
        errors['username'] = 'Username is required'
    elif manager.filter(username=user_data['username']).exists():
        errors['username'] = 'Username is already taken'

    # Validate email
    if not user_data.get('email'):
        errors['email'] = 'Email is required'
    else:
        try:
            EmailValidator()(user_data['email'])
        except ValidationError:
            errors['email'] = 'Invalid email format'

        if manager.filter(email=user_data['email']).exists():
            errors['email'] = 'Email is already registered'

    # Validate password1
    if not user_data.get('password1'):
        errors['password1'] = 'Password is required'
    else:
        try:
            validate_password(user_data['password1'])
        except ValidationError as e:
            errors['password1'] = e.messages

    # Validate password2 (confirmation)
    if not user_data.get('password2'):
        errors['password2'] = 'Password confirmation is required'
    elif user_data.get('password1') != user_data.get('password2'):
        errors['password2'] = 'Passwords do not match'

    return errors