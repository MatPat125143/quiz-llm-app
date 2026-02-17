import logging

from django.db.models import FloatField, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import QuizSession
from ..permissions import IsQuizOwnerOrAdmin
from ..serializers import QuizSessionSerializer
from ..utils.constants import (
    DEFAULT_QUESTIONS_COUNT,
    DEFAULT_TIME_PER_QUESTION,
    DEFAULT_USE_ADAPTIVE_DIFFICULTY,
)
from ..utils.pagination import paginate_queryset
from ..services.history_service import build_quiz_details_payload

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    qs = (
        QuizSession.objects.filter(user=request.user, is_completed=True)
        .annotate(
            total_response_time=Coalesce(
                Sum('answers__response_time'),
                Value(0.0),
                output_field=FloatField()
            )
        )
    )

    topic = request.GET.get('topic')
    difficulty = request.GET.get('difficulty')
    is_custom = request.GET.get('is_custom')

    if topic:
        qs = qs.filter(topic__icontains=topic)

    if difficulty in ['easy', 'medium', 'hard']:
        qs = qs.filter(initial_difficulty=difficulty)

    if is_custom in ['true', 'false']:
        ids = []
        for s in qs.only(
            'id', 'questions_count', 'time_per_question', 'use_adaptive_difficulty'
        ):
            custom = (
                s.questions_count != DEFAULT_QUESTIONS_COUNT
                or s.time_per_question != DEFAULT_TIME_PER_QUESTION
                or s.use_adaptive_difficulty != DEFAULT_USE_ADAPTIVE_DIFFICULTY
            )
            if (is_custom == 'true' and custom) or (is_custom == 'false' and not custom):
                ids.append(s.id)
        qs = qs.filter(id__in=ids)

    order_by = request.GET.get('order_by', '-started_at')
    allowed = [
        'started_at', '-started_at',
        'accuracy', '-accuracy',
        'topic', '-topic',
        'total_questions', '-total_questions'
    ]
    if order_by in allowed:
        qs = qs.order_by(order_by)

    paginator, page_obj, page_size = paginate_queryset(
        request, qs, default_size=10
    )

    data = QuizSessionSerializer(page_obj.object_list, many=True).data

    return Response({
        'results': data,
        'count': paginator.count,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_details(request, session_id):
    try:
        session = QuizSession.objects.select_related('user').get(id=session_id)

        if session.user != request.user and request.user.profile.role != 'admin':
            return Response(
                {'error': 'Brak dostępu do tego quizu'},
                status=status.HTTP_403_FORBIDDEN
            )

        payload = build_quiz_details_payload(session, request.user)
        return Response(payload)

    except QuizSession.DoesNotExist:
        return Response(
            {'error': 'Quiz session not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class QuizSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizSessionSerializer
    permission_classes = [IsAuthenticated, IsQuizOwnerOrAdmin]

    def get_queryset(self):
        return QuizSession.objects.filter(
            user=self.request.user
        ).order_by('-started_at')


@api_view(['GET'])
def quiz_api_root(request):
    return Response({
        'message': 'Quiz LLM API',
        'version': '3.4',
        'endpoints': {
            'start_quiz': '/api/quiz/start/',
            'get_question': '/api/quiz/question/<session_id>/',
            'submit_answer': '/api/quiz/answer/',
            'end_quiz': '/api/quiz/end/<session_id>/',
            'quiz_history': '/api/quiz/history/',
            'quiz_details': '/api/quiz/details/<session_id>/',
            'questions_library': '/api/quiz/questions/',
        }
    })


