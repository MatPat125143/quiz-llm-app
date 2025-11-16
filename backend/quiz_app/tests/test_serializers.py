from django.test import TestCase
from django.contrib.auth import get_user_model
from quiz_app.models import QuizSession, Question
from quiz_app.serializers import (
    QuizSessionSerializer,
    QuestionSerializer,
    QuizSessionCreateSerializer,
    QuestionCreateSerializer
)

User = get_user_model()


class QuizSessionSerializerTest(TestCase):

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
            questions_count=10,
            total_questions=10,
            correct_answers=7
        )

    def test_serializer_contains_expected_fields(self):
        serializer = QuizSessionSerializer(instance=self.session)
        data = serializer.data

        self.assertIn('id', data)
        self.assertIn('topic', data)
        self.assertIn('username', data)
        self.assertIn('accuracy', data)

    def test_accuracy_calculation(self):
        serializer = QuizSessionSerializer(instance=self.session)
        data = serializer.data

        self.assertEqual(data['accuracy'], 70.0)


class QuizSessionCreateSerializerTest(TestCase):

    def test_valid_data(self):
        data = {
            'topic': 'Python',
            'difficulty': 'medium',
            'questions_count': 10,
            'time_per_question': 30,
            'use_adaptive_difficulty': True,
            'knowledge_level': 'high_school'
        }

        serializer = QuizSessionCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_difficulty(self):
        data = {
            'topic': 'Python',
            'difficulty': 'invalid',
            'questions_count': 10,
            'time_per_question': 30
        }

        serializer = QuizSessionCreateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('difficulty', serializer.errors)

    def test_topic_validation(self):
        data = {
            'topic': 'A',
            'difficulty': 'medium',
            'questions_count': 10,
            'time_per_question': 30
        }

        serializer = QuizSessionCreateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('topic', serializer.errors)


class QuestionSerializerTest(TestCase):

    def setUp(self):
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

    def test_serializer_contains_expected_fields(self):
        serializer = QuestionSerializer(instance=self.question)
        data = serializer.data

        self.assertIn('id', data)
        self.assertIn('question_text', data)
        self.assertIn('difficulty_level', data)
        self.assertIn('difficulty_display', data)

    def test_difficulty_display(self):
        serializer = QuestionSerializer(instance=self.question)
        data = serializer.data

        self.assertEqual(data['difficulty_display'], 'Średni')


class QuestionCreateSerializerTest(TestCase):

    def test_valid_question_data(self):
        data = {
            'topic': 'Python',
            'question_text': 'Pytanie testowe o Pythonie?',
            'correct_answer': 'Odpowiedź A',
            'wrong_answer_1': 'Odpowiedź B',
            'wrong_answer_2': 'Odpowiedź C',
            'wrong_answer_3': 'Odpowiedź D',
            'explanation': 'Wyjaśnienie',
            'difficulty_level': 'medium'
        }

        serializer = QuestionCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_duplicate_answers(self):
        data = {
            'topic': 'Python',
            'question_text': 'Pytanie testowe?',
            'correct_answer': 'Odpowiedź A',
            'wrong_answer_1': 'Odpowiedź A',
            'wrong_answer_2': 'Odpowiedź C',
            'wrong_answer_3': 'Odpowiedź D',
            'explanation': 'Wyjaśnienie',
            'difficulty_level': 'medium'
        }

        serializer = QuestionCreateSerializer(data=data)

        self.assertFalse(serializer.is_valid())