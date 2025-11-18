from django.contrib.auth import get_user_model

User = get_user_model()


class UserService:
    """Logika biznesowa dla zarządzania użytkownikami"""

    @staticmethod
    def get_user_statistics(user):
        """Pobierz statystyki użytkownika"""
        return {
            'total_quizzes': user.profile.total_quizzes_played,
            'total_questions': user.profile.total_questions_answered,
            'correct_answers': user.profile.total_correct_answers,
            'highest_streak': user.profile.highest_streak,
            'accuracy': user.profile.accuracy
        }

    @staticmethod
    def update_user_stats(user):
        """Aktualizuj statystyki użytkownika na podstawie jego odpowiedzi"""
        from quiz_app.models import Answer, QuizSession

        profile = user.profile

        # Aktualizuj statystyki z ukończonych quizów
        completed_answers = Answer.objects.filter(
            user=user,
            session__is_completed=True
        )

        profile.total_questions_answered = completed_answers.count()
        profile.total_correct_answers = completed_answers.filter(is_correct=True).count()

        # Oblicz najdłuższą serię
        completed_sessions = QuizSession.objects.filter(user=user, is_completed=True)
        max_streak = 0
        for session in completed_sessions:
            session_answers = Answer.objects.filter(session=session).order_by('answered_at')
            current_streak = 0
            for ans in session_answers:
                if ans.is_correct:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0

        profile.highest_streak = max_streak
        profile.save()

        return profile