from django.conf import settings
from django.db import models


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

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.email} - {self.topic}'

    @property
    def accuracy(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 2)


class Question(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=500)
    wrong_answer_1 = models.CharField(max_length=500)
    wrong_answer_2 = models.CharField(max_length=500)
    wrong_answer_3 = models.CharField(max_length=500)
    explanation = models.TextField()
    difficulty_level = models.FloatField()
    embedding_vector = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Q{self.id}: {self.question_text[:50]}'


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField()
    response_time = models.FloatField()
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {'✓' if self.is_correct else '✗'}"