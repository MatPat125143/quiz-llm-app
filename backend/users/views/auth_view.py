from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from ..services.auth_service import AuthService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')

    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)

        _, email_sent = AuthService.send_reset_code(user)

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
    except (DatabaseError, RuntimeError, TypeError, ValueError) as e:
        logger.error(f"Error in password reset request: {e}")
        return Response({
            'error': 'Failed to send reset code. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code(request):
    email = request.data.get('email')
    code = request.data.get('code')

    if not email or not code:
        return Response(
            {'error': 'Email and code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        if AuthService.verify_reset_code(user, code):
            return Response({'message': 'Code is valid'})
        return Response(
            {'error': 'Code has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid code'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_with_code(request):
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
        success, message = AuthService.reset_password(user, code, new_password)
        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Password reset successful. You can now login with your new password.'})

    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid code'},
            status=status.HTTP_400_BAD_REQUEST
        )


