from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from ..serializers.user import UserSerializer,UpdateProfileSerializer
from ..serializers.profile import ChangePasswordSerializer, AvatarSerializer


User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Pobierz dane zalogowanego użytkownika"""
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Aktualizuj email i username"""
    serializer = UpdateProfileSerializer(
        request.user,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(request.user, context={'request': request}).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Zmień hasło (wymaga zalogowania i znajomości obecnego hasła)"""
    serializer = ChangePasswordSerializer(data=request.data)

    if serializer.is_valid():
        user = request.user

        # Sprawdź stare hasło
        if not user.check_password(serializer.data.get('old_password')):
            return Response(
                {'old_password': ['Wrong password.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ustaw nowe hasło
        user.set_password(serializer.data.get('new_password'))
        user.save()

        return Response({
            'message': 'Password updated successfully'
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== AVATAR MANAGEMENT (CHRONIONE) ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    """Upload avatara użytkownika"""
    profile = request.user.profile
    serializer = AvatarSerializer(profile, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Avatar uploaded successfully',
            'avatar_url': request.build_absolute_uri(profile.avatar.url) if profile.avatar else None
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar(request):
    """Usuń avatar użytkownika"""
    profile = request.user.profile

    if profile.avatar:
        profile.avatar.delete()
        profile.save()
        return Response({'message': 'Avatar deleted successfully'})

    return Response(
        {'message': 'No avatar to delete'},
        status=status.HTTP_400_BAD_REQUEST
    )