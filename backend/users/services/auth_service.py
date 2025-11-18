from django.core.mail import send_mail
from django.conf import settings
from ..models import PasswordResetToken


class AuthService:
    """Logika biznesowa dla autentykacji i resetowania hasła"""

    @staticmethod
    def send_reset_code(user):
        """Generuj i wyślij kod resetowania hasła"""
        # Usuń stare nieużyte tokeny
        PasswordResetToken.objects.filter(user=user, used=False).delete()

        # Wygeneruj nowy kod
        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=user, code=code)

        # Wyślij email
        send_mail(
            subject='Password Reset Code - Quiz App',
            message=f'Your password reset code is: {code}\n\nThis code will expire in 1 hour.\n\nIf you did not request this, please ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return token

    @staticmethod
    def verify_reset_code(user, code):
        """Weryfikuj kod resetowania hasła"""
        try:
            token = PasswordResetToken.objects.filter(
                user=user,
                code=code,
                used=False
            ).latest('created_at')

            return token.is_valid()
        except PasswordResetToken.DoesNotExist:
            return False

    @staticmethod
    def reset_password(user, code, new_password):
        """Resetuj hasło używając kodu"""
        try:
            token = PasswordResetToken.objects.filter(
                user=user,
                code=code,
                used=False
            ).latest('created_at')

            if not token.is_valid():
                return False, 'Code has expired'

            # Zmień hasło
            user.set_password(new_password)
            user.save()

            # Oznacz token jako użyty
            token.used = True
            token.save()

            return True, 'Password reset successful'

        except PasswordResetToken.DoesNotExist:
            return False, 'Invalid code'