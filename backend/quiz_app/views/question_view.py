from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Case, When, Value, IntegerField, FloatField, F, ExpressionWrapper
from django.db.models.functions import Coalesce

from ..models import QuizSession, Question
from ..services.question_delivery_service import get_next_question_payload
from ..utils.constants import DIFFICULTY_ALIAS_MAP, DIFFICULTY_NAME_MAP
from ..utils.pagination import paginate_queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_404_NOT_FOUND
        )

    payload, error = get_next_question_payload(session)
    if error:
        return Response(
            {'error': error},
            status=status.HTTP_404_NOT_FOUND
        )
    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questions_library(request):
    def normalize_diff_token(token: str):
        t = (token or "").strip().lower()
        return DIFFICULTY_ALIAS_MAP.get(t)

    rank_map = {"easy": 1, "medium": 2, "hard": 3}
    rank_by_token = {
        token: rank_map[mapped]
        for token, mapped in DIFFICULTY_ALIAS_MAP.items()
        if mapped in rank_map
    }

    difficulty_rank = Case(
        *[
            When(difficulty_level__iexact=token, then=Value(rank))
            for token, rank in rank_by_token.items()
        ],
        default=Value(2),
        output_field=IntegerField()
    )

    safe_total = Case(
        When(total_answers__gt=0, then=F('total_answers')),
        default=Value(1),
        output_field=FloatField()
    )
    success_rate_expr = ExpressionWrapper(
        100.0 * Coalesce(F('correct_answers_count'), Value(0.0)) / safe_total,
        output_field=FloatField()
    )

    qs = Question.objects.all().annotate(
        _difficulty_rank=difficulty_rank,
        _success_rate=success_rate_expr
    )

    qs = qs.filter(total_answers__gt=0)

    topic = request.GET.get('topic')
    search = request.GET.get('search')
    diff_param = request.GET.get('difficulty')
    knowledge_level = request.GET.get('knowledge_level')

    if topic:
        qs = qs.filter(topic__icontains=topic)

    if search:
        qs = qs.filter(
            Q(question_text__icontains=search) |
            Q(correct_answer__icontains=search) |
            Q(wrong_answer_1__icontains=search) |
            Q(wrong_answer_2__icontains=search) |
            Q(wrong_answer_3__icontains=search) |
            Q(explanation__icontains=search)
        )

    if diff_param:
        tokens = [normalize_diff_token(t) for t in diff_param.split(",")]
        wanted = {t for t in tokens if t}
        if wanted:
            qf = Q()
            for canonical in wanted:
                qf |= Q(difficulty_level__iexact=canonical)
                for token, mapped in DIFFICULTY_ALIAS_MAP.items():
                    if mapped == canonical:
                        qf |= Q(difficulty_level__iexact=token)
            qs = qs.filter(qf)

    if knowledge_level:
        qs = qs.filter(knowledge_level=knowledge_level)

    smin = request.GET.get('success_min')
    smax = request.GET.get('success_max')
    try:
        if smin not in (None, ''):
            qs = qs.filter(_success_rate__gte=float(smin))
        if smax not in (None, ''):
            qs = qs.filter(_success_rate__lte=float(smax))
    except ValueError:
        pass

    umin = request.GET.get('used_min')
    umax = request.GET.get('used_max')
    try:
        if umin not in (None, ''):
            qs = qs.filter(times_used__gte=int(umin))
        if umax not in (None, ''):
            qs = qs.filter(times_used__lte=int(umax))
    except ValueError:
        pass

    has_expl = (request.GET.get('has_explanation') or '').lower()
    if has_expl in ('true', 'false'):
        if has_expl == 'true':
            qs = qs.filter(~Q(explanation__isnull=True) & ~Q(explanation__exact=''))
        else:
            qs = qs.filter(Q(explanation__isnull=True) | Q(explanation__exact=''))

    order_by = request.GET.get('order_by', '-created_at')
    mapping = {
        'created_at': 'created_at',
        '-created_at': '-created_at',
        'success_rate': '_success_rate',
        '-success_rate': '-_success_rate',
    }
    qs = qs.order_by(mapping.get(order_by, '-created_at'))

    paginator, page_obj, page_size = paginate_queryset(
        request, qs, default_size=20
    )

    def normalized_name(label):
        name = (label or "").strip().lower()
        normalized = DIFFICULTY_ALIAS_MAP.get(name, name)
        return DIFFICULTY_NAME_MAP.get(normalized, label or "średni")

    results = []
    for q in page_obj.object_list:
        results.append({
            'id': q.id,
            'question_text': q.question_text,
            'topic': q.topic,
            'knowledge_level': q.knowledge_level,
            'difficulty_level': normalized_name(q.difficulty_level),
            'correct_answer': q.correct_answer,
            'wrong_answer_1': q.wrong_answer_1,
            'wrong_answer_2': q.wrong_answer_2,
            'wrong_answer_3': q.wrong_answer_3,
            'explanation': q.explanation,
            'created_at': q.created_at,
            'stats': {
                'total_answers': q.total_answers,
                'correct_answers': getattr(q, 'correct_answers_count', None),
                'wrong_answers': (q.total_answers - getattr(q, 'correct_answers_count', 0))
                if q.total_answers is not None and getattr(q, 'correct_answers_count', None) is not None else None,
                'accuracy': getattr(q, 'success_rate', None) if getattr(q, 'success_rate', None) is not None else round(
                    getattr(q, '_success_rate', 0.0), 2),
                'times_used': getattr(q, 'times_used', 0),
            }
        })

    return Response({
        'count': paginator.count,
        'results': results
    })


