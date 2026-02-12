import os
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


def _gif_file(name='avatar.gif'):
    gif_bytes = (
        b'GIF89a\x01\x00\x01\x00\x80\x00\x00'
        b'\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,'
        b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    )
    return SimpleUploadedFile(name, gif_bytes, content_type='image/gif')


class AvatarCleanupApiTests(APITestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='quiz-avatar-tests-')
        self.addCleanup(lambda: shutil.rmtree(self.media_root, ignore_errors=True))

        self.user = User.objects.create_user(
            email='avatar_user@example.com',
            username='avatar_user',
            password='Secret123!'
        )
        self.client.force_authenticate(user=self.user)

    def _upload_avatar(self, file_name):
        with override_settings(MEDIA_ROOT=self.media_root):
            response = self.client.post(
                '/api/users/avatar/upload/',
                {'avatar': _gif_file(file_name)},
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        return self.user.profile.avatar.path

    def test_upload_then_delete_avatar_removes_file_from_media(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            file_path = self._upload_avatar('first.gif')
            self.assertTrue(os.path.exists(file_path))

            delete_response = self.client.delete('/api/users/avatar/delete/')
            self.assertEqual(delete_response.status_code, status.HTTP_200_OK)

            self.user.refresh_from_db()
            self.assertFalse(bool(self.user.profile.avatar))
            self.assertFalse(os.path.exists(file_path))

    def test_replacing_avatar_deletes_previous_file(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            first_path = self._upload_avatar('first.gif')
            self.assertTrue(os.path.exists(first_path))

            second_path = self._upload_avatar('second.gif')
            self.assertTrue(os.path.exists(second_path))
            self.assertNotEqual(first_path, second_path)
            self.assertFalse(os.path.exists(first_path))

    def test_delete_avatar_returns_400_when_no_avatar(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            response = self.client.delete('/api/users/avatar/delete/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_account_removes_avatar_file_via_signal(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            avatar_path = self._upload_avatar('to_delete_with_account.gif')
            self.assertTrue(os.path.exists(avatar_path))

            response = self.client.delete('/api/users/delete/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(os.path.exists(avatar_path))
