from django.contrib import admin
from .models import QuizSession, Question, Answer

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'topic', 'total_questions', 'accuracy', 'started_at']
    list_filter = ['is_completed', 'started_at']
    search_fields = ['user__username', 'topic']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'difficulty_level', 'created_at']
    list_filter = ['difficulty_level', 'created_at']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_correct', 'response_time', 'answered_at']
    list_filter = ['is_correct', 'answered_at']