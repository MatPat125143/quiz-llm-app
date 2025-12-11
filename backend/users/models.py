from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone
import secrets


class User(AbstractUser):
    """Custom User model - logowanie przez email"""
    email = models.EmailField(unique=True)

    # Usuń first_name i last_name - są w AbstractUser, ale nie używamy
    first_name = None
    last_name = None

    # Email jako główne pole logowania
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username staje się opcjonalne

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """Profil użytkownika z dodatkowymi danymi"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    KNOWLEDGE_LEVEL_CHOICES = [
        ('elementary', 'Szkoła podstawowa'),
        ('high_school', 'Liceum'),
        ('university', 'Studia'),
        ('expert', 'Ekspert'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # NOWE: Domyślny poziom wiedzy użytkownika
    default_knowledge_level = models.CharField(
        max_length=20,
        choices=KNOWLEDGE_LEVEL_CHOICES,
        default='high_school',
        help_text='Domyślny poziom wiedzy używany przy tworzeniu quizów'
    )

    # Statystyki
    total_quizzes_played = models.IntegerField(default=0)
    total_questions_answered = models.IntegerField(default=0)
    total_correct_answers = models.IntegerField(default=0)
    highest_streak = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.role}"

    @property
    def accuracy(self):
        if self.total_questions_answered == 0:
            return 0
        return round((self.total_correct_answers / self.total_questions_answered) * 100, 1)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatyczne tworzenie profilu po utworzeniu użytkownika"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Automatyczne zapisywanie profilu"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class PasswordResetToken(models.Model):
    """Token do resetowania hasła"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    code = models.CharField(max_length=6)  # 6-cyfrowy kod
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']

    def is_valid(self):
        """Sprawdź czy token jest ważny (nie starszy niż 1h i nieużyty)"""
        from django.conf import settings
        from datetime import timedelta
        from django.utils import timezone
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        expiry_time = self.created_at + timedelta(seconds=timeout)
        return not self.used and timezone.now() < expiry_time

    @staticmethod
    def generate_code():
        """Generuj 6-cyfrowy kod"""
        import secrets
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    def __str__(self):
        return f"{self.user.email} - {self.code} - {'Used' if self.used else 'Valid'}"