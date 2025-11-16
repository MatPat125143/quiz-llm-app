from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import UserProfile, PasswordResetToken
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_str(self):
        self.assertEqual(str(self.user), 'test@example.com')

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')


class UserProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_profile_auto_created(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_default_role(self):
        self.assertEqual(self.user.profile.role, 'user')

    def test_default_statistics(self):
        profile = self.user.profile
        self.assertEqual(profile.total_quizzes_played, 0)
        self.assertEqual(profile.total_questions_answered, 0)
        self.assertEqual(profile.total_correct_answers, 0)
        self.assertEqual(profile.highest_streak, 0)

    def test_accuracy_property(self):
        profile = self.user.profile
        self.assertEqual(profile.accuracy, 0.0)

        profile.total_questions_answered = 10
        profile.total_correct_answers = 7
        profile.save()

        self.assertEqual(profile.accuracy, 70.0)

    def test_profile_str(self):
        expected = f"{self.user.email} - user"
        self.assertEqual(str(self.user.profile), expected)


class PasswordResetTokenModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_generate_code(self):
        code = PasswordResetToken.generate_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_token_creation(self):
        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=self.user, code=code)

        self.assertEqual(token.user, self.user)
        self.assertEqual(token.code, code)
        self.assertFalse(token.used)

    def test_is_valid_new_token(self):
        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=self.user, code=code)

        self.assertTrue(token.is_valid())

    def test_is_valid_used_token(self):
        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=self.user, code=code, used=True)

        self.assertFalse(token.is_valid())

    def test_is_valid_expired_token(self):
        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=self.user, code=code)

        token.created_at = timezone.now() - timedelta(hours=2)
        token.save()

        self.assertFalse(token.is_valid())

    def test_token_str(self):
        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=self.user, code=code)

        expected = f"{self.user.email} - {code} - Ważny"
        self.assertEqual(str(token), expected)