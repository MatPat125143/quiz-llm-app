from rest_framework import serializers
from quiz_app.models import Answer, QuizSessionQuestion


class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='session_question.question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='session_question.question.correct_answer', read_only=True)
    wrong_answer_1 = serializers.CharField(source='session_question.question.wrong_answer_1', read_only=True)
    wrong_answer_2 = serializers.CharField(source='session_question.question.wrong_answer_2', read_only=True)
    wrong_answer_3 = serializers.CharField(source='session_question.question.wrong_answer_3', read_only=True)
    explanation = serializers.CharField(source='session_question.question.explanation', read_only=True)

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


class AnswerDetailSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(source='session_question.question.id', read_only=True)
    question_text = serializers.CharField(source='session_question.question.question_text', read_only=True)
    topic = serializers.CharField(source='session_question.question.topic', read_only=True)
    difficulty = serializers.CharField(source='session_question.question.difficulty_level', read_only=True)
    correct_answer = serializers.CharField(source='session_question.question.correct_answer', read_only=True)
    explanation = serializers.CharField(source='session_question.question.explanation', read_only=True)

    class Meta:
        model = Answer
        fields = [
            'id', 'question_id', 'question_text', 'topic', 'difficulty',
            'selected_answer', 'correct_answer', 'is_correct',
            'explanation', 'response_time', 'answered_at'
        ]


class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.CharField(required=True, allow_blank=False)
    response_time = serializers.IntegerField(required=False, default=0, min_value=0)

    def validate_question_id(self, value):
        if value <= 0:
            raise serializers.ValidationError('ID pytania musi być liczbą dodatnią')
        return value

    def validate_selected_answer(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Odpowiedź jest wymagana')
        return value.strip()

    def validate_response_time(self, value):
        if value < 0:
            raise serializers.ValidationError('Czas odpowiedzi nie może być ujemny')
        if value > 3600:
            raise serializers.ValidationError('Czas odpowiedzi przekroczył limit')
        return value


class SessionAnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(source='session_question.question.id', read_only=True)
    question_text = serializers.CharField(source='session_question.question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='session_question.question.correct_answer', read_only=True)
    difficulty = serializers.CharField(source='session_question.question.difficulty_level', read_only=True)
    explanation = serializers.CharField(source='session_question.question.explanation', read_only=True)

    class Meta:
        model = Answer
        fields = [
            'question_id', 'question_text', 'difficulty',
            'selected_answer', 'correct_answer', 'is_correct',
            'explanation', 'response_time'
        ]