from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from quiz_app.models import QuizSession, Question

User = get_user_model()


class QuizViewsTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_start_quiz_authenticated(self):
        url = reverse('start-quiz')
        data = {
            'topic': 'Python',
            'difficulty': 'medium',
            'questions_count': 10,
            'time_per_question': 30,
            'use_adaptive_difficulty': True,
            'knowledge_level': 'high_school'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('session_id', response.data)

    def test_start_quiz_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('start-quiz')
        data = {
            'topic': 'Python',
            'difficulty': 'medium',
            'questions_count': 10,
            'time_per_question': 30
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_quiz_history(self):
        QuizSession.objects.create(
            user=self.user,
            topic='Python',
            initial_difficulty='medium',
            current_difficulty='medium',
            questions_count=10,
            is_completed=True
        )

        url = reverse('quiz-history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)


class QuestionViewsTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_questions_library(self):
        Question.objects.create(
            topic='Python',
            question_text='Co to jest Python?',
            correct_answer='Język programowania',
            wrong_answer_1='Ptak',
            wrong_answer_2='Wąż',
            wrong_answer_3='Gra',
            explanation='Wyjaśnienie',
            difficulty_level='medium'
        )

        url = reverse('questions-library')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)