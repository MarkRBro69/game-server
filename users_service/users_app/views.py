import logging

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from users_app.models import CustomUserModel, CharacterModel
from users_app.serializers import CustomUserSerializer, CharacterSerializer
from users_app.services import UserService, CharacterService
from users_app.utils import get_auth_user

logger = logging.getLogger('game_server')


@api_view(['POST'])
def register_user(request):
    """
    API endpoint for user registration.

    Args:
        request (Request): The incoming HTTP request containing user data.

    Returns:
        Response: JSON response with success or error messages and appropriate HTTP status code.
    """

    logger.info('Register request received')

    # Extract user data from the request
    user_data = request.data
    logger.debug(f'Received data: {user_data}')

    try:
        # Call UserService to create a new user
        user = UserService.create_user(user_data)
        logger.info(f'User created successfully with ID {user.id}')

        # Prepare success response
        data = {'message': 'Registration successful', 'user_id': user.id}
        logger.debug(f'Response data: {data}')
        return Response(data=data, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        # Handle validation errors
        data = {'errors': e}
        logger.warning(f'Validation error during registration: {e}')
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        # Handle unexpected errors
        data = {'errors': 'An unexpected error occurred. Please try again later.'}
        logger.exception(f'Unexpected error occurred: {e}')
        return Response(data=data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        tokens = RefreshToken.for_user(user)
        data = {
            'access': str(tokens.access_token),
            'refresh': str(tokens),
            'user': CustomUserSerializer(user).data,
        }

        response = Response(data=data, status=status.HTTP_200_OK)

        response.set_cookie(
            key='uat',
            value=str(tokens.access_token),
            max_age=900,
            secure=True,
            httponly=True,
            samesite='None',
        )
        response.set_cookie(
            key='urt',
            value=str(tokens),
            max_age=3600 * 24,
            secure=True,
            httponly=True,
            samesite='None',
        )

        return response

    return Response(data={'error': 'an error'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def get_user(request):
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
        data = {
            'access': uat,
            'refresh': urt,
            'user': serialized_user.data,
        }
        return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
def delete_user(request, username):
    user = get_object_or_404(CustomUserModel, username=username)
    data = {'user deleted': user.id}
    user.delete()
    return Response(data=data, status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
def add_win(request):
    username = request.data.get('username')
    user = get_object_or_404(CustomUserModel, username=username)
    user.wins += 1
    user.save(update_fields=['wins'])
    data = {'wins updated': user.id}
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def add_loss(request):
    username = request.data.get('username')
    user = get_object_or_404(CustomUserModel, username=username)
    user.losses += 1
    user.save(update_fields=['losses'])
    data = {'losses updated': user.id}
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def add_draw(request):
    username = request.data.get('username')
    user = get_object_or_404(CustomUserModel, username=username)
    user.draws += 1
    user.save(update_fields=['draws'])
    data = {'draws updated': user.id}
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def change_rating(request):
    username = request.data.get('username')
    rating = request.data.get('rating')
    user = get_object_or_404(CustomUserModel, username=username)
    user.rating += rating
    user.save(update_fields=['rating'])
    data = {'rating updated': user.id}
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_rating(request):
    users = CustomUserModel.objects.all().order_by('-rating')
    serialized_users = CustomUserSerializer(users, many=True)
    data = {
        'users': serialized_users.data,
    }
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_profile(request):
    username = request.data.get('username')
    user = get_object_or_404(CustomUserModel, username=username)
    serialized_users = CustomUserSerializer(user, many=False)
    data = {
        'profile': serialized_users.data,
    }
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['POST'])
@get_auth_user
def create_character(request, user):
    serialized_character = CharacterSerializer(data=request.data)
    if serialized_character.is_valid():
        username = user.get('username')
        user = get_object_or_404(CustomUserModel, username=username)
        serialized_character.validated_data['owner'] = user
        serialized_character.save()
        return Response(serialized_character.data, status=status.HTTP_201_CREATED)
    return Response(serialized_character.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_character(request, character_name):
    character = get_object_or_404(CharacterModel, name=character_name)
    character.delete()
    data = {
        'message': f'Character: {character_name}, deleted.'
    }
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def update_character(request):
    serialized_character = CharacterSerializer(data=request.data)
    if serialized_character.is_valid():
        serialized_character.save()
        return Response(serialized_character.data, status=status.HTTP_201_CREATED)
    return Response(serialized_character.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_user_characters(request, username):
    characters_query = CharacterService.get_user_characters(username)
    serialized_characters = CharacterSerializer(characters_query, many=True)
    return Response(serialized_characters.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@get_auth_user
def get_user_char_by_name(request, char_name, user=None):
    character = UserService.get_character_by_name(user.get('username'), char_name)
    serialized_char = CharacterSerializer(character)
    response = Response(serialized_char.data, status=status.HTTP_200_OK)
    return response
