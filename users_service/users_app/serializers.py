from rest_framework import serializers
from users_app.models import CustomUserModel


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserModel
        # These are the fields that will be exposed to the client.
        fields = ['username', 'email', 'rating', 'wins', 'losses', 'draws']

