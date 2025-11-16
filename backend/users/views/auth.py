from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from users.services import AuthService
from users.serializers import (
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer
)
from core.exceptions import InvalidPasswordResetCode, ValidationException
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    serializer = PasswordResetRequestSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    try:
        email = serializer.validated_data['email']
        AuthService.request_password_reset(email)

        logger.info(f"Password reset requested for email: {email}")

        return Response({
            'message': 'Jeśli konto o podanym adresie email istnieje, kod resetowania został wysłany'
        }, status=status.HTTP_200_OK)

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error requesting password reset: error={str(e)}")
        return Response(
            {'error': 'Nie udało się wysłać kodu resetowania. Spróbuj ponownie później.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code(request):
    serializer = PasswordResetVerifySerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    try:
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        AuthService.verify_reset_code(email, code)

        logger.info(f"Password reset code verified: email={email}")

        return Response({
            'message': 'Kod jest prawidłowy'
        }, status=status.HTTP_200_OK)

    except InvalidPasswordResetCode:
        raise
    except Exception as e:
        logger.error(f"Error verifying reset code: error={str(e)}")
        return Response(
            {'error': 'Wystąpił błąd podczas weryfikacji kodu'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_with_code(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    try:
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        AuthService.reset_password_with_code(email, code, new_password)

        logger.info(f"Password reset successful: email={email}")

        return Response({
            'message': 'Hasło zostało zresetowane pomyślnie. Możesz się teraz zalogować.'
        }, status=status.HTTP_200_OK)

    except InvalidPasswordResetCode:
        raise
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: error={str(e)}")
        return Response(
            {'error': 'Nie udało się zresetować hasła'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )