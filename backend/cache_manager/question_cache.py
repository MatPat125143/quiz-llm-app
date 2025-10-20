from django.core.cache import cache
import hashlib
import json


class QuestionCache:
    def __init__(self):
        self.cache_timeout = 3600 * 24 * 7

    def _generate_cache_key(self, topic, difficulty):
        data = f"{topic}_{difficulty}"
        hash_key = hashlib.md5(data.encode()).hexdigest()
        return f"question_{hash_key}"

    def get_cached_question(self, topic, difficulty):
        cache_key = self._generate_cache_key(topic, difficulty)
        cached_data = cache.get(cache_key)

        if cached_data:
            return json.loads(cached_data)
        return None

    def cache_question(self, topic, difficulty, question_data):
        cache_key = self._generate_cache_key(topic, difficulty)
        cache.set(cache_key, json.dumps(question_data), self.cache_timeout)