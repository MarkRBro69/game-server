from django.urls import path

from users_app.views import register_user

urlpatterns = [
    path('register_user/', register_user, name='register_user')
]
