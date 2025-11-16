from django.test import TestCase
from django.contrib.auth import get_user_model
from quiz_app.models import Question, QuizSession, QuizSessionQuestion, Answer
from django.utils import timezone

User = get_user_model()


class QuestionModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.question = Question.objects.create(
            topic='Python',
            question_text='Co to jest Python?',
            correct_answer='Język programowania',
            wrong_answer_1='Ptak',
            wrong_answer_2='Wąż',
            wrong_answer_3='Gra komputerowa',
            explanation='Python to język programowania wysokiego poziomu',
            difficulty_level='medium',
            created_by=self.user
        )

    def test_question_creation(self):
        self.assertEqual(self.question.topic, 'Python')
        self.assertEqual(self.question.difficulty_level, 'medium')
        self.assertEqual(self.question.times_used, 0)
        self.assertEqual(self.question.times_correct, 0)

    def test_question_str(self):
        expected = f"{self.question.topic}: {self.question.question_text[:50]}"
        self.assertEqual(str(self.question), expected)

    def test_update_statistics(self):
        self.question.times_used = 10
        self.question.times_correct = 7
        self.question.success_rate = (7 / 10) * 100
        self.question.save()

        self.assertEqual(self.question.success_rate, 70.0)

    def test_content_hash_unique(self):
        duplicate = Question(
            topic='Python',
            question_text='Co to jest Python?',
            correct_answer='Język programowania',
            wrong_answer_1='Ptak',
            wrong_answer_2='Wąż',
            wrong_answer_3='Gra komputerowa',
            explanation='Python to język programowania wysokiego poziomu',
            difficulty_level='medium',
            content_hash=self.question.content_hash
        )

        with self.assertRaises(Exception):
            duplicate.save()


class QuizSessionModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.session = QuizSession.objects.create(
            user=self.user,
            topic='Django',
            initial_difficulty='medium',
            current_difficulty='medium',
            questions_count=10,
            time_per_question=30,
            use_adaptive_difficulty=True
        )

    def test_session_creation(self):
        self.assertEqual(self.session.topic, 'Django')
        self.assertEqual(self.session.questions_count, 10)
        self.assertFalse(self.session.is_completed)
        self.assertEqual(self.session.total_questions, 0)
        self.assertEqual(self.session.correct_answers, 0)

    def test_session_str(self):
        expected = f"{self.user.username} - {self.session.topic}"
        self.assertEqual(str(self.session), expected)

    def test_accuracy_property(self):
        self.session.total_questions = 10
        self.session.correct_answers = 7
        self.session.save()

        self.assertEqual(self.session.accuracy, 70.0)

    def test_accuracy_zero_questions(self):
        self.assertEqual(self.session.accuracy, 0.0)

    def test_session_completion(self):
        self.session.is_completed = True
        self.session.completed_at = timezone.now()
        self.session.save()

        self.assertTrue(self.session.is_completed)
        self.assertIsNotNone(self.session.completed_at)


class QuizSessionQuestionModelTest(TestCase):

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
            question_text='Pytanie testowe?',
            correct_answer='Odpowiedź A',
            wrong_answer_1='Odpowiedź B',
            wrong_answer_2='Odpowiedź C',
            wrong_answer_3='Odpowiedź D',
            explanation='Wyjaśnienie',
            difficulty_level='medium'
        )

        self.session_question = QuizSessionQuestion.objects.create(
            session=self.session,
            question=self.question
        )

    def test_session_question_creation(self):
        self.assertEqual(self.session_question.session, self.session)
        self.assertEqual(self.session_question.question, self.question)
        self.assertIsNone(self.session_question.answered_at)

    def test_session_question_str(self):
        expected = f"Session {self.session.id} - Question {self.question.id}"
        self.assertEqual(str(self.session_question), expected)

    def test_mark_as_answered(self):
        self.session_question.answered_at = timezone.now()
        self.session_question.save()

        self.assertIsNotNone(self.session_question.answered_at)


class AnswerModelTest(TestCase):

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
            question_text='Pytanie testowe?',
            correct_answer='Odpowiedź A',
            wrong_answer_1='Odpowiedź B',
            wrong_answer_2='Odpowiedź C',
            wrong_answer_3='Odpowiedź D',
            explanation='Wyjaśnienie',
            difficulty_level='medium'
        )

        self.session_question = QuizSessionQuestion.objects.create(
            session=self.session,
            question=self.question
        )

        self.answer = Answer.objects.create(
            session_question=self.session_question,
            selected_answer='Odpowiedź A',
            is_correct=True,
            response_time=15
        )

    def test_answer_creation(self):
        self.assertEqual(self.answer.selected_answer, 'Odpowiedź A')
        self.assertTrue(self.answer.is_correct)
        self.assertEqual(self.answer.response_time, 15)

    def test_answer_str(self):
        expected = f"Answer to Question {self.question.id}"
        self.assertEqual(str(self.answer), expected)

    def test_incorrect_answer(self):
        incorrect_answer = Answer.objects.create(
            session_question=self.session_question,
            selected_answer='Odpowiedź B',
            is_correct=False,
            response_time=10
        )

        self.assertFalse(incorrect_answer.is_correct)