from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField, FloatField, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from ..models import QuizSession, Question, QuizSessionQuestion, Answer
from ..utils.helpers import build_question_payload  # ✅ DODANE
import time


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_404_NOT_FOUND
        )

    cached = cache.get(f'next_q:{session.id}')
    if cached:
        cache.delete(f'next_q:{session.id}')
        print("⚡ Served question from cache")
        return Response(cached)

    answered_question_ids = Answer.objects.filter(
        session=session,
        user=session.user
    ).values_list('question_id', flat=True)

    answered_texts = Answer.objects.filter(
        session=session,
        user=session.user
    ).values_list('question__question_text', flat=True)

    session_question = QuizSessionQuestion.objects.filter(
        session=session
    ).exclude(
        question_id__in=answered_question_ids
    ).exclude(
        question__question_text__in=answered_texts
    ).select_related('question').order_by('order').first()

    if not session_question:
        max_wait_time = 10
        poll_interval = 0.5
        waited = 0

        print(f"⏳ Waiting up to {max_wait_time}s for question...")

        while waited < max_wait_time:
            time.sleep(poll_interval)
            waited += poll_interval

            session_question = QuizSessionQuestion.objects.filter(
                session=session
            ).exclude(
                question_id__in=answered_question_ids
            ).exclude(
                question__question_text__in=answered_texts
            ).select_related('question').order_by('order').first()

            if session_question:
                print(f"⏱️ Question appeared after {waited}s")
                break

        if not session_question:
            print(f"❌ No question after {max_wait_time}s")
            return Response(
                {'error': 'No more questions available'},
                status=status.HTTP_404_NOT_FOUND
            )

    question = session_question.question
    generation_status = "pre_generated"
    print(f"📖 Question ID={question.id}")

    # ✅ UŻYCIE FUNKCJI Z HELPERS zamiast 15 linii inline
    payload = build_question_payload(session, question, generation_status)

    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questions_library(request):
    # ... (reszta kodu BEZ ZMIAN - tutaj nie używamy helpers)
    def normalize_diff_token(token: str):
        t = (token or '').strip().lower()
        if t in ('łatwy', 'latwy', 'easy'):
            return 'łatwy'
        if t in ('średni', 'sredni', 'medium'):
            return 'średni'
        if t in ('trudny', 'hard'):
            return 'trudny'
        return None

    difficulty_rank = Case(
        When(difficulty_level__iexact='łatwy', then=Value(1)),
        When(difficulty_level__iexact='latwy', then=Value(1)),
        When(difficulty_level__iexact='easy', then=Value(1)),
        When(difficulty_level__iexact='średni', then=Value(2)),
        When(difficulty_level__iexact='sredni', then=Value(2)),
        When(difficulty_level__iexact='medium', then=Value(2)),
        When(difficulty_level__iexact='trudny', then=Value(3)),
        When(difficulty_level__iexact='hard', then=Value(3)),
        default=Value(2), output_field=IntegerField()
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
        tokens = [normalize_diff_token(t) for t in diff_param.split(',')]
        wanted = {t for t in tokens if t}
        if wanted:
            qf = Q()
            if 'łatwy' in wanted:
                qf |= Q(difficulty_level__iexact='łatwy') | Q(difficulty_level__iexact='latwy') | Q(
                    difficulty_level__iexact='easy')
            if 'średni' in wanted:
                qf |= Q(difficulty_level__iexact='średni') | Q(difficulty_level__iexact='sredni') | Q(
                    difficulty_level__iexact='medium')
            if 'trudny' in wanted:
                qf |= Q(difficulty_level__iexact='trudny') | Q(difficulty_level__iexact='hard')
            qs = qs.filter(qf)

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

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 20))
    except ValueError:
        page_size = 20

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    def normalized_name(label):
        l = (label or '').strip().lower()
        if l in ('łatwy', 'latwy', 'easy'):
            return 'łatwy'
        if l in ('średni', 'sredni', 'medium'):
            return 'średni'
        if l in ('trudny', 'hard'):
            return 'trudny'
        return label or 'średni'

    results = []
    for q in page_obj.object_list:
        results.append({
            'id': q.id,
            'question_text': q.question_text,
            'topic': q.topic,
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