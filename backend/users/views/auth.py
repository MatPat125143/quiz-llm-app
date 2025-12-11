from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from ..models import PasswordResetToken
from ..services.email_service import email_service
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


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

        PasswordResetToken.objects.filter(user=user, used=False).delete()

        code = PasswordResetToken.generate_code()
        PasswordResetToken.objects.create(user=user, code=code)

        email_sent = email_service.send_password_reset_email(email, code)

        if not email_sent:
            logger.error(f"Failed to send password reset email to {email}")
            return Response({
                'error': 'Failed to send reset code. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'message': 'Password reset code sent to your email'
        })

    except User.DoesNotExist:
        return Response({
            'message': 'If an account with that email exists, a reset code has been sent'
        })
    except Exception as e:
        logger.error(f"Error in password reset request: {e}")
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