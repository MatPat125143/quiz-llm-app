from .profile import get_current_user, update_profile, change_password
from .avatar import upload_avatar, delete_avatar
from .auth import request_password_reset, verify_reset_code, reset_password_with_code
from .admin import (
    admin_dashboard,
    all_users,
    search_users,
    user_quiz_history,
    delete_user,
    toggle_user_status,
    change_user_role,
    delete_quiz_session,
)

__all__ = [
    'get_current_user',
    'update_profile',
    'change_password',
    'upload_avatar',
    'delete_avatar',
    'request_password_reset',
    'verify_reset_code',
    'reset_password_with_code',
    'admin_dashboard',
    'all_users',
    'search_users',
    'user_quiz_history',
    'delete_user',
    'toggle_user_status',
    'change_user_role',
    'delete_quiz_session',
]