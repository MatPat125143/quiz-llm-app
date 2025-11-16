from django.conf import settings
from django.db import models
import hashlib


class QuizSession(models.Model):
    KNOWLEDGE_LEVEL_CHOICES = [
        ('elementary', 'Szkoła podstawowa'),
        ('high_school', 'Liceum'),
        ('university', 'Studia'),
        ('expert', 'Ekspert'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_sessions'
    )
    topic = models.CharField(max_length=200)
    subtopic = models.CharField(max_length=200, blank=True, null=True)
    knowledge_level = models.CharField(
        max_length=20,
        choices=KNOWLEDGE_LEVEL_CHOICES,
        default='high_school'
    )
    initial_difficulty = models.CharField(max_length=20)
    current_difficulty = models.CharField(max_length=20)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    questions_count = models.IntegerField(default=10)
    time_per_question = models.IntegerField(default=30)
    use_adaptive_difficulty = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Sesja Quizu'
        verbose_name_plural = 'Sesje Quizów'
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['user', 'is_completed']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.topic}'

    @property
    def accuracy(self):
        if self.total_questions == 0:
            return 0.0
        return round((self.correct_answers / self.total_questions) * 100, 2)


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Łatwy'),
        ('medium', 'Średni'),
        ('hard', 'Trudny'),
    ]

    KNOWLEDGE_LEVEL_CHOICES = [
        ('elementary', 'Szkoła podstawowa'),
        ('high_school', 'Liceum'),
        ('university', 'Studia'),
        ('expert', 'Ekspert'),
    ]

    topic = models.CharField(max_length=200, db_index=True)
    subtopic = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    knowledge_level = models.CharField(
        max_length=20,
        choices=KNOWLEDGE_LEVEL_CHOICES,
        blank=True,
        null=True
    )
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=500)
    wrong_answer_1 = models.CharField(max_length=500)
    wrong_answer_2 = models.CharField(max_length=500)
    wrong_answer_3 = models.CharField(max_length=500)
    explanation = models.TextField()
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    embedding_vector = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_questions'
    )

    times_used = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)

    content_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pytanie'
        verbose_name_plural = 'Pytania'
        indexes = [
            models.Index(fields=['topic', 'difficulty_level']),
            models.Index(fields=['content_hash']),
            models.Index(fields=['-times_used']),
        ]

    def __str__(self):
        return f'{self.topic}: {self.question_text[:50]}'

    def save(self, *args, **kwargs):
        if not self.content_hash:
            content = f"{self.question_text}{self.correct_answer}{self.topic}{self.subtopic or ''}{self.knowledge_level or ''}{self.difficulty_level}"
            self.content_hash = hashlib.sha256(content.encode()).hexdigest()
        super().save(*args, **kwargs)


class QuizSessionQuestion(models.Model):
    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='session_questions'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='question_sessions'
    )
    order = models.IntegerField(default=0)
    shown_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order']
        unique_together = [['session', 'question']]
        verbose_name = 'Pytanie w Sesji'
        verbose_name_plural = 'Pytania w Sesjach'
        indexes = [
            models.Index(fields=['session', 'order']),
        ]

    def __str__(self):
        return f"Session {self.session.id} - Question {self.question.id}"


class Answer(models.Model):
    session_question = models.ForeignKey(
        QuizSessionQuestion,
        on_delete=models.CASCADE,
        related_name='answer_set'
    )
    selected_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField()
    response_time = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-answered_at']
        verbose_name = 'Odpowiedź'
        verbose_name_plural = 'Odpowiedzi'
        indexes = [
            models.Index(fields=['session_question']),
            models.Index(fields=['-answered_at']),
        ]

    def __str__(self):
        return f"Answer to Question {self.session_question.question.id}"
