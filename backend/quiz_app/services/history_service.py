from ..models import Answer
from ..serializers.answer_serializer import AnswerDetailSerializer


def build_quiz_details_payload(session, request_user):
    answers = Answer.objects.filter(
        session=session,
        user=session.user
    ).select_related('question').order_by('answered_at')

    answers_data = AnswerDetailSerializer(answers, many=True).data

    difficulty_progress = []
    if session.use_adaptive_difficulty:
        for ans in answers:
            difficulty_progress.append({
                'difficulty': ans.difficulty_at_answer,
                'is_correct': ans.is_correct
            })

    user_info = None
    if request_user.profile.role == 'admin':
        user_info = {
            'username': session.user.username,
            'email': session.user.email,
            'user_id': session.user.id
        }

    return {
        'session': {
            'id': session.id,
            'topic': session.topic,
            'subtopic': session.subtopic,
            'knowledge_level': session.knowledge_level,
            'difficulty': session.initial_difficulty,
            'questions_count': session.questions_count,
            'time_per_question': session.time_per_question,
            'use_adaptive_difficulty': session.use_adaptive_difficulty,
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'accuracy': session.accuracy,
            'started_at': session.started_at,
            'ended_at': session.ended_at,
            'completed_at': session.ended_at,
            'user_info': user_info,
        },
        'answers': answers_data,
        'difficulty_progress': difficulty_progress
    }


