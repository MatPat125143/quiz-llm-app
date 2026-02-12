from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum, Q, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from ..models import QuizSession, Answer

User = get_user_model()


def _serialize_user(request, user, rank):
    avatar_url = None
    profile = getattr(user, "profile", None)
    if profile and profile.avatar:
        avatar_url = profile.avatar.url
        if avatar_url and request is not None and avatar_url.startswith("/"):
            avatar_url = request.build_absolute_uri(avatar_url)

    total_questions = user.total_questions or 0
    total_correct = user.total_correct or 0
    accuracy = round((total_correct / total_questions * 100), 2) if total_questions else 0

    avg_response_time = getattr(user, "avg_response_time", None)
    if avg_response_time is None:
        avg_response_time = 0

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
        "avg_response_time": round(avg_response_time, 2) if avg_response_time else 0,
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


def _get_period_date_from(period):
    if period == "week":
        return timezone.now() - timedelta(days=7)
    if period == "month":
        return timezone.now() - timedelta(days=30)
    return None


def get_global_leaderboard(request, period, limit):
    filters = _get_period_filter(period)
    date_from = _get_period_date_from(period)
    answers_qs = Answer.objects.filter(
        user=OuterRef("pk"),
        response_time__gt=0,
        session__is_completed=True,
    )
    if date_from:
        answers_qs = answers_qs.filter(session__ended_at__gte=date_from)
    answers_qs = answers_qs.values("user").annotate(
        avg_rt=Avg("response_time")
    ).values("avg_rt")

    users = (
        User.objects.filter(filters)
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
            avg_response_time=Coalesce(Subquery(answers_qs), Value(0.0)),
        )
        .filter(total_quizzes__gt=0)
        .order_by("-total_correct")[:limit]
    )

    leaderboard_data = [
        _serialize_user(request, user, rank)
        for rank, user in enumerate(users, start=1)
    ]

    return {"period": period, "leaderboard": leaderboard_data}


def get_topic_leaderboard(request, topic, limit):
    users = (
        User.objects.filter(
            quiz_sessions__is_completed=True,
            quiz_sessions__topic__icontains=topic
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
        _serialize_user(request, user, rank)
        for rank, user in enumerate(users, start=1)
    ]

    return {"topic": topic, "leaderboard": leaderboard_data}


def get_user_ranking(user):
    stats = QuizSession.objects.filter(
        user=user,
        is_completed=True
    ).aggregate(
        total_quizzes=Coalesce(Count("id"), 0),
        total_questions=Coalesce(Sum("total_questions"), 0),
        total_correct=Coalesce(Sum("correct_answers"), 0),
    )

    total_questions = stats["total_questions"] or 0
    total_correct = stats["total_correct"] or 0
    accuracy = (total_correct / total_questions * 100) if total_questions else 0

    if stats["total_quizzes"] == 0:
        total_users = (
            User.objects.filter(quiz_sessions__is_completed=True)
            .distinct()
            .count()
        )
        return {
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

    return {
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


def get_leaderboard_stats(request):
    total_users = (
        User.objects.filter(quiz_sessions__is_completed=True)
        .distinct()
        .count()
    )
    total_quizzes = QuizSession.objects.filter(is_completed=True).count()
    total_questions = Answer.objects.count()
    correct_answers = Answer.objects.filter(is_correct=True).count()
    avg_accuracy = (correct_answers / total_questions * 100) if total_questions else 0
    avg_response_time = (
        QuizSession.objects.filter(answers__response_time__gt=0)
        .annotate(
            avg_time=Avg(
                "answers__response_time",
                filter=Q(answers__response_time__gt=0),
            )
        )
        .aggregate(avg=Avg("avg_time"))
        .get("avg")
        or 0
    )

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
        .filter(total_quizzes__gt=0)
        .order_by("-total_correct")
        .first()
    )

    best_user_data = _serialize_user(request, best_user, 1) if best_user else None

    return {
        "total_users": total_users,
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "average_accuracy": round(avg_accuracy, 2),
        "average_response_time": round(avg_response_time, 2),
        "popular_topics": list(popular_topics),
        "best_user": best_user_data,
    }


