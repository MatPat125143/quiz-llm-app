from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db.models import FloatField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from ..permissions import IsAdminUser
from quiz_app.models import QuizSession, Question, Answer

User = get_user_model()


def _get_avatar_url(user, request):
    profile = getattr(user, 'profile', None)
    avatar = getattr(profile, 'avatar', None)
    if not avatar:
        return None

    url = avatar.url
    if request is not None and url.startswith('/'):
        return request.build_absolute_uri(url)
    return url


def _serialize_user_for_admin(user, request):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.profile.role,
        'total_quizzes': user.profile.total_quizzes_played,
        'accuracy': user.profile.accuracy,
        'joined': user.date_joined,
        'is_active': user.is_active,
        'avatar_url': _get_avatar_url(user, request),
    }


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    total_users = User.objects.count()
    total_quizzes = QuizSession.objects.count()
    total_questions = Question.objects.count()
    total_answers = Answer.objects.count()

    correct_answers = Answer.objects.filter(is_correct=True).count()
    avg_accuracy = round((correct_answers / total_answers * 100), 2) if total_answers > 0 else 0

    return Response({
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'avg_accuracy': avg_accuracy
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_users(request):
    users = User.objects.select_related('profile').all()

    users_data = [_serialize_user_for_admin(u, request) for u in users]

    return Response(users_data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_users(request):
    query = request.GET.get('query', '').strip().lower()
    role = request.GET.get('role')
    is_active = request.GET.get('is_active')

    users = User.objects.select_related('profile').all()

    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))

    if role in ['admin', 'user']:
        users = users.filter(profile__role=role)

    if is_active in ['true', 'false']:
        users = users.filter(is_active=(is_active == 'true'))

    users_data = [_serialize_user_for_admin(u, request) for u in users]

    return Response(users_data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_quiz_history(request, user_id):
    user = get_object_or_404(User, id=user_id)
    sessions = (
        QuizSession.objects.filter(user=user, is_completed=True)
        .annotate(
            total_response_time=Coalesce(
                Sum('answers__response_time'),
                Value(0.0),
                output_field=FloatField()
            )
        )
        .order_by('-ended_at')
    )

    if not sessions.exists():
        return Response([], status=status.HTTP_200_OK)

    data = [
        {
            "id": s.id,
            "topic": s.topic,
            "subtopic": s.subtopic,
            "difficulty": s.initial_difficulty,
            "knowledge_level": s.knowledge_level,
            "use_adaptive_difficulty": s.use_adaptive_difficulty,
            "accuracy": s.accuracy,
            "correct_answers": s.correct_answers,
            "total_questions": s.total_questions,
            "total_response_time": round(float(getattr(s, 'total_response_time', 0.0) or 0.0), 2),
            "started_at": s.started_at,
            "ended_at": s.ended_at,
        }
        for s in sessions
    ]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_quiz_session(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id)

    Answer.objects.filter(session=session).delete()

    session.delete()

    return Response({'message': f'Sesja quizu {session_id} została usunięta.'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    if user_id == request.user.id:
        return Response({'error': 'Nie możesz usunąć samego siebie'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
        username = user.username
        user.delete()
        return Response({'message': f'Użytkownik {username} został usunięty.'})
    except User.DoesNotExist:
        return Response({'error': 'Użytkownik nie znaleziony'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_user_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)

        if user == request.user:
            return Response({'error': 'Nie możesz dezaktywować swojego konta.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.is_active = not user.is_active
        user.save()

        return Response({
            'message': f'Użytkownik {user.username} {"aktywowany" if user.is_active else "dezaktywowany"}',
            'is_active': user.is_active
        })
    except User.DoesNotExist:
        return Response({'error': 'Użytkownik nie znaleziony'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def change_user_role(request, user_id):
    new_role = request.data.get('role')
    if new_role not in ['user', 'admin']:
        return Response({'error': 'Niepoprawna rola'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
        user.profile.role = new_role
        user.profile.save()
        return Response({'message': f'Rola użytkownika zmieniona na {new_role}'})
    except User.DoesNotExist:
        return Response({'error': 'Użytkownik nie znaleziony'}, status=status.HTTP_404_NOT_FOUND)


