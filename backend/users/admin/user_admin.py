from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .inlines import UserProfileInline

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "get_role", "is_staff", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_superuser", "is_active", "profile__role"]
    search_fields = ["email", "username"]
    ordering = ["-date_joined"]
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )

    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, "profile") else "N/A"

    get_role.short_description = "Role"
    get_role.admin_order_field = "profile__role"
