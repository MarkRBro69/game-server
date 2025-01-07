from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('usr/admin/', admin.site.urls),
    path('usr/api/v1/', include('users_app.urls'))
]
