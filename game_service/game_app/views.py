from rest_framework import status
from rest_framework.response import Response

from game_app.utils import RedisServer


def start_search(request, username):
    r = RedisServer()
    r.add_search(username)
    data = {
        'message': f'searching for {username}'
    }
    return Response(data=data, status=status.HTTP_200_OK)