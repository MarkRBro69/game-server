from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from users_app.managers import CustomUserManager


class CustomUserModel(AbstractBaseUser):
    """
    CustomUserModel
    ===============
    Custom user model for handling user authentication and custom user fields.

    This model extends AbstractBaseUser to provide a custom user model with:
    - A unique username and email address.
    - Active, staff, and superuser flags.
    - Support for a custom user manager for user creation.
    """

    # The username field for the user (must be unique)
    username = models.CharField(max_length=32, unique=True, blank=False, null=False)

    # The email field for the user (must be unique)
    email = models.EmailField(unique=True, blank=False, null=False)

    # Password field
    password = models.CharField(max_length=128, blank=False, null=False)

    # Flag to mark whether the user is active
    is_active = models.BooleanField(default=True)

    # Flag to mark whether the user has staff privileges (used in admin)
    is_staff = models.BooleanField(default=False)

    # Flag to mark whether the user has superuser privileges
    is_superuser = models.BooleanField(default=False)

    # The custom manager used to handle user creation and superuser creation
    objects = CustomUserManager()

    # The field to be used for user authentication (this will be 'username')
    USERNAME_FIELD = 'username'

    def __str__(self):
        """
        Return the string representation of the user.
        In this case, it's the username of the user.
        """
        return self.username
