from django.contrib import admin

from ..models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    readonly_fields = [
        "total_quizzes_played",
        "total_questions_answered",
        "total_correct_answers",
        "highest_streak",
        "accuracy",
        "created_at",
        "updated_at",
    ]
