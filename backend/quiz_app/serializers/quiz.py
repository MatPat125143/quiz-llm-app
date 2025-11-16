from rest_framework import serializers
from quiz_app.models import QuizSession


class QuizSessionSerializer(serializers.ModelSerializer):
    accuracy = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)
    difficulty = serializers.CharField(source='initial_difficulty', read_only=True)
    score = serializers.IntegerField(source='correct_answers', read_only=True)
    completed_at = serializers.DateTimeField(source='ended_at', read_only=True)
    is_custom = serializers.SerializerMethodField()
    initial_difficulty_value = serializers.SerializerMethodField()

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

    def get_is_custom(self, obj):
        return (obj.questions_count != 10 or
                obj.time_per_question != 30 or
                not obj.use_adaptive_difficulty)

    def get_initial_difficulty_value(self, obj):
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


class QuizSessionListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    score_percentage = serializers.SerializerMethodField()

    class Meta:
        model = QuizSession
        fields = [
            'id', 'username', 'topic', 'subtopic',
            'initial_difficulty', 'started_at', 'ended_at',
            'is_completed', 'total_questions', 'correct_answers',
            'score_percentage'
        ]

    def get_score_percentage(self, obj):
        if obj.total_questions and obj.total_questions > 0:
            return round((obj.correct_answers / obj.total_questions) * 100, 2)
        return 0.0


class QuizSessionDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    accuracy = serializers.ReadOnlyField()
    score_percentage = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = QuizSession
        fields = [
            'id', 'username', 'user_email', 'topic', 'subtopic',
            'knowledge_level', 'initial_difficulty', 'current_difficulty',
            'started_at', 'ended_at', 'is_completed',
            'total_questions', 'correct_answers',
            'current_streak', 'best_streak',
            'accuracy', 'score_percentage', 'duration_seconds',
            'questions_count', 'time_per_question', 'use_adaptive_difficulty'
        ]

    def get_score_percentage(self, obj):
        if obj.total_questions and obj.total_questions > 0:
            return round((obj.correct_answers / obj.total_questions) * 100, 2)
        return 0.0

    def get_duration_seconds(self, obj):
        if obj.started_at and obj.ended_at:
            duration = obj.ended_at - obj.started_at
            return int(duration.total_seconds())
        return 0


class QuizSessionCreateSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=200, required=True)
    subtopic = serializers.CharField(max_length=200, required=False, allow_blank=True)
    knowledge_level = serializers.ChoiceField(
        choices=['elementary', 'high_school', 'university', 'expert'],
        default='high_school'
    )
    difficulty = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        required=True
    )
    questions_count = serializers.IntegerField(min_value=1, max_value=50, required=True)
    time_per_question = serializers.IntegerField(min_value=10, max_value=300, required=True)
    use_adaptive_difficulty = serializers.BooleanField(default=False)

    def validate_topic(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Temat jest wymagany')

        if len(value.strip()) < 2:
            raise serializers.ValidationError('Temat musi mieć co najmniej 2 znaki')

        return value.strip()

    def validate_subtopic(self, value):
        if value:
            return value.strip()
        return ''