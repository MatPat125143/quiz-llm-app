from django.contrib import admin
from django.utils.html import format_html

from ..models import Answer


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_email",
        "question_preview",
        "selected_answer_display",
        "correctness_badge",
        "response_time_display",
        "answered_at",
    ]

    list_filter = [
        "is_correct",
        "answered_at",
    ]

    search_fields = [
        "user__email",
        "user__username",
        "question__question_text",
        "selected_answer",
    ]

    readonly_fields = [
        "question",
        "user",
        "selected_answer",
        "is_correct",
        "response_time",
        "answered_at",
    ]

    date_hierarchy = "answered_at"
    ordering = ["-answered_at"]

    fieldsets = (
        ("User & Question", {"fields": ("user", "question")}),
        ("Answer Details", {"fields": ("selected_answer", "is_correct")}),
        ("Timing", {"fields": ("response_time", "answered_at")}),
    )

    def user_email(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.email,
        )

    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"

    def question_preview(self, obj):
        text = obj.question.question_text
        if len(text) > 40:
            return format_html(
                '<a href="/admin/quiz_app/question/{}/change/">{}</a>',
                obj.question.id,
                text[:40] + "...",
            )
        return format_html(
            '<a href="/admin/quiz_app/question/{}/change/">{}</a>',
            obj.question.id,
            text,
        )

    question_preview.short_description = "Question"

    def selected_answer_display(self, obj):
        answer = obj.selected_answer
        if len(answer) > 30:
            return answer[:30] + "..."
        return answer

    selected_answer_display.short_description = "Selected Answer"

    def correctness_badge(self, obj):
        if obj.is_correct:
            return format_html('<span style="color: #10b981; font-weight: bold;">Correct</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">Wrong</span>')

    correctness_badge.short_description = "Correctness"
    correctness_badge.admin_order_field = "is_correct"

    def response_time_display(self, obj):
        seconds = obj.response_time
        if seconds < 10:
            color = "#10b981"
        elif seconds < 20:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        return format_html(
            '<span style="color: {};">{}s</span>',
            color,
            f"{seconds :.1f}",
        )

    response_time_display.short_description = "Response Time"
    response_time_display.admin_order_field = "response_time"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
