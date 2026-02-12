from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..utils.constants import KNOWLEDGE_LEVELS
from .profile_serializer import UserProfileSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'profile',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_staff', 'is_superuser']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    default_knowledge_level = serializers.ChoiceField(
        choices=KNOWLEDGE_LEVELS,
        default='high_school',
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'default_knowledge_level']

    def create(self, validated_data):
        default_knowledge_level = validated_data.pop('default_knowledge_level', 'high_school')

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username', validated_data['email'].split('@')[0]),
            password=validated_data['password']
        )

        if hasattr(user, 'profile'):
            user.profile.default_knowledge_level = default_knowledge_level
            user.profile.save()

        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
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
