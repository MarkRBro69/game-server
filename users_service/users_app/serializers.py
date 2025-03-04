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
        fields = ['name', 'owner', 'char_type', 'strength', 'agility', 'stamina', 'endurance', 'level', 'experience']
        extra_kwargs = {'owner': {'read_only': True}}

    def validate(self, data):
        stats = {
            'strength': data.get('strength', 0),
            'agility': data.get('agility', 0),
            'stamina': data.get('stamina', 0),
            'endurance': data.get('endurance', 0),
        }

        total_stats = sum(stats.values())
        errors = {}

        if total_stats != 20:
            errors['non_field_errors'] = ["Sum of all stats must be 20."]

        for stat, value in stats.items():
            if value < 2:
                errors[stat] = ["Minimum stat value is 2."]

        if errors:
            raise serializers.ValidationError(errors)

        return data

