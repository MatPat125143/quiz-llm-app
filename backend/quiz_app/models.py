from django.conf import settings
from django.db import models
import hashlib


class QuizSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_sessions')
    topic = models.CharField(max_length=200)
    initial_difficulty = models.CharField(max_length=20)
    current_difficulty = models.FloatField(default=1.0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    questions_count = models.IntegerField(default=10)
    time_per_question = models.IntegerField(default=30)
    use_adaptive_difficulty = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Quiz Session'
        verbose_name_plural = 'Quiz Sessions'
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['user', 'is_completed']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.topic}'

    @property
    def accuracy(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 2)


class Question(models.Model):
    """GLOBALNE pytanie - może być używane w wielu quizach"""
    DIFFICULTY_CHOICES = [
        ('łatwy', 'Łatwy'),
        ('średni', 'Średni'),
        ('trudny', 'Trudny'),
    ]

    # session teraz OPCJONALNE (dla kompatybilności)
    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='questions',
        null=True,
        blank=True
    )

    # NOWE POLA dla globalnych pytań
    topic = models.CharField(max_length=200, db_index=True)
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=500)
    wrong_answer_1 = models.CharField(max_length=500)
    wrong_answer_2 = models.CharField(max_length=500)
    wrong_answer_3 = models.CharField(max_length=500)
    explanation = models.TextField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='średni')
    embedding_vector = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Nowe metadane
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_questions'
    )

    # Statystyki
    total_answers = models.IntegerField(default=0)
    correct_answers_count = models.IntegerField(default=0)
    times_used = models.IntegerField(default=0)  # NOWE

    # Hash dla deduplikacji
    content_hash = models.CharField(max_length=64, db_index=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        indexes = [
            models.Index(fields=['topic', 'difficulty_level']),
            models.Index(fields=['content_hash']),
            models.Index(fields=['-times_used']),
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f'Q{self.id}: {self.question_text[:50]}'

    @property
    def success_rate(self):
        if self.total_answers == 0:
            return 0
        return round((self.correct_answers_count / self.total_answers) * 100, 1)

    def update_stats(self, is_correct):
        self.total_answers += 1
        if is_correct:
            self.correct_answers_count += 1
        self.save(update_fields=['total_answers', 'correct_answers_count'])

    def save(self, *args, **kwargs):
        if not self.content_hash:
            content = f"{self.question_text}{self.correct_answer}{self.topic}{self.difficulty_level}"
            self.content_hash = hashlib.sha256(content.encode()).hexdigest()
        super().save(*args, **kwargs)


class QuizSessionQuestion(models.Model):
    """NOWY MODEL - łączy pytanie z sesją"""
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='session_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_sessions')
    order = models.IntegerField(default=0)
    shown_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = [['session', 'question']]
        verbose_name = 'Quiz Session Question'
        verbose_name_plural = 'Quiz Session Questions'
        indexes = [
            models.Index(fields=['session', 'order']),
        ]

    def __str__(self):
        return f"Session {self.session.id} - Question {self.question.id}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='answers',
        null=True,
        blank=True
    )
    selected_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField()
    response_time = models.FloatField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-answered_at']
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        indexes = [
            models.Index(fields=['question', 'user']),
            models.Index(fields=['session', '-answered_at']),
            models.Index(fields=['-answered_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {'✓' if self.is_correct else '✗'}"