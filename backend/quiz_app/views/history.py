from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from ..models import QuizSession, Answer
from ..serializers import QuizSessionSerializer
from ..permissions import IsQuizOwnerOrAdmin


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    qs = QuizSession.objects.filter(user=request.user, is_completed=True)

    topic = request.GET.get('topic')
    difficulty = request.GET.get('difficulty')
    is_custom = request.GET.get('is_custom')

    if topic:
        qs = qs.filter(topic__icontains=topic)

    if difficulty in ['easy', 'medium', 'hard']:
        qs = qs.filter(initial_difficulty=difficulty)

    if is_custom in ['true', 'false']:
        ids = []
        for s in qs.only('id', 'questions_count', 'time_per_question', 'use_adaptive_difficulty'):
            custom = (s.questions_count != 10 or s.time_per_question != 30 or not s.use_adaptive_difficulty)
            if (is_custom == 'true' and custom) or (is_custom == 'false' and not custom):
                ids.append(s.id)
        qs = qs.filter(id__in=ids)

    order_by = request.GET.get('order_by', '-started_at')
    allowed = ['started_at', '-started_at', 'accuracy', '-accuracy', 'topic', '-topic', 'total_questions',
               '-total_questions']
    if order_by in allowed:
        qs = qs.order_by(order_by)

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except ValueError:
        page_size = 10

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

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

        # Sprawdź czy użytkownik ma dostęp (właściciel lub admin)
        if session.user != request.user and request.user.profile.role != 'admin':
            return Response(
                {'error': 'Brak dostępu do tego quizu'},
                status=status.HTTP_403_FORBIDDEN
            )

        answers = Answer.objects.filter(
            session=session,
            user=session.user
        ).select_related('question').order_by('answered_at')

        answers_data = [
            {
                'question_text': ans.question.question_text,
                'correct_answer': ans.question.correct_answer,
                'wrong_answer_1': ans.question.wrong_answer_1,
                'wrong_answer_2': ans.question.wrong_answer_2,
                'wrong_answer_3': ans.question.wrong_answer_3,
                'selected_answer': ans.selected_answer,
                'is_correct': ans.is_correct,
                'explanation': ans.question.explanation,
                'response_time': ans.response_time,
            }
            for ans in answers
        ]

        difficulty_progress = []
        if session.use_adaptive_difficulty:
            for ans in answers:
                difficulty_progress.append({
                    'difficulty': ans.difficulty_at_answer,
                    'is_correct': ans.is_correct
                })

        # Dodaj informacje o użytkowniku dla adminów
        user_info = None
        if request.user.profile.role == 'admin':
            user_info = {
                'username': session.user.username,
                'email': session.user.email,
                'user_id': session.user.id
            }

        return Response({
            'session': {
                'id': session.id,
                'topic': session.topic,
                'subtopic': session.subtopic,
                'knowledge_level': session.knowledge_level,
                'difficulty': session.initial_difficulty,
                'use_adaptive_difficulty': session.use_adaptive_difficulty,
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'accuracy': session.accuracy,
                'started_at': session.started_at,
                'ended_at': session.ended_at,
                'completed_at': session.ended_at,
                'user_info': user_info,  # DODANE
            },
            'answers': answers_data,
            'difficulty_progress': difficulty_progress
        })

    except QuizSession.DoesNotExist:
        return Response(
            {'error': 'Quiz session not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class QuizSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuizSessionSerializer
    permission_classes = [IsAuthenticated, IsQuizOwnerOrAdmin]

    def get_queryset(self):
        return QuizSession.objects.filter(user=self.request.user).order_by('-started_at')


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


print("✅ Views loaded - Stats from completed quizzes only")