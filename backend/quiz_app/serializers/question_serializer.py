from rest_framework import serializers
from django.utils import timezone

from ..models import Question
from ..utils.constants import DIFFICULTY_ALIAS_MAP


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'correct_answer',
            'wrong_answer_1', 'wrong_answer_2', 'wrong_answer_3',
            'explanation', 'difficulty_level', 'created_at', 'updated_at', 'edited_at'
        ]


class AdminQuestionSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        return obj.created_by.email if obj.created_by else None

    def validate_question_text(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                'Question text must be at least 10 characters'
            )
        return value

    def validate_difficulty_level(self, value):
        diff_value = (value or '').strip().lower()
        if diff_value not in DIFFICULTY_ALIAS_MAP:
            raise serializers.ValidationError('Invalid difficulty level')
        return value

    def validate_knowledge_level(self, value):
        if value not in ['elementary', 'high_school', 'university', 'expert']:
            raise serializers.ValidationError('Invalid knowledge level')
        return value

    def update(self, instance, validated_data):
        editable_fields = [
            'topic', 'subtopic', 'knowledge_level', 'question_text',
            'correct_answer', 'wrong_answer_1', 'wrong_answer_2',
            'wrong_answer_3', 'explanation', 'difficulty_level'
        ]
        hash_fields = [
            'topic', 'subtopic', 'knowledge_level',
            'question_text', 'correct_answer', 'difficulty_level'
        ]

        has_meaningful_change = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in editable_fields
        )
        has_hash_change = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in hash_fields
        )

        instance = super().update(instance, validated_data)

        update_fields = []
        if has_hash_change:
            instance.content_hash = Question.build_content_hash(
                question_text=instance.question_text,
                correct_answer=instance.correct_answer,
                topic=instance.topic,
                subtopic=instance.subtopic,
                knowledge_level=instance.knowledge_level,
                difficulty_level=instance.difficulty_level,
            )
            update_fields.append('content_hash')

        if has_meaningful_change:
            instance.edited_at = timezone.now()
            update_fields.append('edited_at')

        if update_fields:
            instance.save(update_fields=update_fields)

        return instance

    class Meta:
        model = Question
        fields = [
            'id', 'topic', 'subtopic', 'knowledge_level',
            'question_text', 'correct_answer', 'wrong_answer_1',
            'wrong_answer_2', 'wrong_answer_3', 'explanation',
            'difficulty_level', 'total_answers', 'correct_answers_count',
            'success_rate', 'times_used', 'created_at', 'updated_at', 'edited_at', 'created_by'
        ]
