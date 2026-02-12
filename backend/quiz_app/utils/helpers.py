import random
from ..models import Question, Answer, QuizSessionQuestion


def build_question_payload(session, question, generation_status):
    answers = [
        question.correct_answer,
        question.wrong_answer_1,
        question.wrong_answer_2,
        question.wrong_answer_3
    ]
    random.shuffle(answers)

    question_number = min(session.total_questions + 1, session.questions_count)
    questions_remaining = max(session.questions_count - session.total_questions, 0)

    return {
        'question_id': question.id,
        'question_text': question.question_text,
        'topic': session.topic,
        'answers': answers,
        'option_a': answers[0],
        'option_b': answers[1],
        'option_c': answers[2],
        'option_d': answers[3],
        'current_difficulty': session.current_difficulty,
        'question_number': question_number,
        'questions_count': session.questions_count,
        'questions_remaining': questions_remaining,
        'time_per_question': session.time_per_question,
        'use_adaptive_difficulty': session.use_adaptive_difficulty,
        'generation_status': generation_status,
        'difficulty_label': question.difficulty_level,
        'times_used': question.times_used,
        'success_rate': question.success_rate,
    }


def get_used_question_refs(session):
    answered_question_ids = Answer.objects.filter(
        session=session,
        user=session.user
    ).values_list('question_id', flat=True)

    answered_texts = Answer.objects.filter(
        session=session,
        user=session.user
    ).values_list('question__question_text', flat=True)

    used_hashes = set(
        Question.objects.filter(id__in=answered_question_ids).values_list('content_hash', flat=True)
    )

    return answered_question_ids, answered_texts, used_hashes


def get_used_hashes(session):
    session_hashes = QuizSessionQuestion.objects.filter(
        session=session
    ).values_list('question__content_hash', flat=True)
    answer_hashes = Answer.objects.filter(
        session=session
    ).values_list('question__content_hash', flat=True)
    return set(session_hashes) | set(answer_hashes)
