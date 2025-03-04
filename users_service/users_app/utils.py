import logging
import environ

from django.http import JsonResponse

from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from users_app.models import CustomUserModel, CharacterModel
from users_app.serializers import CustomUserSerializer


logger = logging.getLogger('game_server')
env = environ.Env()


def get_auth_user(func):
    def wrapper(*args, **kwargs):
        request = args[0]

        response = None
        token_is_valid = False

        access = request.data.get('access')
        refresh = request.data.get('refresh')

        logger.debug(f'Access: {access}')
        logger.debug(f'Refresh: {refresh}')

        if access is None:
            access = request.COOKIES.get('uat')
            logger.debug(f'Access: {access}')

        if refresh is None:
            refresh = request.COOKIES.get('urt')
            logger.debug(f'Refresh: {refresh}')

        uat = None
        urt = None
        user = None

        if access:
            try:
                user_data = AccessToken(access)
                user = get_object_or_404(CustomUserModel, pk=user_data.get('user_id'))
                token_is_valid = True

            except TokenError:
                token_is_valid = False

        if not token_is_valid and refresh:
            user_data = RefreshToken(refresh)
            user = get_object_or_404(CustomUserModel, pk=user_data.get('user_id'))
            new_refresh = RefreshToken.for_user(user)
            uat = str(new_refresh.access_token)
            urt = str(new_refresh)

        if user:
            serialized_user = CustomUserSerializer(user, many=False)
            response = func(*args, **kwargs, user=serialized_user.data)

        if uat:
            response.set_cookie(
                key='uat',
                value=uat,
                max_age=900,
                secure=True,
                httponly=True,
                samesite='None',
            )

        if urt:
            response.set_cookie(
                key='urt',
                value=urt,
                max_age=3600 * 24,
                secure=True,
                httponly=True,
                samesite='None',
            )

        return response
    return wrapper


def auth_service(func):
    def wrapper(*args, **kwargs):
        request = args[0]
        headers = request.headers
        service_key = headers.get('Service-Key')

        if service_key == env.str('USERS_SERVICE_KEY'):
            return func(*args, **kwargs)
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

    return wrapper


def calc_experience(character: CharacterModel, experience_to_add: int) -> (int, bool):
    gain_level = False
    level = int(character.level)
    experience = int(character.experience)
    current_experience = experience + experience_to_add
    next_level_experience = (level * (level + 1) * 100) / 2
    if current_experience >= next_level_experience:
        gain_level = True

    return current_experience, gain_level
