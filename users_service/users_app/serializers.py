from rest_framework import serializers
from users_app.models import CustomUserModel, CharacterModel


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserModel
        # These are the fields that will be exposed to the client.
        fields = ['username', 'email', 'rating', 'wins', 'losses', 'draws']


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterModel
        fields = [
            'name',
            'owner',
            'char_type',
            'strength',
            'agility',
            'stamina',
            'endurance',
            'level',
            'experience',
            'unused_points',
        ]
        extra_kwargs = {
            'owner': {'read_only': True},
            'strength': {'read_only': True},
            'agility': {'read_only': True},
            'stamina': {'read_only': True},
            'endurance': {'read_only': True},
            'level': {'read_only': True},
            'experience': {'read_only': True},
            'unused_points': {'read_only': True},
        }
