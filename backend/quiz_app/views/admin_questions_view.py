from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdminUser
from ..models import Question, QuizSessionQuestion, Answer
from ..serializers.question_serializer import AdminQuestionSerializer
from ..utils.pagination import paginate_queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_questions(request):
    questions = (
        Question.objects.all()
        .select_related('created_by')
        .order_by('-created_at')
    )

    search = request.query_params.get('search', '').strip()
    topic = request.query_params.get('topic', '').strip()
    difficulty = request.query_params.get('difficulty', '').strip()
    knowledge_level = request.query_params.get('knowledge_level', '').strip()

    if search:
        questions = questions.filter(
            Q(question_text__icontains=search)
            | Q(correct_answer__icontains=search)
            | Q(explanation__icontains=search)
        )

    if topic:
        questions = questions.filter(topic__icontains=topic)

    if difficulty:
        questions = questions.filter(difficulty_level=difficulty)

    if knowledge_level:
        questions = questions.filter(knowledge_level=knowledge_level)

    paginator, page_obj, page_size = paginate_queryset(
        request, questions, default_size=20, max_size=100
    )

    questions_data = AdminQuestionSerializer(page_obj, many=True).data

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
    question = get_object_or_404(Question, id=question_id)
    return Response(AdminQuestionSerializer(question).data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    serializer = AdminQuestionSerializer(
        question,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'message': 'Question updated successfully',
        'question': {
            'id': serializer.instance.id,
            'question_text': serializer.instance.question_text,
            'correct_answer': serializer.instance.correct_answer,
            'difficulty_level': serializer.instance.difficulty_level,
            'knowledge_level': serializer.instance.knowledge_level,
            'edited_at': serializer.instance.edited_at,
        }
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    active_usage = QuizSessionQuestion.objects.filter(
        question=question,
        session__is_completed=False
    ).exists()

    if active_usage:
        return Response(
            {'error': 'Cannot delete question used in active quiz sessions'},
            status=status.HTTP_400_BAD_REQUEST
        )

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
    total_questions = Question.objects.count()
    by_difficulty = Question.objects.values('difficulty_level').annotate(
        count=Count('id')
    )
    by_knowledge = Question.objects.values('knowledge_level').annotate(
        count=Count('id')
    )
    by_topic = Question.objects.values('topic').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    avg_success_rate = Question.objects.filter(
        total_answers__gt=0
    ).aggregate(
        avg_rate=Avg('correct_answers_count') * 100.0 / Avg('total_answers')
    )

    return Response({
        'total_questions': total_questions,
        'by_difficulty': list(by_difficulty),
        'by_knowledge_level': list(by_knowledge),
        'top_topics': list(by_topic),
        'average_success_rate': avg_success_rate.get('avg_rate', 0)
    })


