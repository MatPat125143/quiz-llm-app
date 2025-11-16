from django.test import TestCase
from django.contrib.auth import get_user_model
from quiz_app.services import QuizService, QuestionService, AnswerService
from quiz_app.models import QuizSession, Question, QuizSessionQuestion
from core.exceptions import QuizNotFound, QuizAlreadyCompleted, QuestionNotFound

User = get_user_model()


class QuizServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_quiz_session(self):
        session = QuizService.create_quiz_session(
            user=self.user,
            topic='Python',
            difficulty='medium',
            questions_count=10,
            time_per_question=30,
            use_adaptive_difficulty=True
        )

        self.assertIsNotNone(session.id)
        self.assertEqual(session.topic, 'Python')
        self.assertEqual(session.questions_count, 10)
        self.assertFalse(session.is_completed)

    def test_get_active_session(self):
        session = QuizService.create_quiz_session(
            user=self.user,
            topic='Django',
            difficulty='easy',
            questions_count=5,
            time_per_question=20
        )

        retrieved = QuizService.get_active_session(session.id, self.user)

        self.assertEqual(retrieved.id, session.id)

    def test_get_active_session_not_found(self):
        with self.assertRaises(QuizNotFound):
            QuizService.get_active_session(9999, self.user)

    def test_get_completed_session_raises_error(self):
        session = QuizService.create_quiz_session(
            user=self.user,
            topic='Python',
            difficulty='medium',
            questions_count=5,
            time_per_question=30
        )

        session.is_completed = True
        session.save()

        with self.assertRaises(QuizAlreadyCompleted):
            QuizService.get_active_session(session.id, self.user)

    def test_end_quiz_session(self):
        session = QuizService.create_quiz_session(
            user=self.user,
            topic='Python',
            difficulty='medium',
            questions_count=5,
            time_per_question=30
        )

        ended_session = QuizService.end_quiz_session(session.id, self.user)

        self.assertTrue(ended_session.is_completed)
        self.assertIsNotNone(ended_session.completed_at)

    def test_calculate_session_statistics(self):
        session = QuizSession.objects.create(
            user=self.user,
            topic='Python',
            initial_difficulty='medium',
            current_difficulty='medium',
            questions_count=10,
            total_questions=10,
            correct_answers=7,
            is_completed=True
        )

        stats = QuizService.calculate_session_statistics(session)

        self.assertEqual(stats['total_questions'], 10)
        self.assertEqual(stats['correct_answers'], 7)
        self.assertEqual(stats['score_percentage'], 70.0)


class QuestionServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.session = QuizSession.objects.create(
            user=self.user,
            topic='Python',
            initial_difficulty='medium',
            current_difficulty='medium',
            questions_count=5
        )

        self.question = Question.objects.create(
            topic='Python',
            question_text='Co to jest Python?',
            correct_answer='Język programowania',
            wrong_answer_1='Ptak',
            wrong_answer_2='Wąż',
            wrong_answer_3='Gra',
            explanation='Wyjaśnienie',
            difficulty_level='medium'
        )

    def test_get_question_with_details(self):
        service = QuestionService()
        question = service.get_question_with_details(self.question.id)

        self.assertEqual(question.id, self.question.id)

    def test_get_question_not_found(self):
        service = QuestionService()

        with self.assertRaises(QuestionNotFound):
            service.get_question_with_details(9999)

    def test_update_question_statistics(self):
        service = QuestionService()

        initial_times_used = self.question.times_used

        service.update_question_statistics(self.question, is_correct=True, response_time=10)

        self.question.refresh_from_db()
        self.assertEqual(self.question.times_used, initial_times_used + 1)


class AnswerServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.session = QuizSession.objects.create(
            user=self.user,
            topic='Python',
            initial_difficulty='medium',
            current_difficulty='medium',
            questions_count=5
        )

        self.question = Question.objects.create(
            topic='Python',
            question_text='Co to jest Python?',
            correct_answer='Język programowania',
            wrong_answer_1='Ptak',
            wrong_answer_2='Wąż',
            wrong_answer_3='Gra',
            explanation='Wyjaśnienie',
            difficulty_level='medium'
        )

        self.session_question = QuizSessionQuestion.objects.create(
            session=self.session,
            question=self.question
        )

    def test_submit_correct_answer(self):
        result = AnswerService.submit_answer(
            user=self.user,
            question_id=self.question.id,
            selected_answer='Język programowania',
            response_time=15
        )

        self.assertTrue(result['is_correct'])
        self.assertEqual(result['correct_answer'], 'Język programowania')

    def test_submit_wrong_answer(self):
        result = AnswerService.submit_answer(
            user=self.user,
            question_id=self.question.id,
            selected_answer='Ptak',
            response_time=10
        )

        self.assertFalse(result['is_correct'])

    def test_get_session_answers(self):
        AnswerService.submit_answer(
            user=self.user,
            question_id=self.question.id,
            selected_answer='Język programowania',
            response_time=15
        )

        answers = AnswerService.get_session_answers(self.session)

        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0]['question_id'], self.question.id)