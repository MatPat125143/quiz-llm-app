from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quiz_app.services import AnswerService, DifficultyService
from quiz_app.serializers import AnswerSubmitSerializer
from core.exceptions import QuestionNotFound, InvalidAnswerError, AnswerAlreadySubmitted, ValidationException
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    serializer = AnswerSubmitSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationException(field_errors=serializer.errors)

    validated_data = serializer.validated_data

    try:
        result = AnswerService.submit_answer(
            user=request.user,
            question_id=validated_data['question_id'],
            selected_answer=validated_data['selected_answer'],
            response_time=validated_data.get('response_time', 0)
        )

        logger.info(
            f"Answer submitted: user={request.user.id}, question={validated_data['question_id']}, "
            f"correct={result['is_correct']}, session={result['session_id']}"
        )

        try:
            from quiz_app.models import QuizSession
            session = QuizSession.objects.get(id=result['session_id'])

            if session.use_adaptive_difficulty:
                difficulty_service = DifficultyService()
                new_difficulty = difficulty_service.adapt_difficulty(
                    session=session,
                    is_correct=result['is_correct'],
                    response_time=validated_data.get('response_time', 0)
                )
                logger.debug(f"Difficulty adapted: session={session.id}, new_difficulty={new_difficulty}")

        except Exception as e:
            logger.warning(f"Failed to adapt difficulty for session={result['session_id']}: {str(e)}")

        return Response(result, status=status.HTTP_200_OK)

    except QuestionNotFound:
        raise
    except InvalidAnswerError:
        raise
    except AnswerAlreadySubmitted:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer for user={request.user.id}: {str(e)}")
        return Response(
            {'error': 'Nie udało się zapisać odpowiedzi'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )