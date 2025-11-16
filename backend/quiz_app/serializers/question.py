from rest_framework import serializers
from quiz_app.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    times_used = serializers.IntegerField(read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    difficulty_display = serializers.SerializerMethodField()
    knowledge_level_display = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'topic', 'subtopic', 'knowledge_level',
            'question_text', 'correct_answer',
            'wrong_answer_1', 'wrong_answer_2', 'wrong_answer_3',
            'explanation', 'difficulty_level', 'difficulty_display',
            'knowledge_level_display',
            'times_used', 'times_correct', 'success_rate',
            'created_at', 'updated_at'
        ]

    def get_difficulty_display(self, obj):
        difficulty_map = {
            'easy': 'Łatwy',
            'medium': 'Średni',
            'hard': 'Trudny',
        }
        return difficulty_map.get(obj.difficulty_level, obj.difficulty_level)

    def get_knowledge_level_display(self, obj):
        knowledge_map = {
            'elementary': 'Podstawowy',
            'high_school': 'Liceum',
            'university': 'Uniwersytet',
            'expert': 'Ekspert',
        }
        return knowledge_map.get(obj.knowledge_level, obj.knowledge_level)


class QuestionListSerializer(serializers.ModelSerializer):
    difficulty_display = serializers.SerializerMethodField()
    success_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'topic', 'subtopic', 'question_text',
            'difficulty_level', 'difficulty_display',
            'times_used', 'success_rate', 'created_at'
        ]

    def get_difficulty_display(self, obj):
        difficulty_map = {
            'easy': 'Łatwy',
            'medium': 'Średni',
            'hard': 'Trudny',
        }
        return difficulty_map.get(obj.difficulty_level, obj.difficulty_level)


class QuestionDetailSerializer(serializers.ModelSerializer):
    difficulty_display = serializers.SerializerMethodField()
    knowledge_level_display = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'topic', 'subtopic', 'knowledge_level', 'knowledge_level_display',
            'question_text', 'correct_answer',
            'wrong_answer_1', 'wrong_answer_2', 'wrong_answer_3',
            'explanation', 'difficulty_level', 'difficulty_display',
            'times_used', 'times_correct', 'success_rate',
            'created_by_username', 'created_at', 'updated_at'
        ]

    def get_difficulty_display(self, obj):
        difficulty_map = {
            'easy': 'Łatwy',
            'medium': 'Średni',
            'hard': 'Trudny',
        }
        return difficulty_map.get(obj.difficulty_level, obj.difficulty_level)

    def get_knowledge_level_display(self, obj):
        knowledge_map = {
            'elementary': 'Podstawowy',
            'high_school': 'Liceum',
            'university': 'Uniwersytet',
            'expert': 'Ekspert',
        }
        return knowledge_map.get(obj.knowledge_level, obj.knowledge_level)


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'topic', 'subtopic', 'knowledge_level',
            'question_text', 'correct_answer',
            'wrong_answer_1', 'wrong_answer_2', 'wrong_answer_3',
            'explanation', 'difficulty_level'
        ]

    def validate_question_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Treść pytania jest wymagana')

        if len(value.strip()) < 10:
            raise serializers.ValidationError('Treść pytania musi mieć co najmniej 10 znaków')

        return value.strip()

    def validate_correct_answer(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Poprawna odpowiedź jest wymagana')

        return value.strip()

    def validate(self, data):
        wrong_answers = [
            data.get('wrong_answer_1'),
            data.get('wrong_answer_2'),
            data.get('wrong_answer_3')
        ]

        if not all(wrong_answers):
            raise serializers.ValidationError('Wszystkie 3 niepoprawne odpowiedzi są wymagane')

        all_answers = [data.get('correct_answer')] + wrong_answers
        if len(all_answers) != len(set(all_answers)):
            raise serializers.ValidationError('Wszystkie odpowiedzi muszą być unikalne')

        return data