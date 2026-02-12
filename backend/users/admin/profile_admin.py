from django.contrib import admin

from ..models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user_email", "role", "total_quizzes_played", "accuracy", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["user__email", "user__username"]
    readonly_fields = [
        "user",
        "total_quizzes_played",
        "total_questions_answered",
        "total_correct_answers",
        "highest_streak",
        "accuracy",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    fieldsets = (
        ("User", {"fields": ("user",)}),
        ("Role & Avatar", {"fields": ("role", "avatar")}),
        (
            "Statistics",
            {
                "fields": (
                    "total_quizzes_played",
                    "total_questions_answered",
                    "total_correct_answers",
                    "highest_streak",
                    "accuracy",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"
