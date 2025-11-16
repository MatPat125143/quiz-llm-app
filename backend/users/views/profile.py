from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.services import UserService
from users.serializers import (
    UserSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer
)
from core.exceptions import ValidationException
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    try:
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting current user: user_id={request.user.id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać danych użytkownika'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UpdateProfileSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    try:
        updated_user = UserService.update_profile(request.user, serializer.validated_data)

        response_serializer = UserSerializer(updated_user, context={'request': request})

        return Response({
            'message': 'Profil zaktualizowany pomyślnie',
            'user': response_serializer.data
        }, status=status.HTTP_200_OK)

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: user_id={request.user.id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się zaktualizować profilu'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    try:
        UserService.change_password(
            user=request.user,
            old_password=serializer.validated_data['old_password'],
            new_password=serializer.validated_data['new_password']
        )

        logger.info(f"Password changed successfully: user_id={request.user.id}")

        return Response({
            'message': 'Hasło zmienione pomyślnie'
        }, status=status.HTTP_200_OK)

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: user_id={request.user.id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się zmienić hasła'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )