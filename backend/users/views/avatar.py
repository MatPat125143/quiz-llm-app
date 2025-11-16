from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from users.services import UserService
from users.serializers import AvatarSerializer
from core.exceptions import ValidationException
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    profile = request.user.profile
    serializer = AvatarSerializer(profile, data=request.data, partial=True, context={'request': request})

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    try:
        avatar_file = serializer.validated_data.get('avatar')

        if not avatar_file:
            raise ValidationException(detail='Plik avatara jest wymagany')

        updated_profile = UserService.upload_avatar(request.user, avatar_file)

        logger.info(f"Avatar uploaded: user_id={request.user.id}")

        avatar_url = None
        if updated_profile.avatar:
            avatar_url = request.build_absolute_uri(updated_profile.avatar.url)

        return Response({
            'message': 'Avatar został przesłany pomyślnie',
            'avatar_url': avatar_url
        }, status=status.HTTP_200_OK)

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: user_id={request.user.id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się przesłać avatara'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar(request):
    try:
        UserService.delete_avatar(request.user)

        logger.info(f"Avatar deleted: user_id={request.user.id}")

        return Response({
            'message': 'Avatar został usunięty pomyślnie'
        }, status=status.HTTP_200_OK)

    except ValidationException as e:
        return Response(
            {'error': str(e.detail)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error deleting avatar: user_id={request.user.id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się usunąć avatara'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )