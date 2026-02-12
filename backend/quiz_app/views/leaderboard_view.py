from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..services.leaderboard_service import (
    get_global_leaderboard,
    get_topic_leaderboard,
    get_user_ranking,
    get_leaderboard_stats,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def global_leaderboard(request):
    period = request.GET.get("period", "all")
    limit = int(request.GET.get("limit", 50))
    payload = get_global_leaderboard(request, period, limit)
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topic_leaderboard(request):
    topic = request.GET.get("topic")
    limit = int(request.GET.get("limit", 50))

    if not topic:
        return Response({"error": "Topic parameter is required"}, status=400)

    payload = get_topic_leaderboard(request, topic, limit)
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_ranking(request):
    user = request.user
    payload = get_user_ranking(user)
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def leaderboard_stats(request):
    payload = get_leaderboard_stats(request)
    return Response(payload)


