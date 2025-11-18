from django.urls import path
from .views import profile, auth, admin

urlpatterns = [
    # ==================== PROFILE ENDPOINTS ====================
    path('me/', profile.get_current_user, name='current-user'),
    path('update/', profile.update_profile, name='update-profile'),
    path('change-password/', profile.change_password, name='change-password'),
    path('avatar/upload/', profile.upload_avatar, name='upload-avatar'),
    path('avatar/delete/', profile.delete_avatar, name='delete-avatar'),

    # ==================== PASSWORD RESET ENDPOINTS ====================
    path('password-reset/request/', auth.request_password_reset, name='request-password-reset'),
    path('password-reset/verify/', auth.verify_reset_code, name='verify-reset-code'),
    path('password-reset/confirm/', auth.reset_password_with_code, name='reset-password-confirm'),

    # ==================== ADMIN ENDPOINTS ====================
    path('admin/dashboard/', admin.admin_dashboard, name='admin-dashboard'),
    path('admin/users/', admin.all_users, name='admin-users'),
    path('admin/users/search/', admin.search_users, name='admin-search-users'),
    path('admin/users/<int:user_id>/quizzes/', admin.user_quiz_history, name='admin-user-quizzes'),
    path('admin/users/<int:user_id>/delete/', admin.delete_user, name='admin-delete-user'),
    path('admin/users/<int:user_id>/role/', admin.change_user_role, name='admin-change-role'),
    path('admin/users/<int:user_id>/toggle/', admin.toggle_user_status, name='admin-toggle-user'),
    path('admin/sessions/<int:session_id>/delete/', admin.delete_quiz_session, name='admin-delete-session'),
]