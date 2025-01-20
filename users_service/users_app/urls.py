from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users_app.views import *

urlpatterns = [
    path('register_user/', register_user, name='register_user'),
    path('login/', login, name='login'),

    path('delete/<str:username>', delete_user, name='delete_user'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
