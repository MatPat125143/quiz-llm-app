from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quiz_app.services import QuizService, AnswerService
from quiz_app.serializers import QuizSessionListSerializer
from core.mixins import PaginationMixin
from core.exceptions import QuizNotFound, PermissionDenied
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    try:
        filters = {}

        topic = request.GET.get('topic')
        if topic:
            filters['topic'] = topic

        difficulty = request.GET.get('difficulty')
        if difficulty:
            filters['difficulty'] = difficulty

        queryset = QuizService.get_user_quiz_history(request.user, filters)

        mixin = PaginationMixin()
        data, pagination_meta = mixin.paginate_queryset(
            queryset,
            request,
            QuizSessionListSerializer
        )

        logger.debug(f"Quiz history accessed: user={request.user.id}, count={pagination_meta['count']}")

        return mixin.build_paginated_response(data, pagination_meta)

    except Exception as e:
        logger.error(f"Error in quiz history for user={request.user.id}: {str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać historii quizów'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_details(request, session_id):
    try:
        session = QuizService.get_session_details(session_id, request.user)

        statistics = AnswerService.calculate_detailed_statistics(session)

        from quiz_app.serializers import QuizSessionDetailSerializer
        session_data = QuizSessionDetailSerializer(session).data

        logger.debug(f"Quiz details accessed: session_id={session_id}, user={request.user.id}")

        return Response({
            'session': session_data,
            'statistics': statistics
        }, status=status.HTTP_200_OK)

    except QuizNotFound:
        raise
    except PermissionDenied:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz details for session_id={session_id}: {str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać szczegółów quizu'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )