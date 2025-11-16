from django.test import TestCase
from django.contrib.auth import get_user_model
from users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer
)

User = get_user_model()


class UserSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_serializer_contains_expected_fields(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        self.assertIn('id', data)
        self.assertIn('email', data)
        self.assertIn('username', data)
        self.assertIn('profile', data)


class UserCreateSerializerTest(TestCase):

    def test_valid_user_creation(self):
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'password123',
            're_password': 'password123'
        }

        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'password123',
            're_password': 'different123'
        }

        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('re_password', serializer.errors)


class ChangePasswordSerializerTest(TestCase):

    def test_valid_data(self):
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123'
        }

        serializer = ChangePasswordSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_short_new_password(self):
        data = {
            'old_password': 'oldpass123',
            'new_password': 'short'
        }

        serializer = ChangePasswordSerializer(data=data)
        self.assertFalse(serializer.is_valid())