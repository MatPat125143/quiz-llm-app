from django.urls import path
from .views import (
    get_current_user,
    update_profile,
    change_password,
    upload_avatar,
    delete_avatar,
    request_password_reset,
    verify_reset_code,
    reset_password_with_code,
    admin_dashboard,
    all_users,
    search_users,
    user_quiz_history,
    delete_user,
    toggle_user_status,
    change_user_role,
    delete_quiz_session,
)

urlpatterns = [
    path('me/', get_current_user, name='current-user'),
    path('update/', update_profile, name='update-profile'),
    path('change-password/', change_password, name='change-password'),

    path('avatar/upload/', upload_avatar, name='upload-avatar'),
    path('avatar/delete/', delete_avatar, name='delete-avatar'),

    path('password-reset/request/', request_password_reset, name='password-reset-request'),
    path('password-reset/verify/', verify_reset_code, name='password-reset-verify'),
    path('password-reset/confirm/', reset_password_with_code, name='password-reset-confirm'),

    path('admin/dashboard/', admin_dashboard, name='admin-dashboard'),
    path('admin/users/', all_users, name='admin-all-users'),
    path('admin/users/search/', search_users, name='admin-search-users'),
    path('admin/users/<int:user_id>/quizzes/', user_quiz_history, name='admin-user-quizzes'),
    path('admin/users/<int:user_id>/delete/', delete_user, name='admin-delete-user'),
    path('admin/users/<int:user_id>/toggle/', toggle_user_status, name='admin-toggle-user'),
    path('admin/users/<int:user_id>/role/', change_user_role, name='admin-change-role'),
    path('admin/sessions/<int:session_id>/delete/', delete_quiz_session, name='admin-delete-session'),
]