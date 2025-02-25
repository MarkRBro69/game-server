from django.urls import path

from game_app.consumers.chat_consumer import GlobalConsumer
from game_app.consumers.game_consumer import GameConsumer

websocket_urlpatterns = [
    path('ws/global/<str:username>/', GlobalConsumer.as_asgi()),
    path('ws/game/<str:room_token>/<str:username>/<str:char_name>/', GameConsumer.as_asgi()),
]
