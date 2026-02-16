import hashlib

from django.conf import settings
from django.db import models


class QuizSession(models.Model):
    KNOWLEDGE_LEVEL_CHOICES = [
        ('elementary', 'Szkoła podstawowa'),
        ('high_school', 'Liceum'),
        ('university', 'Studia'),
        ('expert', 'Ekspert'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_sessions')
    topic = models.CharField(max_length=200)
    subtopic = models.CharField(max_length=200, blank=True, null=True)
    knowledge_level = models.CharField(max_length=20, choices=KNOWLEDGE_LEVEL_CHOICES, default='high_school')
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
    questions_generated_count = models.IntegerField(default=0)

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
    DIFFICULTY_CHOICES = [
        ('łatwy', 'Łatwy'),
        ('średni', 'Średni'),
        ('trudny', 'Trudny'),
    ]

    KNOWLEDGE_LEVEL_CHOICES = [
        ('elementary', 'Szkoła podstawowa'),
        ('high_school', 'Liceum'),
        ('university', 'Studia'),
        ('expert', 'Ekspert'),
    ]

    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='questions',
        null=True,
        blank=True
    )

    topic = models.CharField(max_length=200, db_index=True)
    subtopic = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    knowledge_level = models.CharField(max_length=20, choices=KNOWLEDGE_LEVEL_CHOICES, blank=True, null=True)
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=500)
    wrong_answer_1 = models.CharField(max_length=500)
    wrong_answer_2 = models.CharField(max_length=500)
    wrong_answer_3 = models.CharField(max_length=500)
    explanation = models.TextField()
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='średni')
    embedding_vector = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_questions'
    )

    total_answers = models.IntegerField(default=0)
    correct_answers_count = models.IntegerField(default=0)
    times_used = models.IntegerField(default=0)

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

    @property
    def incorrect_answers_count(self):
        return max(0, self.total_answers - self.correct_answers_count)

    def update_stats(self, is_correct):
        self.total_answers += 1
        if is_correct:
            self.correct_answers_count += 1
        self.times_used = self.total_answers
        self.save(update_fields=['total_answers', 'correct_answers_count', 'times_used'])

    @staticmethod
    def build_content_hash(
        question_text,
        correct_answer,
        topic,
        subtopic=None,
        knowledge_level=None,
        difficulty_level=None,
    ):
        content = (
            f"{question_text}{correct_answer}{topic}"
            f"{subtopic or ''}{knowledge_level or ''}{difficulty_level}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def compute_content_hash(self):
        return self.build_content_hash(
            self.question_text,
            self.correct_answer,
            self.topic,
            self.subtopic,
            self.knowledge_level,
            self.difficulty_level,
        )

    def save(self, *args, **kwargs):
        if not self.content_hash:
            self.content_hash = self.compute_content_hash()
        super().save(*args, **kwargs)


class QuizSessionQuestion(models.Model):
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
    difficulty_at_answer = models.FloatField(default=5.0)

    class Meta:
        ordering = ['-answered_at']
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        indexes = [
            models.Index(fields=['question', 'user']),
            models.Index(fields=['session', '-answered_at']),
            models.Index(fields=['-answered_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'user', 'session'],
                name='unique_answer_per_question_session'
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {'correct' if self.is_correct else 'wrong'}"
