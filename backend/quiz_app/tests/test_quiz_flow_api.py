from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Question, QuizSession, QuizSessionQuestion

User = get_user_model()


class QuizFlowApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='quiz_flow_user@example.com',
            username='quiz_flow_user',
            password='Secret123!'
        )
        self.client.force_authenticate(user=self.user)

    def _create_question(self, text='Ile to 2 + 2?', correct='4'):
        return Question.objects.create(
            topic='Matematyka',
            subtopic='Równania',
            knowledge_level='high_school',
            question_text=text,
            correct_answer=correct,
            wrong_answer_1='3',
            wrong_answer_2='5',
            wrong_answer_3='6',
            explanation='Proste działanie',
            difficulty_level='średni'
        )

    @patch('quiz_app.views.quiz_view.BackgroundGenerationService.generate_remaining_questions_async')
    @patch('quiz_app.views.quiz_view.BackgroundGenerationService.generate_initial_questions_sync')
    def test_start_quiz_clamps_limits_and_creates_session(
        self,
        mock_generate_initial,
        mock_generate_async
    ):
        mock_generate_initial.return_value = [object(), object(), object()]

        response = self.client.post(
            '/api/quiz/start/',
            {
                'topic': 'Matematyka',
                'subtopic': 'Równania',
                'knowledge_level': 'high_school',
                'difficulty': 'easy',
                'questions_count': 999,
                'time_per_question': 1,
                'use_adaptive_difficulty': True
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = QuizSession.objects.get(id=response.data['session_id'])
        self.assertEqual(session.questions_count, 20)
        self.assertEqual(session.time_per_question, 10)
        self.assertEqual(session.initial_difficulty, 'easy')
        self.assertEqual(session.topic, 'Matematyka')
        self.assertTrue(mock_generate_initial.called)
        self.assertTrue(mock_generate_async.called)

    @patch(
        'quiz_app.views.quiz_view.BackgroundGenerationService.generate_initial_questions_sync',
        side_effect=RuntimeError('generation failed')
    )
    def test_start_quiz_returns_500_and_rolls_back_session_on_generation_error(self, _mock_generate_initial):
        response = self.client.post(
            '/api/quiz/start/',
            {'topic': 'Matematyka', 'difficulty': 'medium'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(QuizSession.objects.filter(user=self.user).count(), 0)

    @patch('quiz_app.views.question_view.get_next_question_payload')
    def test_get_question_returns_payload_for_active_session(self, mock_get_next_question_payload):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=10,
            time_per_question=30,
            is_completed=False
        )
        mock_get_next_question_payload.return_value = ({'question_id': 123, 'topic': 'Matematyka'}, None)

        response = self.client.get(f'/api/quiz/question/{session.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['question_id'], 123)

    def test_get_question_returns_404_for_completed_session(self):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=10,
            time_per_question=30,
            is_completed=True
        )
        response = self.client.get(f'/api/quiz/question/{session.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('quiz_app.views.answer_view.prefetch_next_question_cache')
    @patch('quiz_app.views.answer_view.handle_adaptive_difficulty_change', return_value=(False, None, None))
    def test_submit_answer_updates_session_and_question_stats(
        self,
        _mock_handle_difficulty,
        _mock_prefetch_cache
    ):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=2,
            time_per_question=30,
            use_adaptive_difficulty=False,
            is_completed=False
        )
        question = self._create_question()
        QuizSessionQuestion.objects.create(session=session, question=question, order=1)

        response = self.client.post(
            '/api/quiz/answer/',
            {
                'question_id': question.id,
                'selected_answer': '4',
                'response_time': 2.1
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_correct'])
        self.assertFalse(response.data['quiz_completed'])

        session.refresh_from_db()
        question.refresh_from_db()
        self.assertEqual(session.total_questions, 1)
        self.assertEqual(session.correct_answers, 1)
        self.assertEqual(session.current_streak, 1)
        self.assertEqual(question.total_answers, 1)
        self.assertEqual(question.correct_answers_count, 1)

    @patch('quiz_app.views.answer_view.handle_adaptive_difficulty_change', return_value=(False, None, None))
    def test_submit_answer_timeout_sets_was_timeout(self, _mock_handle_difficulty):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=2,
            time_per_question=30,
            use_adaptive_difficulty=False,
            is_completed=False
        )
        question = self._create_question(text='Ile to 3 + 3?', correct='6')
        QuizSessionQuestion.objects.create(session=session, question=question, order=1)

        response = self.client.post(
            '/api/quiz/answer/',
            {
                'question_id': question.id,
                'selected_answer': '',
                'response_time': 30.0
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_correct'])
        self.assertTrue(response.data['was_timeout'])

    @patch('quiz_app.views.answer_view.handle_adaptive_difficulty_change', return_value=(False, None, None))
    def test_submit_answer_returns_existing_result_without_double_count(self, _mock_handle_difficulty):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=3,
            time_per_question=30,
            is_completed=False
        )
        question = self._create_question(text='Ile to 7 + 1?', correct='8')
        QuizSessionQuestion.objects.create(session=session, question=question, order=1)

        first = self.client.post(
            '/api/quiz/answer/',
            {'question_id': question.id, 'selected_answer': '8', 'response_time': 1.5},
            format='json'
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        second = self.client.post(
            '/api/quiz/answer/',
            {'question_id': question.id, 'selected_answer': '8', 'response_time': 1.5},
            format='json'
        )
        self.assertEqual(second.status_code, status.HTTP_200_OK)

        session.refresh_from_db()
        self.assertEqual(session.total_questions, 1)
        self.assertEqual(session.correct_answers, 1)

    @patch('quiz_app.views.quiz_view.rollback_session')
    def test_end_quiz_deletes_incomplete_session(self, mock_rollback):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=5,
            total_questions=1,
            correct_answers=1,
            is_completed=False
        )
        response = self.client.post(f'/api/quiz/end/{session.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['deleted'])
        mock_rollback.assert_called_once()

    def test_end_quiz_marks_complete_when_all_questions_answered(self):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=2,
            total_questions=2,
            correct_answers=1,
            is_completed=False
        )
        response = self.client.post(f'/api/quiz/end/{session.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['deleted'])

        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        self.assertIsNotNone(session.ended_at)

    @patch('quiz_app.views.quiz_view.rollback_session')
    def test_cancel_quiz_rolls_back_active_session(self, mock_rollback):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='medium',
            current_difficulty=5.0,
            questions_count=5,
            total_questions=1,
            is_completed=False
        )
        response = self.client.post(f'/api/quiz/cancel/{session.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['canceled'])
        mock_rollback.assert_called_once()
