from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.utils import timezone

from ..models import PasswordResetToken


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user_email", "code", "created_at", "expires_at", "used", "is_valid_display"]
    list_filter = ["used", "created_at"]
    search_fields = ["user__email", "code"]
    readonly_fields = ["user", "code", "created_at", "expires_at", "time_remaining"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Token Info", {"fields": ("user", "code", "used")}),
        ("Timing", {"fields": ("created_at", "expires_at", "time_remaining")}),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def expires_at(self, obj):
        timeout = getattr(settings, "PASSWORD_RESET_TIMEOUT", 3600)
        expiry = obj.created_at + timedelta(seconds=timeout)
        return expiry.strftime("%Y-%m-%d %H:%M:%S")

    expires_at.short_description = "Expires At"

    def time_remaining(self, obj):
        if obj.used:
            return "Used"

        timeout = getattr(settings, "PASSWORD_RESET_TIMEOUT", 3600)
        expiry = obj.created_at + timedelta(seconds=timeout)
        remaining = expiry - timezone.now()

        if remaining.total_seconds() <= 0:
            return "Expired"

        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        return f"{minutes}m {seconds}s remaining"

    time_remaining.short_description = "Time Remaining"

    def is_valid_display(self, obj):
        return "Valid" if obj.is_valid() else "Invalid"

    is_valid_display.short_description = "Status"
    is_valid_display.admin_order_field = "used"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["user", "code", "created_at", "expires_at", "time_remaining"]
        return self.readonly_fields
