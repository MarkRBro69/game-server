from django.urls import path

from frontend_app.views import *

urlpatterns = [
    path('', home, name='home'),
    path('registration/', registration, name='registration'),
]
