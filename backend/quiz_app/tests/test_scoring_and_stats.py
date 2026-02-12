from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Answer, Question, QuizSession, QuizSessionQuestion
from quiz_app.services.answer_service import update_profile_stats_on_completion

User = get_user_model()


class ScoringAndStatsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='stats_user@example.com',
            username='stats_user',
            password='Secret123!'
        )
        self.client.force_authenticate(user=self.user)

    def _question(self, idx):
        return Question.objects.create(
            topic='Matematyka',
            subtopic='Algebra',
            knowledge_level='high_school',
            question_text=f'Pytanie {idx}: ile to {idx}+{idx}?',
            correct_answer=str(idx + idx),
            wrong_answer_1='0',
            wrong_answer_2='1',
            wrong_answer_3='2',
            explanation='Wyjaśnienie',
            difficulty_level='średni'
        )

    def test_update_profile_stats_on_completion_aggregates_correctly(self):
        s1 = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            is_completed=True,
            ended_at=timezone.now()
        )
        s2 = QuizSession.objects.create(
            user=self.user,
            topic='Fizyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            is_completed=True,
            ended_at=timezone.now()
        )

        q1, q2, q3, q4, q5 = [self._question(i) for i in range(1, 6)]

        Answer.objects.create(question=q1, user=self.user, session=s1, selected_answer=q1.correct_answer, is_correct=True, response_time=1.0)
        Answer.objects.create(question=q2, user=self.user, session=s1, selected_answer=q2.correct_answer, is_correct=True, response_time=1.0)
        Answer.objects.create(question=q3, user=self.user, session=s1, selected_answer='x', is_correct=False, response_time=1.0)
        Answer.objects.create(question=q4, user=self.user, session=s2, selected_answer=q4.correct_answer, is_correct=True, response_time=1.0)
        Answer.objects.create(question=q5, user=self.user, session=s2, selected_answer='x', is_correct=False, response_time=1.0)

        update_profile_stats_on_completion(self.user)
        profile = self.user.profile
        profile.refresh_from_db()

        self.assertEqual(profile.total_quizzes_played, 2)
        self.assertEqual(profile.total_questions_answered, 5)
        self.assertEqual(profile.total_correct_answers, 3)
        self.assertEqual(profile.highest_streak, 2)
        self.assertEqual(profile.accuracy, 60.0)

    @patch('quiz_app.views.answer_view.cleanup_unused_session_questions')
    @patch('quiz_app.views.answer_view.handle_adaptive_difficulty_change', return_value=(False, None, None))
    def test_submit_answer_on_last_question_updates_profile_stats(
        self,
        _mock_difficulty,
        _mock_cleanup
    ):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=1,
            time_per_question=30,
            use_adaptive_difficulty=False,
            is_completed=False
        )
        question = self._question(10)
        QuizSessionQuestion.objects.create(session=session, question=question, order=1)

        response = self.client.post(
            '/api/quiz/answer/',
            {'question_id': question.id, 'selected_answer': question.correct_answer, 'response_time': 2.4},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['quiz_completed'])

        session.refresh_from_db()
        profile = self.user.profile
        profile.refresh_from_db()

        self.assertTrue(session.is_completed)
        self.assertEqual(session.total_questions, 1)
        self.assertEqual(session.correct_answers, 1)
        self.assertEqual(profile.total_quizzes_played, 1)
        self.assertEqual(profile.total_questions_answered, 1)
        self.assertEqual(profile.total_correct_answers, 1)
