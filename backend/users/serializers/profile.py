from rest_framework import serializers
from ..models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer dla profilu użytkownika"""
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['role', 'avatar', 'avatar_url', 'total_quizzes_played',
                  'total_questions_answered', 'total_correct_answers',
                  'highest_streak', 'accuracy', 'created_at', 'updated_at']
        read_only_fields = ['total_quizzes_played', 'total_questions_answered',
                            'total_correct_answers', 'highest_streak', 'accuracy',
                            'created_at', 'updated_at']

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer do uploadu avatara"""

    class Meta:
        model = UserProfile
        fields = ['avatar']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer do zmiany hasła"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)