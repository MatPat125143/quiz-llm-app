from django.core.cache import cache
import hashlib
import json
from .config import CacheConfig


class QuestionCache:
    """Klasa do cache'owania pytań quizowych"""

    def __init__(self):
        """Inicjalizacja cache pytań"""
        self.cache_timeout = CacheConfig.QUESTION_CACHE_TIMEOUT
        self.cache_prefix = CacheConfig.CACHE_KEY_PREFIX
        self.logging_enabled = CacheConfig.CACHE_LOGGING_ENABLED

    def get_cached_question(self, topic, difficulty, subtopic=None, knowledge_level=None):
        """
        Pobiera pytanie z cache.

        Args:
            topic (str): Temat pytania
            difficulty (str): Poziom trudności
            subtopic (str, optional): Podtemat
            knowledge_level (str, optional): Poziom wiedzy

        Returns:
            dict or None: Dane pytania lub None jeśli brak w cache
        """
        cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
        cached_data = cache.get(cache_key)

        if cached_data:
            self._log(f"⚡ Cache HIT: {cache_key}")
            return json.loads(cached_data)

        self._log(f"❌ Cache MISS: {cache_key}")
        return None

    def cache_question(self, topic, difficulty, question_data, subtopic=None, knowledge_level=None):
        """
        Zapisuje pytanie do cache.

        Args:
            topic (str): Temat pytania
            difficulty (str): Poziom trudności
            question_data (dict): Dane pytania do cache'owania
            subtopic (str, optional): Podtemat
            knowledge_level (str, optional): Poziom wiedzy
        """
        cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
        cache.set(cache_key, json.dumps(question_data), self.cache_timeout)
        self._log(f"💾 Cached question: {cache_key}")

    def clear_cache(self, topic=None, difficulty=None, subtopic=None, knowledge_level=None):
        """
        Czyści cache dla danego tematu/trudności.

        Args:
            topic (str, optional): Temat
            difficulty (str, optional): Trudność
            subtopic (str, optional): Podtemat
            knowledge_level (str, optional): Poziom wiedzy
        """
        if all([topic, difficulty]):
            cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
            cache.delete(cache_key)
            self._log(f"🗑️ Cleared cache: {cache_key}")
        else:
            # Wyczyść cały cache pytań (niebezpieczne!)
            self._log("⚠️ Clearing all question cache not implemented for safety")

    def _generate_cache_key(self, topic, difficulty, subtopic=None, knowledge_level=None):
        """
        Generuje klucz cache uwzględniający temat, trudność, podtemat i poziom wiedzy.

        Args:
            topic (str): Temat
            difficulty (str): Trudność
            subtopic (str, optional): Podtemat
            knowledge_level (str, optional): Poziom wiedzy

        Returns:
            str: Klucz cache
        """
        data = f"{topic}_{difficulty}_{subtopic or ''}_{knowledge_level or ''}"
        hash_key = hashlib.md5(data.encode()).hexdigest()
        return f"{self.cache_prefix}{hash_key}"

    def _log(self, message):
        """Loguje wiadomość jeśli logging jest włączony"""
        if self.logging_enabled:
            print(message)