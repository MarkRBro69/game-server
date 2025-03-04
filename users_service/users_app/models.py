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
    username = models.CharField(max_length=32, unique=True, blank=False, null=False, db_index=True)

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

    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    rating = models.IntegerField(default=1000, db_index=True)

    def __str__(self):
        """
        Return the string representation of the user.
        In this case, it's the username of the user.
        """
        return self.username


class CharacterType(models.TextChoices):
    HUMAN = 'Human'
    ORC = 'Orc'
    ELF = 'Elf'
    DWARF = 'Dwarf'


class CharacterModel(models.Model):
    owner = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name='characters')
    char_type = models.CharField(
        max_length=20,
        choices=CharacterType.choices,
        blank=False,
        null=False,
    )
    name = models.CharField(max_length=40, blank=False, null=False, db_index=True, unique=True)
    strength = models.IntegerField(blank=False, null=False)
    agility = models.IntegerField(blank=False, null=False)
    stamina = models.IntegerField(blank=False, null=False)
    endurance = models.IntegerField(blank=False, null=False)
    level = models.IntegerField(blank=False, null=False, default=1)
    experience = models.IntegerField(blank=False, null=False, default=0)

    objects = models.Manager()

    def __str__(self):
        return self.name

