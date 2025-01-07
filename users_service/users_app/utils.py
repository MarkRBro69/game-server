from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


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
