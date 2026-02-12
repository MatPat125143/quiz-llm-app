from django.contrib import admin
from ..models import Answer, Question


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    can_delete = False
    readonly_fields = ["user", "selected_answer", "is_correct", "response_time", "answered_at"]
    fields = ["user", "selected_answer", "is_correct", "response_time", "answered_at"]

    def has_add_permission(self, request, obj=None):
        return False


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    can_delete = False
    readonly_fields = [
        "question_text",
        "correct_answer",
        "wrong_answer_1",
        "wrong_answer_2",
        "wrong_answer_3",
        "explanation",
        "difficulty_level",
        "created_at",
    ]
    fields = [
        "question_text",
        "correct_answer",
        "wrong_answer_1",
        "wrong_answer_2",
        "wrong_answer_3",
        "explanation",
        "difficulty_level",
        "created_at",
    ]
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False
