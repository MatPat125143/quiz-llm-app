from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import PasswordResetToken

User = get_user_model()


class AuthAndPermissionsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='player_auth@example.com',
            username='player_auth',
            password='Secret123!'
        )
        self.admin = User.objects.create_user(
            email='admin_auth@example.com',
            username='admin_auth',
            password='Secret123!'
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save(update_fields=['role'])

    def test_users_me_requires_authentication(self):
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_cannot_access_admin_dashboard_endpoint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_admin_dashboard_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/users/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)

    def test_password_reset_request_requires_email(self):
        response = self.client.post('/api/users/password-reset/request/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_request_creates_token(self):
        with patch(
            'users.services.auth_service.email_service.send_password_reset_email',
            return_value=True
        ):
            response = self.client.post(
                '/api/users/password-reset/request/',
                {'email': self.user.email},
                format='json'
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            PasswordResetToken.objects.filter(user=self.user, used=False).exists()
        )

    def test_password_reset_request_for_unknown_email_returns_generic_success(self):
        response = self.client.post(
            '/api/users/password-reset/request/',
            {'email': 'not-found@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_and_confirm_password_reset_flow(self):
        token = PasswordResetToken.objects.create(user=self.user, code='123456')

        verify_response = self.client.post(
            '/api/users/password-reset/verify/',
            {'email': self.user.email, 'code': token.code},
            format='json'
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        confirm_response = self.client.post(
            '/api/users/password-reset/confirm/',
            {
                'email': self.user.email,
                'code': token.code,
                'new_password': 'NewPass123!'
            },
            format='json'
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        token.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))
        self.assertTrue(token.used)

    def test_verify_reset_code_rejects_invalid_code(self):
        response = self.client.post(
            '/api/users/password-reset/verify/',
            {'email': self.user.email, 'code': '999999'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_rejects_short_password(self):
        token = PasswordResetToken.objects.create(user=self.user, code='333444')
        response = self.client.post(
            '/api/users/password-reset/confirm/',
            {
                'email': self.user.email,
                'code': token.code,
                'new_password': 'short'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
