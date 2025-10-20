from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


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


class UserSerializer(serializers.ModelSerializer):
    """Serializer dla użytkownika"""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer do rejestracji - email jako główne pole"""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username', validated_data['email'].split('@')[0]),
            password=validated_data['password']
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer do zmiany hasła"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer do aktualizacji profilu"""
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['email', 'username']

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer do uploadu avatara"""

    class Meta:
        model = UserProfile
        fields = ['avatar']