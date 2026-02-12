import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class QuizCacheService:
    DEFAULT_TIMEOUT = getattr(settings, "QUIZ_NEXT_QUESTION_CACHE_TIMEOUT", 120)

    @staticmethod
    def get_cache_key(session_id: int) -> str:
        return f'next_q:{session_id}'

    @staticmethod
    def cache_next_payload(session_id: int, payload: dict, timeout: int | None = None) -> bool:
        cache_key = QuizCacheService.get_cache_key(session_id)
        timeout = QuizCacheService.DEFAULT_TIMEOUT if timeout is None else timeout
        try:
            cache.set(cache_key, payload, timeout=timeout)
            logger.debug(f"Cached payload for session {session_id}")
            return True
        except (OSError, RuntimeError, TypeError, ValueError) as e:
            logger.exception(f"Failed to cache payload for session {session_id}: {e}")
            return False

    @staticmethod
    def get_cached_question(session_id: int):
        cache_key = QuizCacheService.get_cache_key(session_id)
        cached = cache.get(cache_key)

        if cached:
            logger.debug(f"Retrieved cached question for session {session_id}")

        return cached

    @staticmethod
    def delete_cached_question(session_id: int) -> None:
        cache_key = QuizCacheService.get_cache_key(session_id)
        cache.delete(cache_key)
        logger.debug(f"Deleted cached question for session {session_id}")

    @staticmethod
    def clear_session_cache(session_id: int) -> None:
        QuizCacheService.delete_cached_question(session_id)
