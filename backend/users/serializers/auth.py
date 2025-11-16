from rest_framework import serializers


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, min_length=1)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Hasło musi mieć co najmniej 8 znaków')
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Email jest wymagany')
        return value.strip()


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('Kod musi składać się z cyfr')
        if len(value) != 6:
            raise serializers.ValidationError('Kod musi mieć 6 cyfr')
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('Kod musi składać się z cyfr')
        if len(value) != 6:
            raise serializers.ValidationError('Kod musi mieć 6 cyfr')
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Hasło musi mieć co najmniej 8 znaków')
        return value