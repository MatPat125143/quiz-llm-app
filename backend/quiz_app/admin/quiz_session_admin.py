from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from ..models import QuizSession
from .filters import AccuracyFilter
from .inlines import QuestionInline


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_email",
        "topic_display",
        "difficulty_badge",
        "questions_count",
        "score_display",
        "accuracy_badge",
        "status_badge",
        "started_at",
    ]

    list_filter = [
        "is_completed",
        "initial_difficulty",
        AccuracyFilter,
        "started_at",
    ]

    search_fields = [
        "user__email",
        "user__username",
        "topic",
    ]

    readonly_fields = [
        "user",
        "started_at",
        "ended_at",
        "total_questions",
        "correct_answers",
        "current_streak",
        "accuracy",
        "duration_display",
    ]

    date_hierarchy = "started_at"
    ordering = ["-started_at"]
    inlines = [QuestionInline]

    fieldsets = (
        ("User & Topic", {"fields": ("user", "topic")}),
        ("Difficulty", {"fields": ("initial_difficulty", "current_difficulty")}),
        (
            "Progress & Statistics",
            {
                "fields": ("total_questions", "correct_answers", "current_streak", "accuracy"),
                "classes": ("collapse",),
            },
        ),
        ("Status & Timing", {"fields": ("is_completed", "started_at", "ended_at", "duration_display")}),
    )

    actions = ["mark_as_completed", "export_to_csv"]

    def user_email(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.email,
        )

    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"

    def topic_display(self, obj):
        if len(obj.topic) > 30:
            return obj.topic[:30] + "..."
        return obj.topic

    topic_display.short_description = "Topic"
    topic_display.admin_order_field = "session__topic"

    def difficulty_badge(self, obj):
        colors = {
            "easy": "#10b981",
            "medium": "#f59e0b",
            "hard": "#ef4444",
        }
        color = colors.get(obj.initial_difficulty, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.initial_difficulty.upper(),
        )

    difficulty_badge.short_description = "Difficulty"
    difficulty_badge.admin_order_field = "initial_difficulty"

    def questions_count(self, obj):
        return obj.total_questions

    questions_count.short_description = "Questions"
    questions_count.admin_order_field = "total_questions"

    def score_display(self, obj):
        return f"{obj.correct_answers}/{obj.total_questions}"

    score_display.short_description = "Score"

    def accuracy_badge(self, obj):
        accuracy = obj.accuracy
        if accuracy >= 80:
            color = "#10b981"
        elif accuracy >= 50:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            f"{accuracy :.1f}",
        )

    accuracy_badge.short_description = "Accuracy"
    accuracy_badge.admin_order_field = "correct_answers"

    def status_badge(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: #10b981;">Completed</span>')
        return format_html('<span style="color: #f59e0b;">In Progress</span>')

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "is_completed"

    def duration_display(self, obj):
        if obj.ended_at and obj.started_at:
            duration = obj.ended_at - obj.started_at
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            return f"{minutes}m {seconds}s"
        return "In progress"

    duration_display.short_description = "Duration"

    def mark_as_completed(self, request, queryset):
        count = 0
        for session in queryset:
            if not session.is_completed:
                session.is_completed = True
                if not session.ended_at:
                    session.ended_at = timezone.now()
                session.save()
                count += 1
        self.message_user(request, f"{count} quiz(zes) marked as completed.")

    mark_as_completed.short_description = "Mark selected as completed"

    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="quiz_sessions.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ["ID", "User", "Topic", "Difficulty", "Questions", "Correct", "Accuracy", "Status", "Started"]
        )

        for session in queryset:
            writer.writerow(
                [
                    session.id,
                    session.user.email,
                    session.topic,
                    session.initial_difficulty,
                    session.total_questions,
                    session.correct_answers,
                    f"{session.accuracy}%",
                    "Completed" if session.is_completed else "In Progress",
                    session.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return response

    export_to_csv.short_description = "Export selected to CSV"
