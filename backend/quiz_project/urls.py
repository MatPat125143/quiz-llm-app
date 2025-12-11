from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import Group

# Bezpieczne wyrejestrowanie Group (tylko jeśli jest zarejestrowany)
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/users/', include('users.urls')),
    path('api/quiz/', include('quiz_app.urls')),
]

# Dodaj obsługę media files (avatary)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)