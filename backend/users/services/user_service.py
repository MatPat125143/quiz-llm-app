from django.contrib.auth import get_user_model
from users.models import UserProfile
from core.exceptions import UserNotFound, ValidationException
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:

    @staticmethod
    def get_user_by_id(user_id):
        try:
            return User.objects.select_related('profile').get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFound()

    @staticmethod
    def get_user_by_email(email):
        try:
            return User.objects.select_related('profile').get(email=email)
        except User.DoesNotExist:
            raise UserNotFound()

    @staticmethod
    def update_profile(user, data):
        if 'email' in data:
            if User.objects.exclude(pk=user.pk).filter(email=data['email']).exists():
                raise ValidationException(detail='Ten email jest już używany')
            user.email = data['email']

        if 'username' in data:
            if User.objects.exclude(pk=user.pk).filter(username=data['username']).exists():
                raise ValidationException(detail='Ta nazwa użytkownika jest już używana')
            user.username = data['username']

        user.save()
        logger.info(f"Profile updated: user_id={user.id}")

        return user

    @staticmethod
    def change_password(user, old_password, new_password):
        if not user.check_password(old_password):
            raise ValidationException(detail='Nieprawidłowe stare hasło')

        if len(new_password) < 8:
            raise ValidationException(detail='Hasło musi mieć co najmniej 8 znaków')

        user.set_password(new_password)
        user.save()

        logger.info(f"Password changed: user_id={user.id}")

        return True

    @staticmethod
    def upload_avatar(user, avatar_file):
        profile = user.profile

        if profile.avatar:
            profile.avatar.delete()

        profile.avatar = avatar_file
        profile.save()

        logger.info(f"Avatar uploaded: user_id={user.id}")

        return profile

    @staticmethod
    def delete_avatar(user):
        profile = user.profile

        if not profile.avatar:
            raise ValidationException(detail='Brak avatara do usunięcia')

        profile.avatar.delete()
        profile.save()

        logger.info(f"Avatar deleted: user_id={user.id}")

        return True

    @staticmethod
    def update_profile_statistics(user, quiz_session):
        profile = user.profile

        profile.total_quizzes_played += 1
        profile.total_questions_answered += quiz_session.total_questions
        profile.total_correct_answers += quiz_session.correct_answers

        if quiz_session.best_streak > profile.highest_streak:
            profile.highest_streak = quiz_session.best_streak

        profile.save()

        logger.debug(f"Profile stats updated: user_id={user.id}")

        return profile