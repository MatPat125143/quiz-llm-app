import logging
from django.db import transaction, IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import Question, QuizSessionQuestion, Answer
from llm_integration.difficulty_adapter import DifficultyAdapter
from ..services.background_generation_service import BackgroundGenerationService
from ..services.answer_service import (
    handle_adaptive_difficulty_change,
    prefetch_next_question_cache,
    update_profile_stats_on_completion,
)
from ..services.cleanup_service import cleanup_unused_session_questions

logger = logging.getLogger(__name__)

difficulty_adapter = DifficultyAdapter()
bg_generator = BackgroundGenerationService()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    question_id = request.data.get('question_id')
    selected_answer = request.data.get('selected_answer')
    response_time = request.data.get('response_time', 0)

    question = get_object_or_404(Question, id=question_id)

    session_question = QuizSessionQuestion.objects.filter(
        question=question,
        session__user=request.user,
        session__is_completed=False
    ).select_related('session').first()

    if not session_question:
        return Response(
            {'error': 'Question not found in any active session'},
            status=status.HTTP_404_NOT_FOUND
        )

    session = session_question.session

    if session.is_completed:
        return Response({
            'error': 'Quiz already completed',
            'quiz_completed': True
        }, status=status.HTTP_400_BAD_REQUEST)

    if session.total_questions >= session.questions_count:
        session.is_completed = True
        session.ended_at = timezone.now()
        session.save()
        return Response({
            'error': 'Quiz limit reached',
            'quiz_completed': True,
            'session_stats': {
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'accuracy': session.accuracy
            }
        })

    is_timeout = not bool(selected_answer)

    existing_answer = Answer.objects.filter(
        question=question,
        user=request.user,
        session=session
    ).first()

    if existing_answer:
        return Response({
            'is_correct': existing_answer.is_correct,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
            'current_streak': session.current_streak,
            'quiz_completed': session.is_completed,
            'session_stats': {
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'accuracy': session.accuracy
            }
        })

    if selected_answer:
        selected_normalized = ' '.join(selected_answer.strip().split())
        correct_normalized = ' '.join(question.correct_answer.strip().split())
        is_correct = selected_normalized == correct_normalized

        if not is_correct:
            logger.debug(f"Wrong answer: '{selected_answer}' != '{question.correct_answer}'")
        else:
            logger.debug(f"Correct answer: '{selected_answer}'")
    else:
        is_correct = False

    try:
        with transaction.atomic():
            answer, created = Answer.objects.get_or_create(
                question=question,
                user=request.user,
                session=session,
                defaults={
                    'selected_answer': selected_answer or '',
                    'is_correct': is_correct,
                    'response_time': response_time,
                    'difficulty_at_answer': session.current_difficulty
                }
            )
    except IntegrityError:
        answer = Answer.objects.filter(
            question=question,
            user=request.user,
            session=session
        ).first()
        created = False

    if not created:
        return Response({
            'is_correct': answer.is_correct,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
            'current_streak': session.current_streak,
            'quiz_completed': session.is_completed,
            'session_stats': {
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'accuracy': session.accuracy
            }
        })

    session.total_questions += 1
    if session.total_questions > session.questions_count:
        session.total_questions = session.questions_count

    if is_correct:
        session.correct_answers += 1
        session.current_streak += 1
    else:
        session.current_streak = 0


    level_changed, previous_difficulty_level, new_difficulty_level = (
        handle_adaptive_difficulty_change(
            session=session,
            difficulty_adapter=difficulty_adapter,
            bg_generator=bg_generator,
        )
    )

    session.save()
    question.update_stats(is_correct)

    quiz_completed = session.total_questions >= session.questions_count

    if not quiz_completed:
        try:
            prefetch_next_question_cache(session)
        except (OSError, RuntimeError, TypeError, ValueError) as e:
            logger.debug(f"Prefetch cache failed for session {session.id}: {e}")

    if quiz_completed and not session.is_completed:
        session.is_completed = True
        session.ended_at = timezone.now()
        session.save()

        cleanup_unused_session_questions(session)

        update_profile_stats_on_completion(request.user)

        logger.info(f"Quiz {session.id} completed")

    return Response({
        'is_correct': is_correct,
        'was_timeout': is_timeout,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'current_streak': session.current_streak,
        'quiz_completed': quiz_completed,
        'difficulty_changed': level_changed,
        'previous_difficulty': previous_difficulty_level if level_changed else None,
        'new_difficulty': new_difficulty_level if level_changed else None,
        'session_stats': {
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'accuracy': session.accuracy
        },
        'question_stats': {
            'times_used': question.times_used,
            'success_rate': question.success_rate
        }
    })


