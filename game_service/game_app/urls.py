from django.urls import path

from game_app.views import start_search

urlpatterns = {
    path('start_search/<str:username>', start_search, name='start_search'),
}
