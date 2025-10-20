from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetToken
from .serializers import (
    UserSerializer,
    ChangePasswordSerializer,
    UpdateProfileSerializer,
    AvatarSerializer
)

User = get_user_model()


# ==================== USER PROFILE (CHRONIONE) ====================

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


# ==================== PASSWORD RESET (PUBLICZNE - BEZ LOGOWANIA) ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Krok 1: Wyślij 6-cyfrowy kod resetowania hasła na email.
    Nie wymaga logowania - publiczny endpoint.
    """
    email = request.data.get('email')

    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)

        # Usuń stare nieużyte tokeny tego usera
        PasswordResetToken.objects.filter(user=user, used=False).delete()

        # Wygeneruj i zapisz nowy token
        code = PasswordResetToken.generate_code()
        PasswordResetToken.objects.create(user=user, code=code)

        # Wyślij email z kodem
        send_mail(
            subject='Password Reset Code - Quiz App',
            message=f'Your password reset code is: {code}\n\nThis code will expire in 1 hour.\n\nIf you did not request this, please ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({
            'message': 'Password reset code sent to your email'
        })

    except User.DoesNotExist:
        # Security: Nie ujawniaj czy email istnieje w bazie
        return Response({
            'message': 'If an account with that email exists, a reset code has been sent'
        })
    except Exception as e:
        # Loguj błąd do konsoli (w produkcji użyj proper loggera)
        print(f"Error sending password reset email: {e}")
        return Response({
            'error': 'Failed to send reset code. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code(request):
    """
    Krok 2: Weryfikuj czy kod jest poprawny i nie wygasł.
    Nie wymaga logowania - publiczny endpoint.
    """
    email = request.data.get('email')
    code = request.data.get('code')

    if not email or not code:
        return Response(
            {'error': 'Email and code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        token = PasswordResetToken.objects.filter(
            user=user,
            code=code,
            used=False
        ).latest('created_at')

        if token.is_valid():
            return Response({'message': 'Code is valid'})
        else:
            return Response(
                {'error': 'Code has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
        return Response(
            {'error': 'Invalid code'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_with_code(request):
    """
    Krok 3: Resetuj hasło po weryfikacji kodu.
    Nie wymaga logowania - publiczny endpoint.
    """
    email = request.data.get('email')
    code = request.data.get('code')
    new_password = request.data.get('new_password')

    if not email or not code or not new_password:
        return Response(
            {'error': 'Email, code, and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters long'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        token = PasswordResetToken.objects.filter(
            user=user,
            code=code,
            used=False
        ).latest('created_at')

        # Sprawdź czy token jest ważny
        if not token.is_valid():
            return Response(
                {'error': 'Code has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Zmień hasło
        user.set_password(new_password)
        user.save()

        # Oznacz token jako użyty (nie można użyć ponownie)
        token.used = True
        token.save()

        return Response({
            'message': 'Password reset successful. You can now login with your new password.'
        })

    except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
        return Response(
            {'error': 'Invalid code'},
            status=status.HTTP_400_BAD_REQUEST
        )