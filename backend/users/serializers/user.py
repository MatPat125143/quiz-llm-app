from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'role',
            'role_display',
            'avatar',
            'avatar_url',
            'total_quizzes_played',
            'total_questions_answered',
            'total_correct_answers',
            'highest_streak',
            'accuracy',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'total_quizzes_played',
            'total_questions_answered',
            'total_correct_answers',
            'highest_streak',
            'accuracy',
            'created_at',
            'updated_at'
        ]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_role_display(self, obj):
        role_map = {
            'user': 'Użytkownik',
            'admin': 'Administrator',
        }
        return role_map.get(obj.role, obj.role)


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    total_quizzes = serializers.IntegerField(source='profile.total_quizzes_played', read_only=True)
    accuracy = serializers.FloatField(source='profile.accuracy', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'total_quizzes', 'accuracy', 'is_active', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    re_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 're_password']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Użytkownik o podanym adresie email już istnieje')
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Ta nazwa użytkownika jest już zajęta')
        return value

    def validate(self, data):
        if data.get('password') != data.get('re_password'):
            raise serializers.ValidationError({'re_password': 'Hasła nie są identyczne'})
        return data

    def create(self, validated_data):
        validated_data.pop('re_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username', validated_data['email'].split('@')[0]),
            password=validated_data['password']
        )
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False, min_length=3, max_length=150)

    class Meta:
        model = User
        fields = ['email', 'username']

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('Ten email jest już używany')
        return value

    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError('Ta nazwa użytkownika jest już używana')
        return value