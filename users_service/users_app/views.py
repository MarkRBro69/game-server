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
from users_app.utils import get_auth_user, auth_service, calc_experience

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
    """
    Authenticates a user and returns JWT tokens in both the response body and cookies.

    This view expects a JSON request body containing 'username' and 'password'.
    If authentication is successful, it returns:
    - An access token and a refresh token in the response body.
    - The same tokens as HTTP-only cookies for enhanced security.

    The access token ('uat') expires in 15 minutes, while the refresh token ('urt') expires in 24 hours.

    Args:
        request (Request): The HTTP request containing user credentials.

    Returns:
        Response: JSON response with JWT tokens and user data if authentication is successful.
                  Tokens are also set in HTTP-only cookies.
                  If authentication fails, returns an error response with status 400.
    """
    # Extracting username and password from request data
    username = request.data.get('username')
    password = request.data.get('password')

    # Authenticating user
    user = authenticate(username=username, password=password)

    if user:
        # Generating JWT tokens
        tokens = RefreshToken.for_user(user)
        data = {
            'access': str(tokens.access_token),  # Access token for authentication
            'refresh': str(tokens),  # Refresh token for obtaining new access tokens
            'user': CustomUserSerializer(user).data,  # Serialized user data
        }

        # Creating response with tokens and user data
        response = Response(data=data, status=status.HTTP_200_OK)

        # Setting HTTP-only cookies for tokens
        response.set_cookie(
            key='uat',  # Access token cookie
            value=str(tokens.access_token),
            max_age=900,  # 15 minutes expiration
            secure=True,  # Secure cookie (HTTPS required)
            httponly=True,  # JavaScript cannot access this cookie
            samesite='None',  # Cross-site requests allowed
        )
        response.set_cookie(
            key='urt',  # Refresh token cookie
            value=str(tokens),
            max_age=3600 * 24,  # 24 hours expiration
            secure=True,
            httponly=True,
            samesite='None',
        )

        return response

    # Returning an error response if authentication fails
    return Response(data={'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def get_user(request):
    """
    Retrieves user information based on JWT tokens (access or refresh).

    This view checks for a valid access token in the request body or cookies.
    If the access token is invalid or missing, it attempts to refresh the session
    using the refresh token. If successful, new tokens are issued.

    Workflow:
    - Checks for `access` and `refresh` tokens in request data.
    - If not found, attempts to retrieve them from cookies.
    - If the access token is valid, fetches user information.
    - If the access token is invalid but a refresh token is present,
      generates new tokens and returns updated credentials.
    - Returns user data along with new tokens if needed.

    Args:
        request (Request): The HTTP request containing tokens.

    Returns:
        Response: JSON response containing user data and optionally new tokens.
    """

    token_is_valid = False

    # Extract access and refresh tokens from request data
    access = request.data.get('access')
    refresh = request.data.get('refresh')

    logger.debug(f'Access: {access}')
    logger.debug(f'Refresh: {refresh}')

    # If tokens are missing in the request body, retrieve them from cookies
    if access is None:
        access = request.COOKIES.get('uat')
        logger.debug(f'Access (from cookies): {access}')

    if refresh is None:
        refresh = request.COOKIES.get('urt')
        logger.debug(f'Refresh (from cookies): {refresh}')

    uat = None  # New access token (if refreshed)
    urt = None  # New refresh token (if refreshed)
    user = None

    # Validate access token if available
    if access:
        try:
            user_data = AccessToken(access)
            user = get_object_or_404(CustomUserModel, pk=user_data.get('user_id'))
            token_is_valid = True
        except TokenError:
            token_is_valid = False  # Access token is invalid

    # If access token is invalid, try using the refresh token
    if not token_is_valid and refresh:
        try:
            user_data = RefreshToken(refresh)
            user = get_object_or_404(CustomUserModel, pk=user_data.get('user_id'))

            # Generate new tokens
            new_refresh = RefreshToken.for_user(user)
            uat = str(new_refresh.access_token)
            urt = str(new_refresh)
        except TokenError:
            return Response(data={'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)

    # If user is successfully authenticated, return their data
    if user:
        serialized_user = CustomUserSerializer(user, many=False)
        data = {
            'access': uat,  # New access token if refreshed
            'refresh': urt,  # New refresh token if refreshed
            'user': serialized_user.data,  # User information
        }
        logger.debug(f'User: {serialized_user.data}')
        return Response(data=data, status=status.HTTP_200_OK)

    # If authentication fails completely, return an error response
    return Response(data={'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)


# TODO Remake this view
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
    logger.debug(f'Username: {username}, Rating: {rating}')
    user = get_object_or_404(CustomUserModel, username=username)
    user.rating += int(rating)
    user.save(update_fields=['rating'])
    data = {'rating updated': user.id}
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def update_char_experience(request):
    charname = request.data.get('charname')
    experience = request.data.get('experience')
    logger.debug(f'Charname: {charname}, Experience: {experience}')
    character = get_object_or_404(CharacterModel, name=charname)

    new_exp, level_gain = calc_experience(character, int(experience))
    character.experience = new_exp

    if level_gain:
        character.level += 1
        character.unused_points += 5

    character.save(update_fields=['experience', 'level', 'unused_points'])
    data = {'updated_character': character}
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
    username = request.query_params.get('username')
    logger.debug(f'Username: {username}')
    user = get_object_or_404(CustomUserModel, username=username)
    serialized_users = CustomUserSerializer(user, many=False)
    data = {
        'profile': serialized_users.data,
    }
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['POST'])
@get_auth_user
def create_character(request, user=None):
    serialized_character = CharacterSerializer(data=request.data)
    if serialized_character.is_valid():
        username = user.get('username')
        user = get_object_or_404(CustomUserModel, username=username)
        serialized_character.validated_data['owner'] = user
        serialized_character.save()
        return Response(serialized_character.data, status=status.HTTP_201_CREATED)
    return Response(serialized_character.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@get_auth_user
def add_point(request, charname, stat, user=None):
    username = user.get('username')
    logger.debug(f'Username: {username}')
    user = get_object_or_404(CustomUserModel, username=username)

    character = CharacterModel.objects.filter(name=charname, owner=user).first()

    if not character:
        return Response(data={'message': 'Character not found or you do not have permission to modify it.'},
                        status=status.HTTP_403_FORBIDDEN)

    if character.unused_points == 0:
        return Response(data={'message': 'Do not have enough points'}, status=status.HTTP_400_BAD_REQUEST)

    stat_to_update = getattr(character, stat)
    updated_value = stat_to_update + 1
    setattr(character, stat, updated_value)

    character.unused_points -= 1
    character.save(update_fields=[stat, 'unused_points'])
    serialized_character = CharacterSerializer(character)

    return Response(data={'character': serialized_character.data}, status=status.HTTP_200_OK)


# TODO Remake this view
@api_view(['DELETE'])
# @auth_service
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
