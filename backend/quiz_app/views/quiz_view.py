import logging

from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cache_manager import QuizCacheService
from llm_integration.difficulty_adapter import DifficultyAdapter

from ..models import QuizSession
from ..services.background_generation_service import BackgroundGenerationService
from ..services.cleanup_service import rollback_session
from ..utils.constants import (
    DEFAULT_QUESTIONS_COUNT,
    DEFAULT_TIME_PER_QUESTION,
    DEFAULT_USE_ADAPTIVE_DIFFICULTY,
    QUESTIONS_COUNT_MIN,
    QUESTIONS_COUNT_MAX,
    TIME_PER_QUESTION_MIN,
    TIME_PER_QUESTION_MAX,
    DIFFICULTY_NAME_MAP,
    SYNC_QUESTION_COUNT,
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request):
    topic = request.data.get('topic')
    subtopic = request.data.get('subtopic', '')
    knowledge_level = request.data.get('knowledge_level', 'high_school')
    difficulty = request.data.get('difficulty', 'medium')
    questions_count = request.data.get('questions_count', DEFAULT_QUESTIONS_COUNT)
    time_per_question = request.data.get('time_per_question', DEFAULT_TIME_PER_QUESTION)
    use_adaptive_difficulty = request.data.get(
        'use_adaptive_difficulty',
        DEFAULT_USE_ADAPTIVE_DIFFICULTY
    )

    questions_count = min(
        max(int(questions_count), QUESTIONS_COUNT_MIN),
        QUESTIONS_COUNT_MAX
    )
    time_per_question = min(
        max(int(time_per_question), TIME_PER_QUESTION_MIN),
        TIME_PER_QUESTION_MAX
    )

    difficulty_text = DIFFICULTY_NAME_MAP.get(difficulty, 'średni')

    difficulty_adapter = DifficultyAdapter()
    initial_difficulty = difficulty_adapter.get_initial_difficulty(difficulty_text)

    logger.info(
        "Starting quiz: topic=%s, difficulty=%s (%s)",
        topic,
        difficulty_text,
        initial_difficulty
    )

    open_sessions = QuizSession.objects.filter(
        user=request.user,
        is_completed=False
    )
    for open_s in open_sessions:
        try:
            QuizCacheService.clear_session_cache(open_s.id)
            rollback_session(open_s)
        except (DatabaseError, OSError, RuntimeError, TypeError, ValueError) as e:
            logger.warning(
                "Failed to rollback previous open session %s: %s",
                open_s.id,
                e
            )

    session = QuizSession.objects.create(
        user=request.user,
        topic=topic,
        subtopic=subtopic if subtopic else None,
        knowledge_level=knowledge_level,
        initial_difficulty=difficulty,
        current_difficulty=initial_difficulty,
        questions_count=questions_count,
        time_per_question=time_per_question,
        use_adaptive_difficulty=use_adaptive_difficulty,
        questions_generated_count=0
    )

    logger.info(
        "Quiz session %s created for user %s",
        session.id,
        request.user.id
    )

    bg_generator = BackgroundGenerationService()

    sync_count = min(SYNC_QUESTION_COUNT, questions_count)
    logger.debug(
        "Generating %s questions synchronously, %s total",
        sync_count,
        questions_count
    )

    try:
        initial_questions = bg_generator.generate_initial_questions_sync(
            session, count=sync_count
        )
        logger.info(
            "Generated %s initial questions for session %s",
            len(initial_questions),
            session.id
        )

        if questions_count > sync_count:
            remaining = questions_count - len(initial_questions)
            logger.info(
                "Starting background generation for %s remaining questions",
                remaining
            )
            bg_generator.generate_remaining_questions_async(
                session_id=session.id,
                total_needed=questions_count,
                already_generated=len(initial_questions)
            )

    except (DatabaseError, RuntimeError, TypeError, ValueError) as e:
        logger.error(
            "Failed to generate initial questions for session %s: %s",
            session.id,
            e
        )
        session.delete()
        return Response(
            {
                'error': 'Failed to generate initial questions',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            'session_id': session.id,
            'message': 'Quiz started successfully!',
            'topic': topic,
            'subtopic': subtopic,
            'knowledge_level': knowledge_level,
            'difficulty': difficulty,
            'questions_count': questions_count,
            'time_per_question': time_per_question,
            'use_adaptive_difficulty': use_adaptive_difficulty,
            'questions_ready': len(initial_questions),
            'generating_in_background': questions_count > sync_count
        },
        status=status.HTTP_201_CREATED
    )




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_quiz(request, session_id):
    session = get_object_or_404(
        QuizSession,
        id=session_id,
        user=request.user
    )

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if session.total_questions < session.questions_count:
        logger.info("Deleting incomplete session %s", session.id)
        rollback_session(session)
        return Response({
            'message': 'Incomplete quiz session deleted',
            'deleted': True
        })

    session.ended_at = timezone.now()
    session.is_completed = True
    session.save()

    return Response({
        'message': 'Quiz ended successfully',
        'session_id': session.id,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'accuracy': session.accuracy,
        'deleted': False
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_quiz(request, session_id):
    session = get_object_or_404(
        QuizSession,
        id=session_id,
        user=request.user
    )

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        rollback_session(session)

    return Response({
        'message': 'Quiz session canceled and rolled back',
        'canceled': True
    })


