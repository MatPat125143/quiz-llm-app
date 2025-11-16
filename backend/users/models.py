from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import timedelta
from django.utils import timezone
import secrets


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = None
    last_name = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Użytkownik'),
        ('admin', 'Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    total_quizzes_played = models.IntegerField(default=0)
    total_questions_answered = models.IntegerField(default=0)
    total_correct_answers = models.IntegerField(default=0)
    highest_streak = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Użytkownika'
        verbose_name_plural = 'Profile Użytkowników'

    def __str__(self):
        return f"{self.user.email} - {self.role}"

    @property
    def accuracy(self):
        if self.total_questions_answered == 0:
            return 0.0
        return round((self.total_correct_answers / self.total_questions_answered) * 100, 1)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Token Resetowania Hasła'
        verbose_name_plural = 'Tokeny Resetowania Hasła'
        ordering = ['-created_at']

    def is_valid(self):
        from django.conf import settings
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        expiry_time = self.created_at + timedelta(seconds=timeout)
        return not self.used and timezone.now() < expiry_time

    @staticmethod
    def generate_code():
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    def __str__(self):
        return f"{self.user.email} - {self.code} - {'Użyty' if self.used else 'Ważny'}"