from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, F
from .models import QuizSession, Question, QuizSessionQuestion, Answer


class QuizSessionQuestionInline(admin.TabularInline):
    model = QuizSessionQuestion
    extra = 0
    readonly_fields = ['question', 'order', 'shown_at', 'answered_at']
    fields = ['question', 'order', 'shown_at', 'answered_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class AccuracyFilter(admin.SimpleListFilter):
    title = 'poziom accuracy'
    parameter_name = 'accuracy'

    def lookups(self, request, model_admin):
        return (
            ('high', 'Wysoki (80-100%)'),
            ('medium', 'Średni (50-79%)'),
            ('low', 'Niski (0-49%)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(
                total_questions__gt=0,
                correct_answers__gte=0.8 * F('total_questions')
            )
        elif self.value() == 'medium':
            return queryset.filter(
                total_questions__gt=0,
                correct_answers__gte=0.5 * F('total_questions'),
                correct_answers__lt=0.8 * F('total_questions')
            )
        elif self.value() == 'low':
            return queryset.filter(
                total_questions__gt=0,
                correct_answers__lt=0.5 * F('total_questions')
            )


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user_display',
        'topic',
        'subtopic',
        'knowledge_level',
        'difficulty_badge',
        'score_display',
        'accuracy_badge',
        'status_badge',
        'started_at'
    ]

    list_filter = [
        'is_completed',
        'initial_difficulty',
        'knowledge_level',
        AccuracyFilter,
        'started_at'
    ]

    search_fields = [
        'user__email',
        'user__username',
        'topic',
        'subtopic'
    ]

    readonly_fields = [
        'started_at',
        'ended_at',
        'completed_at',
        'accuracy',
        'total_questions',
        'correct_answers'
    ]

    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('user', 'topic', 'subtopic', 'knowledge_level')
        }),
        ('Konfiguracja', {
            'fields': (
                'initial_difficulty',
                'current_difficulty',
                'questions_count',
                'time_per_question',
                'use_adaptive_difficulty'
            )
        }),
        ('Status i wyniki', {
            'fields': (
                'is_completed',
                'total_questions',
                'correct_answers',
                'accuracy',
                'current_streak',
                'best_streak'
            )
        }),
        ('Daty', {
            'fields': ('started_at', 'ended_at', 'completed_at')
        }),
    )

    inlines = [QuizSessionQuestionInline]

    def user_display(self, obj):
        return obj.user.username

    user_display.short_description = 'Użytkownik'

    def difficulty_badge(self, obj):
        colors = {
            'easy': '#28a745',
            'medium': '#ffc107',
            'hard': '#dc3545'
        }
        color = colors.get(obj.initial_difficulty, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.initial_difficulty.upper()
        )

    difficulty_badge.short_description = 'Trudność'

    def score_display(self, obj):
        return f"{obj.correct_answers}/{obj.total_questions}"

    score_display.short_description = 'Wynik'

    def accuracy_badge(self, obj):
        accuracy = obj.accuracy
        if accuracy >= 80:
            color = '#28a745'
        elif accuracy >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{:.1f}%</span>',
            color,
            accuracy
        )

    accuracy_badge.short_description = 'Accuracy'

    def status_badge(self, obj):
        if obj.is_completed:
            color = '#28a745'
            text = 'Ukończony'
        else:
            color = '#007bff'
            text = 'W trakcie'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            text
        )

    status_badge.short_description = 'Status'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'topic',
        'subtopic',
        'knowledge_level',
        'question_preview',
        'difficulty_badge',
        'usage_stats',
        'success_rate_display',
        'created_at'
    ]

    list_filter = [
        'difficulty_level',
        'knowledge_level',
        'topic',
        'created_at'
    ]

    search_fields = [
        'topic',
        'subtopic',
        'question_text',
        'correct_answer'
    ]

    readonly_fields = [
        'content_hash',
        'times_used',
        'times_correct',
        'success_rate',
        'created_at',
        'updated_at',
        'created_by'
    ]

    fieldsets = (
        ('Klasyfikacja', {
            'fields': ('topic', 'subtopic', 'knowledge_level', 'difficulty_level')
        }),
        ('Treść pytania', {
            'fields': ('question_text', 'explanation')
        }),
        ('Odpowiedzi', {
            'fields': (
                'correct_answer',
                'wrong_answer_1',
                'wrong_answer_2',
                'wrong_answer_3'
            )
        }),
        ('Statystyki', {
            'fields': ('times_used', 'times_correct', 'success_rate')
        }),
        ('Metadata', {
            'fields': ('content_hash', 'embedding_vector', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def question_preview(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text

    question_preview.short_description = 'Pytanie'

    def difficulty_badge(self, obj):
        colors = {
            'easy': '#28a745',
            'medium': '#ffc107',
            'hard': '#dc3545'
        }
        labels = {
            'easy': 'Łatwy',
            'medium': 'Średni',
            'hard': 'Trudny'
        }
        color = colors.get(obj.difficulty_level, '#6c757d')
        label = labels.get(obj.difficulty_level, obj.difficulty_level)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            label
        )

    difficulty_badge.short_description = 'Trudność'

    def usage_stats(self, obj):
        return f"{obj.times_used}× ({obj.times_correct} ✓)"

    usage_stats.short_description = 'Użycia'

    def success_rate_display(self, obj):
        rate = obj.success_rate
        if rate >= 70:
            color = '#28a745'
        elif rate >= 40:
            color = '#ffc107'
        else:
            color = '#dc3545'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{:.1f}%</span>',
            color,
            rate
        )

    success_rate_display.short_description = 'Skuteczność'


@admin.register(QuizSessionQuestion)
class QuizSessionQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'question_preview', 'order', 'shown_at', 'answered_at']
    list_filter = ['shown_at', 'answered_at']
    search_fields = ['session__topic', 'question__question_text']
    readonly_fields = ['shown_at', 'answered_at']

    def question_preview(self, obj):
        text = obj.question.question_text
        return text[:60] + '...' if len(text) > 60 else text

    question_preview.short_description = 'Pytanie'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'session_display',
        'question_preview',
        'selected_answer',
        'correctness_badge',
        'response_time',
        'answered_at'
    ]

    list_filter = [
        'is_correct',
        'answered_at'
    ]

    search_fields = [
        'session_question__session__topic',
        'session_question__question__question_text',
        'selected_answer'
    ]

    readonly_fields = ['answered_at']

    def session_display(self, obj):
        return f"Session {obj.session_question.session.id}"

    session_display.short_description = 'Sesja'

    def question_preview(self, obj):
        text = obj.session_question.question.question_text
        return text[:50] + '...' if len(text) > 50 else text

    question_preview.short_description = 'Pytanie'

    def correctness_badge(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Poprawna</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Błędna</span>'
            )

    correctness_badge.short_description = 'Poprawność'