import logging
from django.core.cache import cache
from ..utils.helpers import build_question_payload

logger = logging.getLogger(__name__)


class QuizCacheService:
    """Service for managing quiz-related caching operations"""

    CACHE_TIMEOUT = 120

    @staticmethod
    def get_cache_key(session_id):
        """Generate cache key for quiz session"""
        return f'next_q:{session_id}'

    @staticmethod
    def cache_next_question(session, question):
        """
        Cache next question payload for quiz session.

        Args:
            session: QuizSession object
            question: Question object
        """
        try:
            payload = build_question_payload(session, question, generation_status='cached')
            cache_key = QuizCacheService.get_cache_key(session.id)
            cache.set(cache_key, payload, timeout=QuizCacheService.CACHE_TIMEOUT)
            logger.debug(f"Cached question {question.id} for session {session.id}")
        except Exception as e:
            logger.error(f"Failed to cache question for session {session.id}: {e}")

    @staticmethod
    def get_cached_question(session_id):
        """
        Retrieve cached question for session.

        Args:
            session_id: ID of quiz session

        Returns:
            dict or None: Cached question payload or None if not found
        """
        cache_key = QuizCacheService.get_cache_key(session_id)
        cached = cache.get(cache_key)

        if cached:
            logger.debug(f"Retrieved cached question for session {session_id}")

        return cached

    @staticmethod
    def delete_cached_question(session_id):
        """
        Delete cached question for session.

        Args:
            session_id: ID of quiz session
        """
        cache_key = QuizCacheService.get_cache_key(session_id)
        cache.delete(cache_key)
        logger.debug(f"Deleted cached question for session {session_id}")

    @staticmethod
    def clear_session_cache(session_id):
        """
        Clear all cache entries for session.

        Args:
            session_id: ID of quiz session
        """
        QuizCacheService.delete_cached_question(session_id)
