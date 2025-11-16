from django.contrib.auth import get_user_model
from django.db.models import Q
from quiz_app.models import QuizSession, Question, Answer
from core.exceptions import UserNotFound, ValidationException, PermissionDenied
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AdminService:

    @staticmethod
    def get_dashboard_statistics():
        total_users = User.objects.count()
        total_quizzes = QuizSession.objects.count()
        total_questions = Question.objects.count()
        total_answers = Answer.objects.count()

        correct_answers = Answer.objects.filter(is_correct=True).count()
        avg_accuracy = round((correct_answers / total_answers * 100), 2) if total_answers > 0 else 0

        completed_quizzes = QuizSession.objects.filter(is_completed=True).count()
        active_users = User.objects.filter(is_active=True).count()

        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_quizzes': total_quizzes,
            'completed_quizzes': completed_quizzes,
            'total_questions': total_questions,
            'total_answers': total_answers,
            'avg_accuracy': avg_accuracy
        }

    @staticmethod
    def get_all_users():
        users = User.objects.select_related('profile').all().order_by('-date_joined')

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.profile.role,
                'total_quizzes': user.profile.total_quizzes_played,
                'accuracy': user.profile.accuracy,
                'joined': user.date_joined,
                'is_active': user.is_active
            })

        return users_data

    @staticmethod
    def search_users(query=None, role=None, is_active=None):
        users = User.objects.select_related('profile').all()

        if query:
            users = users.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )

        if role in ['admin', 'user']:
            users = users.filter(profile__role=role)

        if is_active is not None:
            users = users.filter(is_active=is_active)

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.profile.role,
                'total_quizzes': user.profile.total_quizzes_played,
                'accuracy': user.profile.accuracy,
                'joined': user.date_joined,
                'is_active': user.is_active
            })

        return users_data

    @staticmethod
    def get_user_quiz_history(user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFound()

        sessions = QuizSession.objects.filter(
            user=user,
            is_completed=True
        ).order_by('-ended_at')

        history_data = []
        for session in sessions:
            history_data.append({
                'id': session.id,
                'topic': session.topic,
                'subtopic': session.subtopic,
                'difficulty': session.initial_difficulty,
                'knowledge_level': session.knowledge_level,
                'use_adaptive_difficulty': session.use_adaptive_difficulty,
                'accuracy': session.accuracy,
                'correct_answers': session.correct_answers,
                'total_questions': session.total_questions,
                'started_at': session.started_at,
                'ended_at': session.ended_at,
            })

        return history_data

    @staticmethod
    def delete_user(user_id, requesting_user):
        if user_id == requesting_user.id:
            raise ValidationException(detail='Nie możesz usunąć samego siebie')

        try:
            user = User.objects.get(id=user_id)
            username = user.username
            user.delete()

            logger.info(f"User deleted: user_id={user_id}, by={requesting_user.id}")

            return username

        except User.DoesNotExist:
            raise UserNotFound()

    @staticmethod
    def toggle_user_status(user_id, requesting_user):
        if user_id == requesting_user.id:
            raise ValidationException(detail='Nie możesz dezaktywować swojego konta')

        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()

            logger.info(f"User status toggled: user_id={user_id}, is_active={user.is_active}, by={requesting_user.id}")

            return {
                'username': user.username,
                'is_active': user.is_active
            }

        except User.DoesNotExist:
            raise UserNotFound()

    @staticmethod
    def change_user_role(user_id, new_role):
        if new_role not in ['user', 'admin']:
            raise ValidationException(detail='Nieprawidłowa rola')

        try:
            user = User.objects.get(id=user_id)
            user.profile.role = new_role
            user.profile.save()

            logger.info(f"User role changed: user_id={user_id}, new_role={new_role}")

            return new_role

        except User.DoesNotExist:
            raise UserNotFound()

    @staticmethod
    def delete_quiz_session(session_id):
        try:
            session = QuizSession.objects.get(id=session_id)
            session.delete()

            logger.info(f"Quiz session deleted: session_id={session_id}")

            return True

        except QuizSession.DoesNotExist:
            from core.exceptions import QuizNotFound
            raise QuizNotFound()