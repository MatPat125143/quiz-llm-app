from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from llm_integration.difficulty_adapter import DifficultyAdapter
from quiz_app.models import Answer, Question, QuizSession, QuizSessionQuestion
from quiz_app.services.answer_service import handle_adaptive_difficulty_change

User = get_user_model()


class AdaptiveDifficultyServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='adaptive_user@example.com',
            username='adaptive_user',
            password='Secret123!'
        )
        self.adapter = DifficultyAdapter()

    def _question(self, text, difficulty='łatwy'):
        return Question.objects.create(
            topic='Matematyka',
            subtopic='Algebra',
            knowledge_level='high_school',
            question_text=text,
            correct_answer='4',
            wrong_answer_1='3',
            wrong_answer_2='5',
            wrong_answer_3='6',
            explanation='Wyjaśnienie',
            difficulty_level=difficulty
        )

    @patch('quiz_app.services.answer_service.QuizCacheService.clear_session_cache')
    @patch('quiz_app.services.answer_service._schedule_level_generation')
    def test_handle_adaptive_difficulty_change_updates_level_and_cleans_old_questions(
        self,
        mock_schedule_generation,
        mock_clear_session_cache
    ):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='easy',
            current_difficulty=4.0,
            questions_count=10,
            total_questions=2,
            use_adaptive_difficulty=True,
            is_completed=False
        )

        answered_q1 = self._question('Pytanie 1', difficulty='łatwy')
        answered_q2 = self._question('Pytanie 2', difficulty='łatwy')
        old_unused_q = self._question('Pytanie do usunięcia', difficulty='łatwy')

        QuizSessionQuestion.objects.create(session=session, question=answered_q1, order=1)
        QuizSessionQuestion.objects.create(session=session, question=answered_q2, order=2)
        QuizSessionQuestion.objects.create(session=session, question=old_unused_q, order=3)

        Answer.objects.create(
            question=answered_q1,
            user=self.user,
            session=session,
            selected_answer='4',
            is_correct=True,
            response_time=1.0,
            difficulty_at_answer=4.0
        )
        Answer.objects.create(
            question=answered_q2,
            user=self.user,
            session=session,
            selected_answer='4',
            is_correct=True,
            response_time=1.0,
            difficulty_at_answer=4.0
        )

        level_changed, previous_level, new_level = handle_adaptive_difficulty_change(
            session=session,
            difficulty_adapter=self.adapter,
            bg_generator=Mock()
        )

        self.assertTrue(level_changed)
        self.assertEqual(previous_level, 'łatwy')
        self.assertEqual(new_level, 'średni')
        self.assertEqual(session.current_difficulty, 5.0)
        self.assertFalse(Question.objects.filter(id=old_unused_q.id).exists())
        mock_clear_session_cache.assert_called_once_with(session.id)
        mock_schedule_generation.assert_called_once()

    def test_handle_adaptive_difficulty_change_is_noop_when_feature_disabled(self):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Matematyka',
            initial_difficulty='easy',
            current_difficulty=4.0,
            questions_count=10,
            total_questions=1,
            use_adaptive_difficulty=False,
            is_completed=False
        )

        level_changed, previous_level, new_level = handle_adaptive_difficulty_change(
            session=session,
            difficulty_adapter=self.adapter,
            bg_generator=Mock()
        )

        self.assertFalse(level_changed)
        self.assertIsNone(previous_level)
        self.assertIsNone(new_level)
        self.assertEqual(session.current_difficulty, 4.0)
