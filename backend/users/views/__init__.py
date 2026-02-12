from .admin_view import (
    admin_dashboard,
    all_users,
    change_user_role,
    delete_quiz_session,
    delete_user,
    search_users,
    toggle_user_status,
    user_quiz_history,
)
from .auth_view import request_password_reset, reset_password_with_code, verify_reset_code
from .profile_view import (
    change_password,
    delete_avatar,
    delete_my_account,
    get_current_user,
    update_profile,
    update_profile_settings,
    upload_avatar,
)

__all__ = [
    "request_password_reset",
    "verify_reset_code",
    "reset_password_with_code",
    "get_current_user",
    "update_profile",
    "change_password",
    "upload_avatar",
    "delete_avatar",
    "update_profile_settings",
    "delete_my_account",
    "admin_dashboard",
    "all_users",
    "search_users",
    "user_quiz_history",
    "delete_quiz_session",
    "delete_user",
    "toggle_user_status",
    "change_user_role",
]
