from django.test import TestCase
from django.contrib.auth import get_user_model
from users.services import UserService, AuthService, AdminService
from users.models import PasswordResetToken
from core.exceptions import UserNotFound, ValidationException
from quiz_app.models import QuizSession

User = get_user_model()


class UserServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_get_user_by_id(self):
        user = UserService.get_user_by_id(self.user.id)
        self.assertEqual(user.id, self.user.id)

    def test_get_user_by_id_not_found(self):
        with self.assertRaises(UserNotFound):
            UserService.get_user_by_id(9999)

    def test_get_user_by_email(self):
        user = UserService.get_user_by_email('test@example.com')
        self.assertEqual(user.email, 'test@example.com')

    def test_update_profile(self):
        updated_user = UserService.update_profile(
            self.user,
            {'username': 'newusername'}
        )

        self.assertEqual(updated_user.username, 'newusername')

    def test_change_password(self):
        result = UserService.change_password(
            self.user,
            'testpass123',
            'newpassword123'
        )

        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_change_password_wrong_old(self):
        with self.assertRaises(ValidationException):
            UserService.change_password(
                self.user,
                'wrongpassword',
                'newpassword123'
            )


class AuthServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_request_password_reset(self):
        result = AuthService.request_password_reset('test@example.com')
        self.assertTrue(result)

        tokens = PasswordResetToken.objects.filter(user=self.user, used=False)
        self.assertEqual(tokens.count(), 1)

    def test_verify_reset_code(self):
        code = PasswordResetToken.generate_code()
        PasswordResetToken.objects.create(user=self.user, code=code)

        result = AuthService.verify_reset_code('test@example.com', code)
        self.assertTrue(result)

    def test_reset_password_with_code(self):
        code = PasswordResetToken.generate_code()
        PasswordResetToken.objects.create(user=self.user, code=code)

        result = AuthService.reset_password_with_code(
            'test@example.com',
            code,
            'newpassword123'
        )

        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))


class AdminServiceTest(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='admin123'
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='user123'
        )

    def test_get_dashboard_statistics(self):
        stats = AdminService.get_dashboard_statistics()

        self.assertIn('total_users', stats)
        self.assertIn('total_quizzes', stats)
        self.assertIn('avg_accuracy', stats)

    def test_get_all_users(self):
        users = AdminService.get_all_users()

        self.assertGreaterEqual(len(users), 2)

    def test_delete_user(self):
        username = AdminService.delete_user(self.user.id, self.admin)

        self.assertEqual(username, 'user')
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_toggle_user_status(self):
        result = AdminService.toggle_user_status(self.user.id, self.admin)

        self.assertIn('is_active', result)
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, result['is_active'])