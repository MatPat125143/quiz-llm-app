"""
Konfiguracja dla systemu cache pytań quizowych
"""
import os


class CacheConfig:
    """Konfiguracja dla cache'owania pytań"""

    # Timeout dla cache (w sekundach)
    # Domyślnie: 7 dni = 3600 * 24 * 7 = 604800 sekund
    QUESTION_CACHE_TIMEOUT = int(os.getenv('QUESTION_CACHE_TIMEOUT', 604800))

    # Prefix dla kluczy cache
    CACHE_KEY_PREFIX = os.getenv('CACHE_KEY_PREFIX', 'question_')

    # Czy włączyć logowanie operacji cache
    CACHE_LOGGING_ENABLED = os.getenv('CACHE_LOGGING_ENABLED', 'True').lower() == 'true'

    @classmethod
    def get_timeout_days(cls):
        """Zwraca timeout w dniach"""
        return cls.QUESTION_CACHE_TIMEOUT / (3600 * 24)

    @classmethod
    def get_timeout_hours(cls):
        """Zwraca timeout w godzinach"""
        return cls.QUESTION_CACHE_TIMEOUT / 3600