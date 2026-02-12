from django.contrib import admin
from django.utils.html import format_html

from ..models import Question
from ..utils.constants import DIFFICULTY_ALIAS_MAP, DIFFICULTY_NAME_MAP
from .inlines import AnswerInline


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "question_preview",
        "topic_display",
        "difficulty_display",
        "answer_count",
        "created_at",
    ]

    list_filter = [
        "difficulty_level",
        "created_at",
        "session__initial_difficulty",
        "session__topic",
    ]

    search_fields = [
        "question_text",
        "correct_answer",
        "wrong_answer_1",
        "wrong_answer_2",
        "wrong_answer_3",
        "explanation",
        "session__topic",
        "session__user__email",
    ]

    readonly_fields = [
        "session",
        "question_text_display",
        "all_answers_display",
        "explanation_display",
        "difficulty_level",
        "created_at",
    ]

    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    list_per_page = 25

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("answers")

    inlines = [AnswerInline]

    fieldsets = (
        ("Session Info", {"fields": ("session",)}),
        ("Question", {"fields": ("question_text_display", "difficulty_level")}),
        (
            "All Answers",
            {
                "fields": ("all_answers_display",),
                "description": "All answers with correct answer marked in green",
            },
        ),
        ("Explanation", {"fields": ("explanation_display",)}),
        ("Metadata", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def question_preview(self, obj):
        text = obj.question_text
        if len(text) > 60:
            return text[:60] + "..."
        return text

    question_preview.short_description = "Question"

    def question_text_display(self, obj):
        return format_html(
            '<div style="padding: 10px; background-color: #f3f4f6; '
            'border-left: 4px solid #3b82f6; border-radius: 4px; font-size: 14px;">'
            "<strong>Question:</strong><br>{}"
            "</div>",
            obj.question_text,
        )

    question_text_display.short_description = "Question Text"

    def all_answers_display(self, obj):
        answers = [
            ("A", obj.correct_answer, True),
            ("B", obj.wrong_answer_1, False),
            ("C", obj.wrong_answer_2, False),
            ("D", obj.wrong_answer_3, False),
        ]

        html_parts = []
        html_parts.append('<div style="margin-top: 10px;">')

        for letter, answer, is_correct in answers:
            if is_correct:
                style = (
                    "padding: 10px; margin: 5px 0; background-color: #d1fae5; "
                    "border: 2px solid #10b981; border-radius: 4px; font-size: 14px;"
                )
                label = "CORRECT"
                label_color = "#10b981"
            else:
                style = (
                    "padding: 10px; margin: 5px 0; background-color: #fee2e2; "
                    "border: 1px solid #fecaca; border-radius: 4px; font-size: 14px;"
                )
                label = "WRONG"
                label_color = "#ef4444"

            html_parts.append(
                f'<div style="{style}">'
                f'<span style="font-weight: bold; color: {label_color};">{label}</span> '
                f"<strong>{letter}:</strong> {answer}"
                "</div>"
            )

        html_parts.append("</div>")
        return format_html("".join(html_parts))

    all_answers_display.short_description = "All Answers (Correct Answer Highlighted)"

    def explanation_display(self, obj):
        return format_html(
            '<div style="padding: 10px; background-color: #fef3c7; '
            'border-left: 4px solid #f59e0b; border-radius: 4px; font-size: 14px;">'
            "<strong>Explanation:</strong><br>{}"
            "</div>",
            obj.explanation,
        )

    explanation_display.short_description = "Explanation"

    def topic_display(self, obj):
        if obj.session:
            topic = obj.session.topic
            return format_html(
                '<a href="/admin/quiz_app/quizsession/{}/change/" title="{}">{}</a>',
                obj.session.id,
                topic,
                topic[:30] + "..." if len(topic) > 30 else topic,
            )
        topic = obj.topic or "Brak"
        return topic[:30] + "..." if len(topic) > 30 else topic

    topic_display.short_description = "Topic"
    topic_display.admin_order_field = "topic"

    def difficulty_display(self, obj):
        level_raw = (obj.difficulty_level or "").strip().lower()
        normalized = DIFFICULTY_ALIAS_MAP.get(level_raw, level_raw)
        fallback = DIFFICULTY_NAME_MAP.get("medium", "medium")
        label = DIFFICULTY_NAME_MAP.get(normalized, level_raw or fallback)
        label = label[:1].upper() + label[1:] if label else label
        colors = {
            "easy": "#10b981",
            "medium": "#f59e0b",
            "hard": "#ef4444",
        }
        color = colors.get(normalized, "#6b7280")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            label,
        )

    difficulty_display.short_description = "Difficulty"
    difficulty_display.admin_order_field = "difficulty_level"

    def answer_count(self, obj):
        count = obj.answers.count()
        if count == 0:
            return format_html('<span style="color: #9ca3af;">0 answers</span>')

        correct_count = obj.answers.filter(is_correct=True).count()
        wrong_count = count - correct_count

        return format_html(
            '<span style="color: #10b981;">Correct: {}</span> / '
            '<span style="color: #ef4444;">Wrong: {}</span>',
            correct_count,
            wrong_count,
        )

    answer_count.short_description = "User Answers"

    def has_add_permission(self, request):
        return False
