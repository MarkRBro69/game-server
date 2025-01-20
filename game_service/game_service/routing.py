from django.urls import path

from game_service.consumers.chat_consumer import GlobalConsumer
from game_service.consumers.game_consumer import GameConsumer

websocket_urlpatterns = [
    path('ws/global/<str:username>/', GlobalConsumer.as_asgi()),
    path('ws/game/<str:room_token>/<str:username>/', GameConsumer.as_asgi()),
]
