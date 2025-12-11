from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import Question
from users.permissions import IsAdminUser


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_questions(request):
    """
    Listuje wszystkie pytania z paginacją i filtrowaniem.
    Parametry query:
    - page: numer strony (domyślnie 1)
    - page_size: ilość na stronę (domyślnie 20, max 100)
    - search: wyszukiwanie w treści pytania
    - topic: filtruj po temacie
    - difficulty: filtruj po poziomie trudności
    - knowledge_level: filtruj po poziomie wiedzy
    """
    questions = Question.objects.all().select_related('created_by').order_by('-created_at')

    # Filtrowanie
    search = request.query_params.get('search', '').strip()
    topic = request.query_params.get('topic', '').strip()
    difficulty = request.query_params.get('difficulty', '').strip()
    knowledge_level = request.query_params.get('knowledge_level', '').strip()

    if search:
        questions = questions.filter(
            Q(question_text__icontains=search) |
            Q(correct_answer__icontains=search) |
            Q(explanation__icontains=search)
        )

    if topic:
        questions = questions.filter(topic__icontains=topic)

    if difficulty:
        questions = questions.filter(difficulty_level=difficulty)

    if knowledge_level:
        questions = questions.filter(knowledge_level=knowledge_level)

    # Paginacja
    page = request.query_params.get('page', 1)
    page_size = min(int(request.query_params.get('page_size', 20)), 100)

    paginator = Paginator(questions, page_size)
    page_obj = paginator.get_page(page)

    questions_data = []
    for question in page_obj:
        questions_data.append({
            'id': question.id,
            'topic': question.topic,
            'subtopic': question.subtopic,
            'knowledge_level': question.knowledge_level,
            'question_text': question.question_text,
            'correct_answer': question.correct_answer,
            'wrong_answer_1': question.wrong_answer_1,
            'wrong_answer_2': question.wrong_answer_2,
            'wrong_answer_3': question.wrong_answer_3,
            'explanation': question.explanation,
            'difficulty_level': question.difficulty_level,
            'total_answers': question.total_answers,
            'correct_answers_count': question.correct_answers_count,
            'success_rate': question.success_rate,
            'times_used': question.times_used,
            'created_at': question.created_at,
            'created_by': question.created_by.email if question.created_by else None
        })

    return Response({
        'questions': questions_data,
        'pagination': {
            'total_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_question_detail(request, question_id):
    """Pobierz szczegóły pojedynczego pytania"""
    question = get_object_or_404(Question, id=question_id)

    return Response({
        'id': question.id,
        'topic': question.topic,
        'subtopic': question.subtopic,
        'knowledge_level': question.knowledge_level,
        'question_text': question.question_text,
        'correct_answer': question.correct_answer,
        'wrong_answer_1': question.wrong_answer_1,
        'wrong_answer_2': question.wrong_answer_2,
        'wrong_answer_3': question.wrong_answer_3,
        'explanation': question.explanation,
        'difficulty_level': question.difficulty_level,
        'total_answers': question.total_answers,
        'correct_answers_count': question.correct_answers_count,
        'success_rate': question.success_rate,
        'times_used': question.times_used,
        'created_at': question.created_at,
        'created_by': question.created_by.email if question.created_by else None
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_question(request, question_id):
    """Zaktualizuj pytanie"""
    question = get_object_or_404(Question, id=question_id)

    # Pola które można edytować
    editable_fields = [
        'question_text', 'correct_answer',
        'wrong_answer_1', 'wrong_answer_2', 'wrong_answer_3',
        'explanation', 'topic', 'subtopic',
        'difficulty_level', 'knowledge_level'
    ]

    # Walidacja
    if 'question_text' in request.data and len(request.data['question_text'].strip()) < 10:
        return Response(
            {'error': 'Question text must be at least 10 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if 'difficulty_level' in request.data and request.data['difficulty_level'] not in ['łatwy', 'średni', 'trudny']:
        return Response(
            {'error': 'Invalid difficulty level'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if 'knowledge_level' in request.data and request.data['knowledge_level'] not in ['elementary', 'high_school', 'university', 'expert']:
        return Response(
            {'error': 'Invalid knowledge level'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Aktualizuj tylko dozwolone pola
    for field in editable_fields:
        if field in request.data:
            setattr(question, field, request.data[field])

    # Przelicz content_hash po zmianach
    import hashlib
    content = f"{question.question_text}{question.correct_answer}{question.topic}{question.subtopic or ''}{question.knowledge_level or ''}{question.difficulty_level}"
    question.content_hash = hashlib.sha256(content.encode()).hexdigest()

    question.save()

    return Response({
        'message': 'Question updated successfully',
        'question': {
            'id': question.id,
            'question_text': question.question_text,
            'correct_answer': question.correct_answer,
            'difficulty_level': question.difficulty_level,
            'knowledge_level': question.knowledge_level
        }
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_question(request, question_id):
    """Usuń pytanie"""
    question = get_object_or_404(Question, id=question_id)

    # Sprawdź czy pytanie jest używane w aktywnych sesjach
    from ..models import QuizSessionQuestion, Answer

    active_usage = QuizSessionQuestion.objects.filter(
        question=question,
        session__is_completed=False
    ).exists()

    if active_usage:
        return Response(
            {'error': 'Cannot delete question used in active quiz sessions'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Usuń powiązane odpowiedzi (cascade powinno to zrobić, ale dla pewności)
    Answer.objects.filter(question=question).delete()
    QuizSessionQuestion.objects.filter(question=question).delete()

    question_text = question.question_text[:50]
    question.delete()

    return Response({
        'message': f'Question deleted successfully: {question_text}...'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def question_stats(request):
    """Statystyki pytań"""
    from django.db.models import Count, Avg

    total_questions = Question.objects.count()
    by_difficulty = Question.objects.values('difficulty_level').annotate(count=Count('id'))
    by_knowledge = Question.objects.values('knowledge_level').annotate(count=Count('id'))
    by_topic = Question.objects.values('topic').annotate(count=Count('id')).order_by('-count')[:10]

    avg_success_rate = Question.objects.filter(total_answers__gt=0).aggregate(
        avg_rate=Avg('correct_answers_count') * 100.0 / Avg('total_answers')
    )

    return Response({
        'total_questions': total_questions,
        'by_difficulty': list(by_difficulty),
        'by_knowledge_level': list(by_knowledge),
        'top_topics': list(by_topic),
        'average_success_rate': avg_success_rate.get('avg_rate', 0)
    })
