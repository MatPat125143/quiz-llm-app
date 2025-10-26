from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from users.permissions import IsAdminUser
from quiz_app.models import QuizSession, Question, Answer

User = get_user_model()

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

    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.profile.role,
            'total_quizzes': user.profile.total_quizzes_played,
            'accuracy': user.profile.accuracy,
            'joined': user.date_joined,
            'is_active': user.is_active
        })

    return Response(users_data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    if user_id == request.user.id:
        return Response({'error': 'Cannot delete yourself'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
        username = user.username
        user.delete()
        return Response({'message': f'User {username} deleted'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def change_user_role(request, user_id):
    new_role = request.data.get('role')

    if new_role not in ['user', 'admin']:
        return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
        user.profile.role = new_role
        user.profile.save()
        return Response({'message': f'Role changed to {new_role}'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)