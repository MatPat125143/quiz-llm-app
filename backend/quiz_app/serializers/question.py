from rest_framework import serializers
from ..models import Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'correct_answer',
            'wrong_answer_1', 'wrong_answer_2', 'wrong_answer_3',
            'explanation', 'difficulty_level', 'created_at'
        ]