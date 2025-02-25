from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users_app.views import *

urlpatterns = [
    path('register_user/', register_user, name='register_user'),
    path('login/', login, name='login'),
    path('get_user/', get_user, name='get_user'),

    path('delete/<str:username>', delete_user, name='delete_user'),

    path('add_win/', add_win, name='add_win'),
    path('add_loss/', add_loss, name='add_loss'),
    path('add_draw/', add_draw, name='add_draw'),
    path('change_rating/', change_rating, name='change_rating'),
    path('get_rating/', get_rating, name='get_rating'),
    path('get_profile/', get_profile, name='get_profile'),

    path('create_character/', create_character, name='create_character'),
    path('delete_character/<str:character_name>', delete_character, name='delete_character'),
    path('update_character/', update_character, name='update_character'),
    path('get_user_characters/<str:username>', get_user_characters, name='get_user_characters'),
    path('get_user_char_by_name/<str:char_name>', get_user_char_by_name, name='get_user_char_by_name'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
