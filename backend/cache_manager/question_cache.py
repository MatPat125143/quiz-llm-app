from django.core.cache import cache
import hashlib
import json
import logging

logger = logging.getLogger('cache_manager')


class QuestionCache:
    def __init__(self):
        self.cache_timeout = 3600 * 24 * 7

    def _generate_cache_key(self, topic, difficulty, subtopic=None, knowledge_level=None):
        data = f"{topic}_{difficulty}_{subtopic or ''}_{knowledge_level or ''}"
        hash_key = hashlib.md5(data.encode()).hexdigest()
        return f"question_{hash_key}"

    def get_cached_question(self, topic, difficulty, subtopic=None, knowledge_level=None):
        cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.debug(f"Cache HIT: {cache_key}")
            return json.loads(cached_data)

        logger.debug(f"Cache MISS: {cache_key}")
        return None

    def cache_question(self, topic, difficulty, question_data, subtopic=None, knowledge_level=None):
        cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
        cache.set(cache_key, json.dumps(question_data), self.cache_timeout)
        logger.debug(f"Cached question: {cache_key}")

    def clear_cache(self, topic=None, difficulty=None, subtopic=None, knowledge_level=None):
        if all([topic, difficulty]):
            cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
            cache.delete(cache_key)
            logger.info(f"Cleared cache: {cache_key}")
        else:
            logger.warning("Clearing all question cache not implemented for safety")