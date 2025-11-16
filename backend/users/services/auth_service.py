from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from users.models import PasswordResetToken
from core.exceptions import UserNotFound, InvalidPasswordResetCode, ValidationException
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def request_password_reset(email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return True

        PasswordResetToken.objects.filter(user=user, used=False).delete()

        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=user, code=code)

        try:
            send_mail(
                subject='Kod resetowania hasła - Quiz App',
                message=f'Twój kod resetowania hasła to: {code}\n\nKod wygaśnie za 1 godzinę.\n\nJeśli to nie Ty, zignoruj tę wiadomość.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            logger.info(f"Password reset email sent: user_id={user.id}, email={email}")

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            raise ValidationException(detail='Nie udało się wysłać kodu. Spróbuj ponownie później.')

        return True

    @staticmethod
    def verify_reset_code(email, code):
        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.objects.filter(
                user=user,
                code=code,
                used=False
            ).latest('created_at')

            if not token.is_valid():
                raise InvalidPasswordResetCode(detail='Kod wygasł. Poproś o nowy kod.')

            return True

        except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
            raise InvalidPasswordResetCode(detail='Nieprawidłowy kod')

    @staticmethod
    def reset_password_with_code(email, code, new_password):
        if len(new_password) < 8:
            raise ValidationException(detail='Hasło musi mieć co najmniej 8 znaków')

        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.objects.filter(
                user=user,
                code=code,
                used=False
            ).latest('created_at')

            if not token.is_valid():
                raise InvalidPasswordResetCode(detail='Kod wygasł. Poproś o nowy kod.')

            user.set_password(new_password)
            user.save()

            token.used = True
            token.save()

            logger.info(f"Password reset successful: user_id={user.id}, email={email}")

            return True

        except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
            raise InvalidPasswordResetCode(detail='Nieprawidłowy kod')