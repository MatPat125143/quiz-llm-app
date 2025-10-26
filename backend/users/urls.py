from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.get_current_user, name='current-user'),
    path('update/', views.update_profile, name='update-profile'),
    path('change-password/', views.change_password, name='change-password'),
    path('avatar/upload/', views.upload_avatar, name='upload-avatar'),
    path('avatar/delete/', views.delete_avatar, name='delete-avatar'),

    # Password Reset
    path('password-reset/request/', views.request_password_reset, name='request-password-reset'),
    path('password-reset/verify/', views.verify_reset_code, name='verify-reset-code'),
    path('password-reset/confirm/', views.reset_password_with_code, name='reset-password-confirm'),
]