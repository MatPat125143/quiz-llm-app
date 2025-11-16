from llm_integration.difficulty_adapter import DifficultyAdapter
from core.exceptions import DifficultyAdaptationError


class DifficultyService:

    def __init__(self):
        self.adapter = DifficultyAdapter()

    def adapt_difficulty(self, session, is_correct, response_time):
        if not session.use_adaptive_difficulty:
            return session.current_difficulty

        try:
            new_difficulty = self.adapter.adjust_difficulty(
                current_difficulty=session.current_difficulty,
                is_correct=is_correct,
                response_time=response_time,
                time_limit=session.time_per_question,
                current_streak=session.current_streak or 0
            )

            if new_difficulty != session.current_difficulty:
                session.current_difficulty = new_difficulty
                session.save(update_fields=['current_difficulty'])

            return new_difficulty

        except Exception as e:
            raise DifficultyAdaptationError(detail=f'Błąd adaptacji trudności: {str(e)}')

    @staticmethod
    def get_difficulty_progression(session):
        from quiz_app.models import QuizSessionQuestion, Answer

        session_questions = QuizSessionQuestion.objects.filter(
            session=session,
            answered_at__isnull=False
        ).select_related('question').prefetch_related('answer_set').order_by('answered_at')

        progression = []

        for sq in session_questions:
            answer = sq.answer_set.first()

            if answer:
                progression.append({
                    'question_number': len(progression) + 1,
                    'difficulty': sq.question.difficulty_level,
                    'is_correct': answer.is_correct,
                    'response_time': answer.response_time,
                })

        return progression

    @staticmethod
    def should_increase_difficulty(session):
        if session.current_streak >= 3:
            return True

        recent_count = 5
        from quiz_app.models import QuizSessionQuestion

        recent_questions = QuizSessionQuestion.objects.filter(
            session=session,
            answered_at__isnull=False
        ).select_related('question').prefetch_related('answer_set').order_by('-answered_at')[:recent_count]

        if recent_questions.count() < recent_count:
            return False

        correct_count = sum(
            1 for sq in recent_questions
            if sq.answer_set.first() and sq.answer_set.first().is_correct
        )

        return correct_count >= 4

    @staticmethod
    def should_decrease_difficulty(session):
        if session.current_streak == 0 and session.total_questions > 0:
            recent_count = 3
            from quiz_app.models import QuizSessionQuestion

            recent_questions = QuizSessionQuestion.objects.filter(
                session=session,
                answered_at__isnull=False
            ).select_related('question').prefetch_related('answer_set').order_by('-answered_at')[:recent_count]

            if recent_questions.count() < recent_count:
                return False

            wrong_count = sum(
                1 for sq in recent_questions
                if sq.answer_set.first() and not sq.answer_set.first().is_correct
            )

            return wrong_count >= 2

        return False