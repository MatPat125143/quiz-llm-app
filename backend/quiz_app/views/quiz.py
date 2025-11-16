from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quiz_app.services import QuizService, QuestionService
from quiz_app.serializers import QuizSessionSerializer, QuizSessionCreateSerializer
from core.exceptions import QuizNotFound, QuizAlreadyCompleted, ValidationException
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request):
    serializer = QuizSessionCreateSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    validated_data = serializer.validated_data

    try:
        session = QuizService.create_quiz_session(
            user=request.user,
            topic=validated_data['topic'],
            difficulty=validated_data['difficulty'],
            questions_count=validated_data['questions_count'],
            time_per_question=validated_data['time_per_question'],
            use_adaptive_difficulty=validated_data.get('use_adaptive_difficulty', False),
            subtopic=validated_data.get('subtopic', ''),
            knowledge_level=validated_data.get('knowledge_level', 'high_school')
        )

        logger.info(f"Quiz started: session_id={session.id}, user={request.user.id}, topic={validated_data['topic']}")

        question_service = QuestionService()

        try:
            first_question = question_service.get_next_question(session)
            logger.debug(f"First question generated: question_id={first_question.id}, session_id={session.id}")
        except Exception as e:
            logger.error(f"Failed to generate first question for session_id={session.id}: {str(e)}")

        return Response({
            'session_id': session.id,
            'message': 'Quiz rozpoczęty pomyślnie',
            'topic': session.topic,
            'subtopic': session.subtopic,
            'knowledge_level': session.knowledge_level,
            'difficulty': session.initial_difficulty,
            'questions_count': session.questions_count,
            'time_per_question': session.time_per_question,
            'use_adaptive_difficulty': session.use_adaptive_difficulty
        }, status=status.HTTP_201_CREATED)

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error starting quiz for user={request.user.id}: {str(e)}")
        return Response(
            {'error': 'Nie udało się rozpocząć quizu'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_quiz(request, session_id):
    try:
        session = QuizService.end_quiz_session(session_id, request.user)

        logger.info(
            f"Quiz ended: session_id={session.id}, user={request.user.id}, score={session.correct_answers}/{session.total_questions}")

        statistics = QuizService.calculate_session_statistics(session)

        return Response({
            'message': 'Quiz zakończony pomyślnie',
            'statistics': statistics
        }, status=status.HTTP_200_OK)

    except QuizNotFound:
        raise
    except QuizAlreadyCompleted:
        raise
    except Exception as e:
        logger.error(f"Error ending quiz session_id={session_id}: {str(e)}")
        return Response(
            {'error': 'Nie udało się zakończyć quizu'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )