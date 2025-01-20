from django.urls import path

from frontend_app.views import *

urlpatterns = [
    path('', home, name='home'),
    path('registration/', registration, name='registration'),
    path('login/', login, name='login'),
    path('desktop/', desktop, name='desktop'),

    path('global_lobby/', global_lobby, name='global_lobby'),
    path('game_lobby/<str:room_token>/', game_lobby, name='game_lobby'),
]
