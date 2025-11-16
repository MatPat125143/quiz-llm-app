from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quiz_app.services import QuizService, QuestionService
from quiz_app.serializers import QuestionListSerializer
from quiz_app.utils.helpers import build_question_filters
from core.mixins import PaginationMixin
from core.exceptions import QuizNotFound, QuizAlreadyCompleted, QuestionGenerationError
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question(request, session_id):
    try:
        session = QuizService.get_active_session(session_id, request.user)

        progress = QuizService.check_session_progress(session)

        if progress['is_complete']:
            return Response({
                'message': 'Quiz został ukończony',
                'session_completed': True,
                'statistics': QuizService.calculate_session_statistics(session)
            }, status=status.HTTP_200_OK)

        question_service = QuestionService()

        try:
            question = question_service.get_next_question(session)
            logger.debug(f"Question retrieved: question_id={question.id}, session_id={session_id}")

        except QuestionGenerationError as e:
            logger.error(f"Failed to generate question for session_id={session_id}: {str(e)}")
            raise

        response_data = question_service.format_question_response(question, session)
        response_data['generation_status'] = 'ready'

        return Response(response_data, status=status.HTTP_200_OK)

    except QuizNotFound:
        raise
    except QuizAlreadyCompleted:
        raise
    except QuestionGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error getting question for session_id={session_id}: {str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać pytania'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questions_library(request):
    try:
        filters = build_question_filters(request)

        question_service = QuestionService()
        queryset = question_service.get_questions_library(filters, request.user)

        mixin = PaginationMixin()
        data, pagination_meta = mixin.paginate_queryset(
            queryset,
            request,
            QuestionListSerializer
        )

        logger.debug(
            f"Questions library accessed: user={request.user.id}, filters={filters}, count={pagination_meta['count']}")

        return mixin.build_paginated_response(data, pagination_meta)

    except Exception as e:
        logger.error(f"Error in questions library for user={request.user.id}: {str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać biblioteki pytań'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )