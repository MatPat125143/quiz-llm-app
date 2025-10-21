from rest_framework import serializers
from .models import QuizSession, Question, Answer


class QuizSessionSerializer(serializers.ModelSerializer):
    accuracy = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)
    difficulty = serializers.CharField(source='initial_difficulty', read_only=True)
    score = serializers.IntegerField(source='correct_answers', read_only=True)
    completed_at = serializers.DateTimeField(source='ended_at', read_only=True)

    class Meta:
        model = QuizSession
        fields = ['id', 'username', 'topic', 'initial_difficulty', 'difficulty', 'current_difficulty',
                  'started_at', 'ended_at', 'completed_at', 'is_completed', 'total_questions',
                  'correct_answers', 'score', 'current_streak', 'accuracy']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'correct_answer', 'wrong_answer_1',
                  'wrong_answer_2', 'wrong_answer_3', 'explanation',
                  'difficulty_level', 'created_at']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'selected_answer', 'is_correct',
                  'response_time', 'answered_at']