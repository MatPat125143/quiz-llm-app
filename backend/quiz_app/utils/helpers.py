
"""
Funkcje pomocnicze dla quiz_app
"""
import random


def build_question_payload(session, question, generation_status):
    """
    Buduje payload z pytaniem dla API.

    Args:
        session: QuizSession object
        question: Question object
        generation_status: str - status generowania ('pre_generated', 'cached', 'generated')

    Returns:
        dict: Payload z pytaniem gotowy do Response
    """
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