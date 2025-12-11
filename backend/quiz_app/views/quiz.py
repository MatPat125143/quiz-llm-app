from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import QuizSession, Answer, QuizSessionQuestion, Question
from ..services.background_generator import BackgroundQuestionGenerator
from llm_integration.difficulty_adapter import DifficultyAdapter
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request):
    topic = request.data.get('topic')
    subtopic = request.data.get('subtopic', '')
    knowledge_level = request.data.get('knowledge_level', 'high_school')
    difficulty = request.data.get('difficulty', 'medium')
    questions_count = request.data.get('questions_count', 10)
    time_per_question = request.data.get('time_per_question', 30)
    use_adaptive_difficulty = request.data.get('use_adaptive_difficulty', True)

    questions_count = min(max(int(questions_count), 5), 20)
    time_per_question = min(max(int(time_per_question), 10), 60)

    difficulty_map_text = {
        'easy': 'łatwy',
        'medium': 'średni',
        'hard': 'trudny'
    }
    difficulty_text = difficulty_map_text.get(difficulty, 'średni')

    difficulty_adapter = DifficultyAdapter()
    initial_difficulty = difficulty_adapter.get_initial_difficulty(difficulty_text)

    logger.info(f"Starting quiz: topic={topic}, difficulty={difficulty_text} ({initial_difficulty})")

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

    logger.info(f"Quiz session {session.id} created for user {request.user.id}")

    bg_generator = BackgroundQuestionGenerator()

    sync_count = min(3, questions_count)
    logger.debug(f"Generating {sync_count} questions synchronously, {questions_count} total")

    try:
        initial_questions = bg_generator.generate_initial_questions_sync(session, count=sync_count)
        logger.info(f"Generated {len(initial_questions)} initial questions for session {session.id}")

        if questions_count > sync_count:
            remaining = questions_count - len(initial_questions)
            logger.info(f"Starting background generation for {remaining} remaining questions")
            bg_generator.generate_remaining_questions_async(
                session_id=session.id,
                total_needed=questions_count,
                already_generated=len(initial_questions)
            )

    except Exception as e:
        logger.error(f"Failed to generate initial questions for session {session.id}: {e}")
        session.delete()
        return Response({
            'error': 'Failed to generate initial questions',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
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
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_quiz(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if session.total_questions < session.questions_count:
        print(f"🗑️ Deleting incomplete session {session.id}")

        # Pobierz wszystkie pytania z tej sesji
        session_question_ids = list(QuizSessionQuestion.objects.filter(
            session=session
        ).values_list('question_id', flat=True))

        # Usuń Answer i QuizSessionQuestion
        Answer.objects.filter(session=session).delete()
        QuizSessionQuestion.objects.filter(session=session).delete()
        session.delete()

        # Usuń orphaned questions (bez odpowiedzi, nie używane w innych sesjach)
        if session_question_ids:
            orphaned_questions = Question.objects.filter(
                id__in=session_question_ids,
                total_answers=0
            )

            for orphan_q in orphaned_questions:
                used_in_active = QuizSessionQuestion.objects.filter(
                    question=orphan_q,
                    session__is_completed=False
                ).exists()

                if not used_in_active:
                    print(f"🗑️ Deleting orphaned Question ID={orphan_q.id} (incomplete session)")
                    orphan_q.delete()

        return Response({'message': 'Incomplete quiz session deleted', 'deleted': True})

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