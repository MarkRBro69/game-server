import logging

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from users_app.services import UserService

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
        data = {'message': 'An unexpected error occurred. Please try again later.'}
        logger.exception(f'Unexpected error occurred: {e}')
        return Response(data=data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
