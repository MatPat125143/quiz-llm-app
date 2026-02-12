from ..models import PasswordResetToken
from .email_service import email_service


class AuthService:

    @staticmethod
    def send_reset_code(user):

        PasswordResetToken.objects.filter(user=user, used=False).delete()

        code = PasswordResetToken.generate_code()
        token = PasswordResetToken.objects.create(user=user, code=code)

        email_sent = email_service.send_password_reset_email(user.email, code)

        return token, email_sent

    @staticmethod
    def verify_reset_code(user, code):
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
        try:
            token = PasswordResetToken.objects.filter(
                user=user,
                code=code,
                used=False
            ).latest('created_at')

            if not token.is_valid():
                return False, 'Code has expired'

            user.set_password(new_password)
            user.save()

            token.used = True
            token.save()

            return True, 'Password reset successful'

        except PasswordResetToken.DoesNotExist:
            return False, 'Invalid code'
