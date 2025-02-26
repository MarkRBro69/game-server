import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from game_app.utils import token_auth, GamesManager


logger = logging.getLogger('game_server')


@api_view(['GET'])
@token_auth
def get_auth_token(request, user=None):
    logger.debug(f'Headers: {request.headers}')
    logger.debug(f'Cookies: {request.COOKIES}')
    token = None
    if user:
        games_manager = GamesManager()
        token = games_manager.generate_token(user.get('username'))
        logger.debug(f'Token: {token}')

    data = {'token': token}
    return Response(data, status=status.HTTP_200_OK)
