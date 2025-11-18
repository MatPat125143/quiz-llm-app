from rest_framework import serializers
from ..models import QuizSession


class QuizSessionSerializer(serializers.ModelSerializer):
    accuracy = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)
    difficulty = serializers.CharField(source='initial_difficulty', read_only=True)
    score = serializers.IntegerField(source='correct_answers', read_only=True)
    completed_at = serializers.DateTimeField(source='ended_at', read_only=True)
    is_custom = serializers.SerializerMethodField()
    initial_difficulty_value = serializers.SerializerMethodField()

    def get_is_custom(self, obj):
        """Sprawdź czy quiz używał niestandardowych ustawień"""
        return (obj.questions_count != 10 or
                obj.time_per_question != 30 or
                not obj.use_adaptive_difficulty)

    def get_initial_difficulty_value(self, obj):
        """Zwraca liczbę odpowiadającą startowemu poziomowi trudności"""
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
            'id', 'username', 'topic', 'subtopic', 'knowledge_level',
            'initial_difficulty', 'difficulty', 'current_difficulty',
            'initial_difficulty_value',
            'started_at', 'ended_at', 'completed_at', 'is_completed',
            'total_questions', 'correct_answers', 'score',
            'current_streak', 'accuracy', 'questions_count',
            'time_per_question', 'use_adaptive_difficulty', 'is_custom'
        ]