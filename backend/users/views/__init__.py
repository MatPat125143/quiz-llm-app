from .auth import request_password_reset, verify_reset_code, reset_password_with_code
from .profile import get_current_user, update_profile, change_password, upload_avatar, delete_avatar
from .admin import (
    admin_dashboard,
    all_users,
    search_users,
    user_quiz_history,
    delete_quiz_session,
    delete_user,
    toggle_user_status,
    change_user_role
)

__all__ = [
    # Auth
    'request_password_reset',
    'verify_reset_code',
    'reset_password_with_code',
    # Profile
    'get_current_user',
    'update_profile',
    'change_password',
    'upload_avatar',
    'delete_avatar',
    # Admin
    'admin_dashboard',
    'all_users',
    'search_users',
    'user_quiz_history',
    'delete_quiz_session',
    'delete_user',
    'toggle_user_status',
    'change_user_role'
]