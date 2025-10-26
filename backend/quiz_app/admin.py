from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, F
from .models import QuizSession, Question, Answer


# ==================== INLINE ADMINS ====================

class AnswerInline(admin.TabularInline):
    """Inline admin for viewing answers within a question"""
    model = Answer
    extra = 0
    can_delete = False
    readonly_fields = ['user', 'selected_answer', 'is_correct', 'response_time', 'answered_at']
    fields = ['user', 'selected_answer', 'is_correct', 'response_time', 'answered_at']

    def has_add_permission(self, request, obj=None):
        """Prevent manual addition of answers"""
        return False


class QuestionInline(admin.StackedInline):
    """Inline admin for viewing questions within a quiz session"""
    model = Question
    extra = 0
    can_delete = False
    readonly_fields = ['question_text', 'correct_answer', 'wrong_answer_1',
                       'wrong_answer_2', 'wrong_answer_3', 'explanation',
                       'difficulty_level', 'created_at']
    fields = ['question_text', 'correct_answer', 'wrong_answer_1',
              'wrong_answer_2', 'wrong_answer_3', 'explanation',
              'difficulty_level', 'created_at']
    show_change_link = True  # Link to full question detail

    def has_add_permission(self, request, obj=None):
        """Prevent manual addition of questions"""
        return False


# ==================== CUSTOM FILTERS ====================

class AccuracyFilter(admin.SimpleListFilter):
    """Custom filter for quiz accuracy ranges"""
    title = 'accuracy level'
    parameter_name = 'accuracy'

    def lookups(self, request, model_admin):
        return (
            ('high', 'High (80-100%)'),
            ('medium', 'Medium (50-79%)'),
            ('low', 'Low (0-49%)'),
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


# ==================== QUIZ SESSION ADMIN ====================

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    """Enhanced admin for QuizSession model"""

    list_display = [
        'id',
        'user_email',
        'topic_display',
        'difficulty_badge',
        'questions_count',
        'score_display',
        'accuracy_badge',
        'status_badge',
        'started_at'
    ]

    list_filter = [
        'is_completed',
        'initial_difficulty',
        AccuracyFilter,
        'started_at'
    ]

    search_fields = [
        'user__email',
        'user__username',
        'topic'
    ]

    readonly_fields = [
        'user',
        'started_at',
        'ended_at',
        'total_questions',
        'correct_answers',
        'current_streak',
        'accuracy',
        'duration_display'
    ]

    date_hierarchy = 'started_at'

    ordering = ['-started_at']

    inlines = [QuestionInline]

    fieldsets = (
        ('User & Topic', {
            'fields': ('user', 'topic')
        }),
        ('Difficulty', {
            'fields': ('initial_difficulty', 'current_difficulty')
        }),
        ('Progress & Statistics', {
            'fields': ('total_questions', 'correct_answers', 'current_streak', 'accuracy'),
            'classes': ('collapse',)
        }),
        ('Status & Timing', {
            'fields': ('is_completed', 'started_at', 'ended_at', 'duration_display')
        }),
    )

    actions = ['mark_as_completed', 'export_to_csv']

    # Custom display methods

    def user_email(self, obj):
        """Display user email with link"""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.email
        )
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def topic_display(self, obj):
        """Display topic with truncation"""
        if len(obj.topic) > 30:
            return obj.topic[:30] + '...'
        return obj.topic
    topic_display.short_description = 'Topic'
    topic_display.admin_order_field = 'topic'

    def difficulty_badge(self, obj):
        """Display difficulty as colored badge"""
        colors = {
            'easy': '#10b981',
            'medium': '#f59e0b',
            'hard': '#ef4444'
        }
        color = colors.get(obj.initial_difficulty, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.initial_difficulty.upper()
        )
    difficulty_badge.short_description = 'Difficulty'
    difficulty_badge.admin_order_field = 'initial_difficulty'

    def questions_count(self, obj):
        """Display total questions"""
        return obj.total_questions
    questions_count.short_description = 'Questions'
    questions_count.admin_order_field = 'total_questions'

    def score_display(self, obj):
        """Display score as fraction"""
        return f'{obj.correct_answers}/{obj.total_questions}'
    score_display.short_description = 'Score'

    def accuracy_badge(self, obj):
        """Display accuracy with color coding"""
        accuracy = obj.accuracy
        if accuracy >= 80:
            color = '#10b981'  # Green
        elif accuracy >= 50:
            color = '#f59e0b'  # Yellow
        else:
            color = '#ef4444'  # Red

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            f'{accuracy:.1f}'
        )
    accuracy_badge.short_description = 'Accuracy'
    accuracy_badge.admin_order_field = 'correct_answers'

    def status_badge(self, obj):
        """Display completion status with icon"""
        if obj.is_completed:
            return format_html(
                '<span style="color: #10b981;">✓ Completed</span>'
            )
        return format_html(
            '<span style="color: #f59e0b;">⏳ In Progress</span>'
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_completed'

    def duration_display(self, obj):
        """Display quiz duration"""
        if obj.ended_at and obj.started_at:
            duration = obj.ended_at - obj.started_at
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            return f'{minutes}m {seconds}s'
        return 'In progress'
    duration_display.short_description = 'Duration'

    # Custom actions

    def mark_as_completed(self, request, queryset):
        """Mark selected quizzes as completed"""
        from django.utils import timezone
        count = 0
        for session in queryset:
            if not session.is_completed:
                session.is_completed = True
                if not session.ended_at:
                    session.ended_at = timezone.now()
                session.save()
                count += 1
        self.message_user(request, f'{count} quiz(zes) marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'

    def export_to_csv(self, request, queryset):
        """Export selected quizzes to CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="quiz_sessions.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Topic', 'Difficulty', 'Questions',
                        'Correct', 'Accuracy', 'Status', 'Started'])

        for session in queryset:
            writer.writerow([
                session.id,
                session.user.email,
                session.topic,
                session.initial_difficulty,
                session.total_questions,
                session.correct_answers,
                f'{session.accuracy}%',
                'Completed' if session.is_completed else 'In Progress',
                session.started_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
    export_to_csv.short_description = 'Export selected to CSV'


# ==================== QUESTION ADMIN ====================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Enhanced admin for Question model with all answers displayed"""

    list_display = [
        'id',
        'question_preview',
        'topic_display',
        'difficulty_display',
        'answer_count',
        'created_at'
    ]

    list_filter = [
        'difficulty_level',
        'created_at',
        'session__initial_difficulty',
        'session__topic'
    ]

    search_fields = [
        'question_text',
        'correct_answer',
        'wrong_answer_1',
        'wrong_answer_2',
        'wrong_answer_3',
        'explanation',
        'session__topic',
        'session__user__email'
    ]

    readonly_fields = [
        'session',
        'question_text_display',
        'all_answers_display',
        'explanation_display',
        'difficulty_level',
        'created_at'
    ]

    date_hierarchy = 'created_at'

    ordering = ['-created_at']

    list_per_page = 25

    # Prefetch answers for better performance
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('answers')

    inlines = [AnswerInline]

    fieldsets = (
        ('Session Info', {
            'fields': ('session',)
        }),
        ('Question', {
            'fields': ('question_text_display', 'difficulty_level')
        }),
        ('All Answers', {
            'fields': ('all_answers_display',),
            'description': 'All answers with correct answer marked in green'
        }),
        ('Explanation', {
            'fields': ('explanation_display',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # Custom display methods

    def question_preview(self, obj):
        """Display truncated question text"""
        text = obj.question_text
        if len(text) > 60:
            return text[:60] + '...'
        return text
    question_preview.short_description = 'Question'

    def question_text_display(self, obj):
        """Display full question text nicely formatted"""
        return format_html(
            '<div style="padding: 10px; background-color: #f3f4f6; '
            'border-left: 4px solid #3b82f6; border-radius: 4px; font-size: 14px;">'
            '<strong>Question:</strong><br>{}'
            '</div>',
            obj.question_text
        )
    question_text_display.short_description = 'Question Text'

    def all_answers_display(self, obj):
        """Display all answers with correct answer highlighted"""
        answers = [
            ('A', obj.correct_answer, True),
            ('B', obj.wrong_answer_1, False),
            ('C', obj.wrong_answer_2, False),
            ('D', obj.wrong_answer_3, False)
        ]

        # Shuffle to match actual presentation, but we'll show in order with labels
        html_parts = []
        html_parts.append('<div style="margin-top: 10px;">')

        for letter, answer, is_correct in answers:
            if is_correct:
                style = (
                    'padding: 10px; margin: 5px 0; background-color: #d1fae5; '
                    'border: 2px solid #10b981; border-radius: 4px; font-size: 14px;'
                )
                icon = '✓ CORRECT'
                icon_color = '#10b981'
            else:
                style = (
                    'padding: 10px; margin: 5px 0; background-color: #fee2e2; '
                    'border: 1px solid #fecaca; border-radius: 4px; font-size: 14px;'
                )
                icon = '✗ Wrong'
                icon_color = '#ef4444'

            html_parts.append(
                f'<div style="{style}">'
                f'<span style="font-weight: bold; color: {icon_color};">[{icon}]</span> '
                f'<strong>{letter}:</strong> {answer}'
                f'</div>'
            )

        html_parts.append('</div>')
        return format_html(''.join(html_parts))
    all_answers_display.short_description = 'All Answers (Correct Answer Highlighted)'

    def explanation_display(self, obj):
        """Display explanation nicely formatted"""
        return format_html(
            '<div style="padding: 10px; background-color: #fef3c7; '
            'border-left: 4px solid #f59e0b; border-radius: 4px; font-size: 14px;">'
            '<strong>💡 Explanation:</strong><br>{}'
            '</div>',
            obj.explanation
        )
    explanation_display.short_description = 'Explanation'

    def topic_display(self, obj):
        """Display session topic with link"""
        topic = obj.session.topic
        return format_html(
            '<a href="/admin/quiz_app/quizsession/{}/change/" title="{}">{}</a>',
            obj.session.id,
            topic,
            topic[:30] + '...' if len(topic) > 30 else topic
        )
    topic_display.short_description = 'Topic'
    topic_display.admin_order_field = 'session__topic'

    def difficulty_display(self, obj):
        """Display difficulty with color"""
        level = obj.difficulty_level
        colors = {
            'łatwy': ('#10b981', 'Łatwy'),
            'średni': ('#f59e0b', 'Średni'),
            'trudny': ('#ef4444', 'Trudny')
        }
        color, label = colors.get(level, ('#6b7280', level.title()))

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            label
        )
    difficulty_display.short_description = 'Difficulty'
    difficulty_display.admin_order_field = 'difficulty_level'

    def answer_count(self, obj):
        """Display number of user answers submitted"""
        count = obj.answers.count()
        if count == 0:
            return format_html('<span style="color: #9ca3af;">0 answers</span>')

        correct_count = obj.answers.filter(is_correct=True).count()
        wrong_count = count - correct_count

        return format_html(
            '<span style="color: #10b981;">✓ {}</span> / '
            '<span style="color: #ef4444;">✗ {}</span>',
            correct_count,
            wrong_count
        )
    answer_count.short_description = 'User Answers (✓/✗)'

    def has_add_permission(self, request):
        """Prevent manual addition - questions generated via API"""
        return False


# ==================== ANSWER ADMIN ====================

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Enhanced admin for Answer model"""

    list_display = [
        'id',
        'user_email',
        'question_preview',
        'selected_answer_display',
        'correctness_badge',
        'response_time_display',
        'answered_at'
    ]

    list_filter = [
        'is_correct',
        'answered_at'
    ]

    search_fields = [
        'user__email',
        'user__username',
        'question__question_text',
        'selected_answer'
    ]

    readonly_fields = [
        'question',
        'user',
        'selected_answer',
        'is_correct',
        'response_time',
        'answered_at'
    ]

    date_hierarchy = 'answered_at'

    ordering = ['-answered_at']

    fieldsets = (
        ('User & Question', {
            'fields': ('user', 'question')
        }),
        ('Answer Details', {
            'fields': ('selected_answer', 'is_correct')
        }),
        ('Timing', {
            'fields': ('response_time', 'answered_at')
        }),
    )

    # Custom display methods

    def user_email(self, obj):
        """Display user email with link"""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.email
        )
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def question_preview(self, obj):
        """Display truncated question text"""
        text = obj.question.question_text
        if len(text) > 40:
            return format_html(
                '<a href="/admin/quiz_app/question/{}/change/">{}</a>',
                obj.question.id,
                text[:40] + '...'
            )
        return format_html(
            '<a href="/admin/quiz_app/question/{}/change/">{}</a>',
            obj.question.id,
            text
        )
    question_preview.short_description = 'Question'

    def selected_answer_display(self, obj):
        """Display selected answer truncated"""
        answer = obj.selected_answer
        if len(answer) > 30:
            return answer[:30] + '...'
        return answer
    selected_answer_display.short_description = 'Selected Answer'

    def correctness_badge(self, obj):
        """Display correctness with icon and color"""
        if obj.is_correct:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Correct</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">✗ Wrong</span>'
        )
    correctness_badge.short_description = 'Correctness'
    correctness_badge.admin_order_field = 'is_correct'

    def response_time_display(self, obj):
        """Display response time formatted"""
        seconds = obj.response_time
        if seconds < 10:
            color = '#10b981'  # Fast
        elif seconds < 20:
            color = '#f59e0b'  # Medium
        else:
            color = '#ef4444'  # Slow

        return format_html(
            '<span style="color: {};">{}s</span>',
            color,
            f'{seconds:.1f}'
        )
    response_time_display.short_description = 'Response Time'
    response_time_display.admin_order_field = 'response_time'

    def has_add_permission(self, request):
        """Prevent manual addition - answers created via API"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but prevent editing"""
        return True

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True
