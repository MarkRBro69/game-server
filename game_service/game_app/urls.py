from django.urls import path

from game_app.views import get_auth_token

urlpatterns = {
    path('get_auth_token/', get_auth_token, name='get_auth_token')
}
