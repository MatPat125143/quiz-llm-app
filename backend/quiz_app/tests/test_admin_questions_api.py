from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Answer, Question, QuizSession, QuizSessionQuestion

User = get_user_model()


class AdminQuestionsApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin_questions@example.com',
            username='admin_questions',
            password='Secret123!'
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save(update_fields=['role'])

        self.user = User.objects.create_user(
            email='user_questions@example.com',
            username='user_questions',
            password='Secret123!'
        )

    def _question(self):
        return Question.objects.create(
            topic='Matematyka',
            subtopic='Algebra',
            knowledge_level='high_school',
            question_text='To jest przykładowa treść pytania do walidacji.',
            correct_answer='4',
            wrong_answer_1='3',
            wrong_answer_2='5',
            wrong_answer_3='6',
            explanation='Wyjaśnienie',
            difficulty_level='średni',
            created_by=self.admin
        )

    def test_non_admin_cannot_access_admin_questions_endpoint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/quiz/admin/questions/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_question_rejects_too_short_question_text(self):
        question = self._question()
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f'/api/quiz/admin/questions/{question.id}/update/',
            {'question_text': 'krótkie'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('question_text', response.data)

    def test_update_question_sets_edited_at_and_updates_hash(self):
        question = self._question()
        old_hash = question.content_hash
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f'/api/quiz/admin/questions/{question.id}/update/',
            {'correct_answer': '42'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        question.refresh_from_db()
        self.assertIsNotNone(question.edited_at)
        self.assertNotEqual(question.content_hash, old_hash)
        self.assertEqual(question.correct_answer, '42')

    def test_delete_question_blocked_when_used_in_active_session(self):
        question = self._question()
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            is_completed=False
        )
        QuizSessionQuestion.objects.create(session=session, question=question, order=1)

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/quiz/admin/questions/{question.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Question.objects.filter(id=question.id).exists())

    def test_delete_question_removes_related_answers_and_links(self):
        question = self._question()
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            is_completed=True
        )
        QuizSessionQuestion.objects.create(session=session, question=question, order=1)
        Answer.objects.create(
            question=question,
            user=self.user,
            session=session,
            selected_answer='4',
            is_correct=True,
            response_time=1.1
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/quiz/admin/questions/{question.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Question.objects.filter(id=question.id).exists())
        self.assertEqual(Answer.objects.filter(question=question).count(), 0)
        self.assertEqual(QuizSessionQuestion.objects.filter(question=question).count(), 0)
