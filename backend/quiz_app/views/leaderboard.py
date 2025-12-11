from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import QuizSession, Answer

User = get_user_model()


def _serialize_user(user, rank):
    avatar_url = None
    try:
        if user.profile and user.profile.avatar:
            avatar_url = user.profile.avatar.url
    except Exception:
        avatar_url = None

    total_questions = user.total_questions or 0
    total_correct = user.total_correct or 0
    accuracy = round((total_correct / total_questions * 100), 2) if total_questions else 0

    return {
        "rank": rank,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": avatar_url,
        "total_quizzes": user.total_quizzes or 0,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "accuracy": accuracy,
        "total_score": total_correct,
    }


def _get_period_filter(period):
    filters = Q(quiz_sessions__is_completed=True)
    if period == "week":
        date_from = timezone.now() - timedelta(days=7)
        filters &= Q(quiz_sessions__ended_at__gte=date_from)
    elif period == "month":
        date_from = timezone.now() - timedelta(days=30)
        filters &= Q(quiz_sessions__ended_at__gte=date_from)
    return filters


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def global_leaderboard(request):
    period = request.GET.get("period", "all")
    limit = int(request.GET.get("limit", 50))

    filters = _get_period_filter(period)

    users = (
        User.objects.filter(filters)
        .annotate(
            total_quizzes=Count(
                "quiz_sessions", filter=Q(quiz_sessions__is_completed=True)
            ),
            total_questions=Coalesce(
                Sum("quiz_sessions__total_questions", filter=Q(quiz_sessions__is_completed=True)), 0
            ),
            total_correct=Coalesce(
                Sum("quiz_sessions__correct_answers", filter=Q(quiz_sessions__is_completed=True)), 0
            ),
        )
        .filter(total_quizzes__gt=0)
        .order_by("-total_correct")[:limit]
    )

    leaderboard_data = [
        _serialize_user(user, rank) for rank, user in enumerate(users, start=1)
    ]

    return Response({"period": period, "leaderboard": leaderboard_data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topic_leaderboard(request):
    topic = request.GET.get("topic")
    limit = int(request.GET.get("limit", 50))

    if not topic:
        return Response({"error": "Topic parameter is required"}, status=400)

    users = (
        User.objects.filter(
            quiz_sessions__is_completed=True, quiz_sessions__topic__icontains=topic
        )
        .annotate(
            total_quizzes=Count(
                "quiz_sessions",
                filter=Q(
                    quiz_sessions__is_completed=True,
                    quiz_sessions__topic__icontains=topic,
                ),
            ),
            total_questions=Coalesce(
                Sum(
                    "quiz_sessions__total_questions",
                    filter=Q(
                        quiz_sessions__is_completed=True,
                        quiz_sessions__topic__icontains=topic,
                    ),
                ),
                0,
            ),
            total_correct=Coalesce(
                Sum(
                    "quiz_sessions__correct_answers",
                    filter=Q(
                        quiz_sessions__is_completed=True,
                        quiz_sessions__topic__icontains=topic,
                    ),
                ),
                0,
            ),
        )
        .filter(total_quizzes__gt=0)
        .order_by("-total_correct")[:limit]
    )

    leaderboard_data = [
        _serialize_user(user, rank) for rank, user in enumerate(users, start=1)
    ]

    return Response({"topic": topic, "leaderboard": leaderboard_data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_ranking(request):
    user = request.user

    stats = QuizSession.objects.filter(user=user, is_completed=True).aggregate(
        total_quizzes=Coalesce(Count("id"), 0),
        total_questions=Coalesce(Sum("total_questions"), 0),
        total_correct=Coalesce(Sum("correct_answers"), 0),
    )

    total_questions = stats["total_questions"] or 0
    total_correct = stats["total_correct"] or 0
    accuracy = (total_correct / total_questions * 100) if total_questions else 0

    if stats["total_quizzes"] == 0:
        total_users = (
            User.objects.filter(quiz_sessions__is_completed=True).distinct().count()
        )
        return Response(
            {
                "rank": None,
                "total_users": total_users,
                "percentile": 0,
                "stats": {
                    "total_quizzes": 0,
                    "total_questions": 0,
                    "total_correct": 0,
                    "accuracy": 0,
                },
            }
        )

    all_users = (
        User.objects.filter(quiz_sessions__is_completed=True)
        .annotate(
            total_questions=Coalesce(
                Sum(
                    "quiz_sessions__total_questions",
                    filter=Q(quiz_sessions__is_completed=True),
                ),
                0,
            ),
            total_correct=Coalesce(
                Sum(
                    "quiz_sessions__correct_answers",
                    filter=Q(quiz_sessions__is_completed=True),
                ),
                0,
            ),
        )
        .filter(total_questions__gt=0)
    )

    better_users = [
        u
        for u in all_users
        if (u.total_correct / u.total_questions * 100) > accuracy
    ]

    rank = len(better_users) + 1
    total_users = all_users.count()
    percentile = round((1 - (rank - 1) / total_users) * 100, 1) if total_users else 0

    return Response(
        {
            "rank": rank,
            "total_users": total_users,
            "percentile": percentile,
            "stats": {
                "total_quizzes": stats["total_quizzes"],
                "total_questions": total_questions,
                "total_correct": total_correct,
                "accuracy": round(accuracy, 2),
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def leaderboard_stats(request):
    total_users = (
        User.objects.filter(quiz_sessions__is_completed=True).distinct().count()
    )
    total_quizzes = QuizSession.objects.filter(is_completed=True).count()
    total_questions = Answer.objects.count()
    correct_answers = Answer.objects.filter(is_correct=True).count()
    avg_accuracy = (correct_answers / total_questions * 100) if total_questions else 0

    popular_topics = (
        QuizSession.objects.filter(is_completed=True)
        .values("topic")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    best_user = (
        User.objects.filter(quiz_sessions__is_completed=True)
        .annotate(
            total_quizzes=Count(
                "quiz_sessions", filter=Q(quiz_sessions__is_completed=True)
            ),
            total_questions=Coalesce(
                Sum(
                    "quiz_sessions__total_questions",
                    filter=Q(quiz_sessions__is_completed=True),
                ),
                0,
            ),
            total_correct=Coalesce(
                Sum(
                    "quiz_sessions__correct_answers",
                    filter=Q(quiz_sessions__is_completed=True),
                ),
                0,
            ),
        )
        .filter(total_quizzes__gte=5, total_questions__gt=0)
        .order_by("-total_correct")
        .first()
    )

    best_user_data = None
    if best_user:
        best_accuracy = (
            best_user.total_correct / best_user.total_questions * 100
            if best_user.total_questions
            else 0
        )
        best_user_data = {
            "username": best_user.username,
            "accuracy": round(best_accuracy, 2),
            "total_quizzes": best_user.total_quizzes,
        }

    return Response(
        {
            "total_users": total_users,
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "avg_accuracy": round(avg_accuracy, 2),
            "popular_topics": list(popular_topics),
            "best_user": best_user_data,
        }
    )
