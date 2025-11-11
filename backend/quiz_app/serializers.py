from rest_framework import serializers
from .models import QuizSession, Question, Answer


class QuizSessionSerializer(serializers.ModelSerializer):
    accuracy = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)
    difficulty = serializers.CharField(source='initial_difficulty', read_only=True)
    score = serializers.IntegerField(source='correct_answers', read_only=True)
    completed_at = serializers.DateTimeField(source='ended_at', read_only=True)
    is_custom = serializers.SerializerMethodField()
    # NEW: liczbowy odpowiednik początkowej trudności (dla frontu)
    initial_difficulty_value = serializers.SerializerMethodField()

    def get_is_custom(self, obj):
        """Sprawdź czy quiz używał niestandardowych ustawień"""
        return (obj.questions_count != 10 or
                obj.time_per_question != 30 or
                not obj.use_adaptive_difficulty)

    def get_initial_difficulty_value(self, obj):
        """
        Zwraca liczbę odpowiadającą startowemu poziomowi trudności.
        Jeśli masz w modelu pole 'initial_difficulty_value' – użyj go,
        w przeciwnym razie mapuj z tekstu.
        """
        # jeśli kiedyś dodasz pole w modelu, to będzie użyte w pierwszej kolejności
        if hasattr(obj, 'initial_difficulty_value') and obj.initial_difficulty_value is not None:
            try:
                return float(obj.initial_difficulty_value)
            except (TypeError, ValueError):
                pass

        mapping = {
            'easy': 2.0, 'medium': 5.0, 'hard': 8.0,
            'łatwy': 2.0, 'średni': 5.0, 'trudny': 8.0,
        }
        name = (obj.initial_difficulty or '').strip().lower()
        return mapping.get(name, None)

    class Meta:
        model = QuizSession
        fields = [
            'id', 'username', 'topic', 'subtopic', 'knowledge_level',  # <-- DODANE subtopic i knowledge_level
            'initial_difficulty', 'difficulty', 'current_difficulty',
            'initial_difficulty_value',          # <-- DODANE
            'started_at', 'ended_at', 'completed_at', 'is_completed',
            'total_questions', 'correct_answers', 'score',
            'current_streak', 'accuracy', 'questions_count',
            'time_per_question', 'use_adaptive_difficulty', 'is_custom'
        ]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'correct_answer',
            'wrong_answer_1', 'wrong_answer_2', 'wrong_answer_3',
            'explanation', 'difficulty_level', 'created_at'
        ]


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