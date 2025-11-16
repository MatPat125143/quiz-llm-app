from django.utils import timezone
from quiz_app.models import QuizSession, QuizSessionQuestion
from quiz_app.utils.validators import validate_quiz_parameters
from core.exceptions import QuizNotFound, QuizAlreadyCompleted, QuizSessionInactive


class QuizService:

    @staticmethod
    def create_quiz_session(user, topic, difficulty, questions_count, time_per_question,
                            use_adaptive_difficulty=False, subtopic='', knowledge_level='high_school'):

        validate_quiz_parameters({
            'topic': topic,
            'difficulty': difficulty,
            'questions_count': questions_count,
            'time_per_question': time_per_question,
            'knowledge_level': knowledge_level,
        })

        session = QuizSession.objects.create(
            user=user,
            topic=topic,
            subtopic=subtopic,
            knowledge_level=knowledge_level,
            difficulty=difficulty,
            current_difficulty=difficulty,
            questions_count=questions_count,
            time_per_question=time_per_question,
            use_adaptive_difficulty=use_adaptive_difficulty,
            is_completed=False,
        )

        return session

    @staticmethod
    def get_active_session(session_id, user):
        try:
            session = QuizSession.objects.get(id=session_id, user=user)
        except QuizSession.DoesNotExist:
            raise QuizNotFound()

        if session.is_completed:
            raise QuizAlreadyCompleted()

        return session

    @staticmethod
    def end_quiz_session(session_id, user):
        session = QuizService.get_active_session(session_id, user)

        session.is_completed = True
        session.completed_at = timezone.now()

        total_answered = QuizSessionQuestion.objects.filter(
            session=session,
            answered_at__isnull=False
        ).count()

        session.total_questions = total_answered
        session.save()

        return session

    @staticmethod
    def calculate_session_statistics(session):
        total_questions = session.total_questions or 0
        correct_answers = session.correct_answers or 0

        if total_questions == 0:
            score_percentage = 0.0
        else:
            score_percentage = round((correct_answers / total_questions) * 100, 2)

        return {
            'session_id': session.id,
            'topic': session.topic,
            'subtopic': session.subtopic,
            'difficulty': session.difficulty,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'wrong_answers': total_questions - correct_answers,
            'score_percentage': score_percentage,
            'current_streak': session.current_streak or 0,
            'best_streak': session.best_streak or 0,
            'completed_at': session.completed_at,
            'use_adaptive_difficulty': session.use_adaptive_difficulty,
        }

    @staticmethod
    def get_user_quiz_history(user, filters=None):
        queryset = QuizSession.objects.filter(user=user, is_completed=True)

        if filters:
            if filters.get('topic'):
                queryset = queryset.filter(topic__icontains=filters['topic'])

            if filters.get('difficulty'):
                queryset = queryset.filter(difficulty=filters['difficulty'])

            if filters.get('start_date'):
                queryset = queryset.filter(created_at__gte=filters['start_date'])

            if filters.get('end_date'):
                queryset = queryset.filter(created_at__lte=filters['end_date'])

        return queryset.order_by('-created_at')

    @staticmethod
    def get_session_details(session_id, user):
        try:
            session = QuizSession.objects.select_related('user').get(id=session_id)
        except QuizSession.DoesNotExist:
            raise QuizNotFound()

        if session.user != user and (not hasattr(user, 'profile') or user.profile.role != 'admin'):
            from core.exceptions import PermissionDenied
            raise PermissionDenied()

        return session

    @staticmethod
    def check_session_progress(session):
        answered_questions = QuizSessionQuestion.objects.filter(
            session=session,
            answered_at__isnull=False
        ).count()

        remaining_questions = session.questions_count - answered_questions

        return {
            'answered': answered_questions,
            'remaining': max(remaining_questions, 0),
            'total': session.questions_count,
            'is_complete': answered_questions >= session.questions_count,
        }