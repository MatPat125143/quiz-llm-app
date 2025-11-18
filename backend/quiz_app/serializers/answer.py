from rest_framework import serializers
from ..models import Answer


class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='question.correct_answer', read_only=True)
    wrong_answer_1 = serializers.CharField(source='question.wrong_answer_1', read_only=True)
    wrong_answer_2 = serializers.CharField(source='question.wrong_answer_2', read_only=True)
    wrong_answer_3 = serializers.CharField(source='question.wrong_answer_3', read_only=True)
    explanation = serializers.CharField(source='question.explanation', read_only=True)

    class Meta:
        model = Answer
        fields = [
            'id',
            'question_text',
            'correct_answer',
            'wrong_answer_1',
            'wrong_answer_2',
            'wrong_answer_3',
            'selected_answer',
            'is_correct',
            'explanation',
            'response_time',
            'answered_at'
        ]