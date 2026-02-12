from rest_framework import serializers
from ..models import QuizSession
from ..utils.constants import (
    DEFAULT_QUESTIONS_COUNT,
    DEFAULT_TIME_PER_QUESTION,
    DEFAULT_USE_ADAPTIVE_DIFFICULTY,
    DIFFICULTY_VALUE_MAP,
    DIFFICULTY_ALIAS_MAP,
)


class QuizSessionSerializer(serializers.ModelSerializer):
    accuracy = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)
    difficulty = serializers.CharField(source='initial_difficulty', read_only=True)
    score = serializers.IntegerField(source='correct_answers', read_only=True)
    completed_at = serializers.DateTimeField(source='ended_at', read_only=True)
    is_custom = serializers.SerializerMethodField()
    initial_difficulty_value = serializers.SerializerMethodField()

    def get_is_custom(self, obj):
        return (obj.questions_count != DEFAULT_QUESTIONS_COUNT or
                obj.time_per_question != DEFAULT_TIME_PER_QUESTION or
                obj.use_adaptive_difficulty != DEFAULT_USE_ADAPTIVE_DIFFICULTY)

    def get_initial_difficulty_value(self, obj):
        if hasattr(obj, 'initial_difficulty_value') and obj.initial_difficulty_value is not None:
            try:
                return float(obj.initial_difficulty_value)
            except (TypeError, ValueError):
                pass

        name = (obj.initial_difficulty or '').strip().lower()
        normalized = DIFFICULTY_ALIAS_MAP.get(name, name)
        return DIFFICULTY_VALUE_MAP.get(normalized, None)

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

