from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from users.permissions import IsAdminUser
from users.services import AdminService
from core.exceptions import UserNotFound, ValidationException, QuizNotFound
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    try:
        statistics = AdminService.get_dashboard_statistics()

        logger.debug(f"Admin dashboard accessed: user_id={request.user.id}")

        return Response(statistics, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting admin dashboard: error={str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać statystyk'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_users(request):
    try:
        users_data = AdminService.get_all_users()

        logger.debug(f"All users accessed: user_id={request.user.id}, count={len(users_data)}")

        return Response(users_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting all users: error={str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać listy użytkowników'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_users(request):
    try:
        query = request.GET.get('query', '').strip()
        role = request.GET.get('role')
        is_active_param = request.GET.get('is_active')

        is_active = None
        if is_active_param == 'true':
            is_active = True
        elif is_active_param == 'false':
            is_active = False

        users_data = AdminService.search_users(
            query=query if query else None,
            role=role,
            is_active=is_active
        )

        logger.debug(f"Users search: user_id={request.user.id}, query={query}, count={len(users_data)}")

        return Response(users_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error searching users: error={str(e)}")
        return Response(
            {'error': 'Nie udało się wyszukać użytkowników'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_quiz_history(request, user_id):
    try:
        history_data = AdminService.get_user_quiz_history(user_id)

        logger.debug(f"User quiz history accessed: admin_id={request.user.id}, user_id={user_id}")

        return Response(history_data, status=status.HTTP_200_OK)

    except UserNotFound:
        raise
    except Exception as e:
        logger.error(f"Error getting user quiz history: user_id={user_id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się pobrać historii quizów użytkownika'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    try:
        username = AdminService.delete_user(user_id, request.user)

        logger.warning(f"User deleted: user_id={user_id}, username={username}, by={request.user.id}")

        return Response({
            'message': f'Użytkownik {username} został usunięty'
        }, status=status.HTTP_200_OK)

    except ValidationException:
        raise
    except UserNotFound:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: user_id={user_id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się usunąć użytkownika'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_user_status(request, user_id):
    try:
        result = AdminService.toggle_user_status(user_id, request.user)

        logger.info(f"User status toggled: user_id={user_id}, is_active={result['is_active']}, by={request.user.id}")

        return Response({
            'message': f'Użytkownik {result["username"]} {"aktywowany" if result["is_active"] else "dezaktywowany"}',
            'is_active': result['is_active']
        }, status=status.HTTP_200_OK)

    except ValidationException:
        raise
    except UserNotFound:
        raise
    except Exception as e:
        logger.error(f"Error toggling user status: user_id={user_id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się zmienić statusu użytkownika'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def change_user_role(request, user_id):
    try:
        new_role = request.data.get('role')

        if not new_role:
            raise ValidationException(detail='Rola jest wymagana')

        AdminService.change_user_role(user_id, new_role)

        logger.info(f"User role changed: user_id={user_id}, new_role={new_role}, by={request.user.id}")

        return Response({
            'message': f'Rola użytkownika zmieniona na {new_role}'
        }, status=status.HTTP_200_OK)

    except ValidationException:
        raise
    except UserNotFound:
        raise
    except Exception as e:
        logger.error(f"Error changing user role: user_id={user_id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się zmienić roli użytkownika'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_quiz_session(request, session_id):
    try:
        AdminService.delete_quiz_session(session_id)

        logger.warning(f"Quiz session deleted: session_id={session_id}, by={request.user.id}")

        return Response({
            'message': f'Sesja quizu {session_id} została usunięta'
        }, status=status.HTTP_200_OK)

    except QuizNotFound:
        raise
    except Exception as e:
        logger.error(f"Error deleting quiz session: session_id={session_id}, error={str(e)}")
        return Response(
            {'error': 'Nie udało się usunąć sesji quizu'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )