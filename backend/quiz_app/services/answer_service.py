from django.utils import timezone
from django.db.models import F
from quiz_app.models import QuizSession, Question, QuizSessionQuestion, Answer
from core.exceptions import QuestionNotFound, InvalidAnswerError, AnswerAlreadySubmitted


class AnswerService:

    @staticmethod
    def submit_answer(user, question_id, selected_answer, response_time=0):
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise QuestionNotFound()

        session_question = QuizSessionQuestion.objects.filter(
            question=question,
            session__user=user,
            session__is_completed=False
        ).select_related('session').first()

        if not session_question:
            raise InvalidAnswerError(detail='Pytanie nie należy do aktywnej sesji')

        if session_question.answered_at:
            raise AnswerAlreadySubmitted()

        session = session_question.session
        is_correct = selected_answer == question.correct_answer

        answer = Answer.objects.create(
            session_question=session_question,
            selected_answer=selected_answer,
            is_correct=is_correct,
            response_time=response_time
        )

        session_question.answered_at = timezone.now()
        session_question.save()

        AnswerService._update_session_statistics(session, is_correct)
        AnswerService._update_question_statistics(question, is_correct, response_time)

        return {
            'is_correct': is_correct,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
            'current_streak': session.current_streak,
            'correct_answers': session.correct_answers,
            'total_questions': session.total_questions,
            'session_id': session.id,
        }

    @staticmethod
    def _update_session_statistics(session, is_correct):
        session.total_questions = F('total_questions') + 1

        if is_correct:
            session.correct_answers = F('correct_answers') + 1
            session.current_streak = F('current_streak') + 1

            session.save()
            session.refresh_from_db()

            if session.current_streak > (session.best_streak or 0):
                session.best_streak = session.current_streak
                session.save(update_fields=['best_streak'])
        else:
            session.current_streak = 0
            session.save()
            session.refresh_from_db()

    @staticmethod
    def _update_question_statistics(question, is_correct, response_time):
        question.times_used = F('times_used') + 1

        if is_correct:
            question.times_correct = F('times_correct') + 1

        question.save()
        question.refresh_from_db()

        if question.times_used > 0:
            question.success_rate = (question.times_correct / question.times_used) * 100
            question.save(update_fields=['success_rate'])

    @staticmethod
    def get_session_answers(session):
        session_questions = QuizSessionQuestion.objects.filter(
            session=session,
            answered_at__isnull=False
        ).select_related('question').prefetch_related('answer_set')

        answers_data = []

        for sq in session_questions:
            answer = sq.answer_set.first()

            if answer:
                answers_data.append({
                    'question_id': sq.question.id,
                    'question_text': sq.question.question_text,
                    'selected_answer': answer.selected_answer,
                    'correct_answer': sq.question.correct_answer,
                    'is_correct': answer.is_correct,
                    'explanation': sq.question.explanation,
                    'response_time': answer.response_time,
                    'difficulty': sq.question.difficulty_level,
                })

        return answers_data

    @staticmethod
    def calculate_detailed_statistics(session):
        answers = AnswerService.get_session_answers(session)

        total_questions = len(answers)
        correct_count = sum(1 for a in answers if a['is_correct'])
        wrong_count = total_questions - correct_count

        total_time = sum(a['response_time'] for a in answers)
        avg_time = total_time / total_questions if total_questions > 0 else 0

        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0

        difficulty_breakdown = {}
        for answer in answers:
            diff = answer['difficulty']
            if diff not in difficulty_breakdown:
                difficulty_breakdown[diff] = {'correct': 0, 'total': 0}

            difficulty_breakdown[diff]['total'] += 1
            if answer['is_correct']:
                difficulty_breakdown[diff]['correct'] += 1

        return {
            'total_questions': total_questions,
            'correct_answers': correct_count,
            'wrong_answers': wrong_count,
            'score_percentage': round(score_percentage, 2),
            'total_time': total_time,
            'average_time': round(avg_time, 2),
            'best_streak': session.best_streak or 0,
            'difficulty_breakdown': difficulty_breakdown,
            'answers': answers,
        }