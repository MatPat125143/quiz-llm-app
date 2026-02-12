from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Answer, Question, QuizSession

User = get_user_model()


class AdminDeleteSessionApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin_session@example.com',
            username='admin_session',
            password='Secret123!'
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save(update_fields=['role'])

        self.player = User.objects.create_user(
            email='player_session@example.com',
            username='player_session',
            password='Secret123!'
        )

    def _create_session_with_answer(self):
        session = QuizSession.objects.create(
            user=self.player,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=10,
            time_per_question=30,
            is_completed=True,
            total_questions=1,
            correct_answers=1
        )
        question = Question.objects.create(
            topic='Matematyka',
            subtopic='Równania',
            knowledge_level='high_school',
            question_text='Ile to 2 + 2?',
            correct_answer='4',
            wrong_answer_1='3',
            wrong_answer_2='5',
            wrong_answer_3='6',
            explanation='2 + 2 = 4',
            difficulty_level='średni'
        )
        Answer.objects.create(
            question=question,
            user=self.player,
            session=session,
            selected_answer='4',
            is_correct=True,
            response_time=3.5,
            difficulty_at_answer=5.0
        )
        return session

    def test_admin_can_delete_quiz_session(self):
        session = self._create_session_with_answer()
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(f'/api/users/admin/sessions/{session.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(QuizSession.objects.filter(id=session.id).exists())
        self.assertEqual(Answer.objects.filter(session_id=session.id).count(), 0)

    def test_non_admin_cannot_delete_quiz_session(self):
        session = self._create_session_with_answer()
        self.client.force_authenticate(user=self.player)

        response = self.client.delete(f'/api/users/admin/sessions/{session.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(QuizSession.objects.filter(id=session.id).exists())
