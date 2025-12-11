from rest_framework import serializers
from django.contrib.auth import get_user_model
from .profile import UserProfileSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer dla użytkownika"""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer do rejestracji - email jako główne pole + poziom wiedzy"""
    password = serializers.CharField(write_only=True, min_length=8)
    default_knowledge_level = serializers.ChoiceField(
        choices=['elementary', 'high_school', 'university', 'expert'],
        default='high_school',
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'default_knowledge_level']

    def create(self, validated_data):
        # Wyciągnij default_knowledge_level przed utworzeniem usera
        default_knowledge_level = validated_data.pop('default_knowledge_level', 'high_school')

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username', validated_data['email'].split('@')[0]),
            password=validated_data['password']
        )

        # Zaktualizuj profil użytkownika z poziomem wiedzy
        if hasattr(user, 'profile'):
            user.profile.default_knowledge_level = default_knowledge_level
            user.profile.save()

        return user


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