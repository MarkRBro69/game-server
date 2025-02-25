from django.urls import path

from frontend_app.views import *

urlpatterns = [
    path('', home, name='home'),
    path('registration/', registration, name='registration'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('desktop/', desktop, name='desktop'),
    path('rating/', rating, name='rating'),
    path('profile/<str:username>/', profile, name='profile'),

    path('create_character', create_character, name='create_character'),

    path('global_lobby/', global_lobby, name='global_lobby'),
    path('game_lobby/<str:room_token>/', game_lobby, name='game_lobby'),
]
