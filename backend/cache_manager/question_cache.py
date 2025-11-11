from django.core.cache import cache
import hashlib
import json


class QuestionCache:
    def __init__(self):
        self.cache_timeout = 3600 * 24 * 7  # 7 dni

    def _generate_cache_key(self, topic, difficulty, subtopic=None, knowledge_level=None):
        """
        Generuje klucz cache uwzględniający temat, trudność, podtemat i poziom wiedzy.
        """
        data = f"{topic}_{difficulty}_{subtopic or ''}_{knowledge_level or ''}"
        hash_key = hashlib.md5(data.encode()).hexdigest()
        return f"question_{hash_key}"

    def get_cached_question(self, topic, difficulty, subtopic=None, knowledge_level=None):
        """
        Pobiera pytanie z cache.
        """
        cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
        cached_data = cache.get(cache_key)

        if cached_data:
            print(f"⚡ Cache HIT: {cache_key}")
            return json.loads(cached_data)

        print(f"❌ Cache MISS: {cache_key}")
        return None

    def cache_question(self, topic, difficulty, question_data, subtopic=None, knowledge_level=None):
        """
        Zapisuje pytanie do cache.
        """
        cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
        cache.set(cache_key, json.dumps(question_data), self.cache_timeout)
        print(f"💾 Cached question: {cache_key}")

    def clear_cache(self, topic=None, difficulty=None, subtopic=None, knowledge_level=None):
        """
        Czyści cache dla danego tematu/trudności (opcjonalnie).
        """
        if all([topic, difficulty]):
            cache_key = self._generate_cache_key(topic, difficulty, subtopic, knowledge_level)
            cache.delete(cache_key)
            print(f"🗑️ Cleared cache: {cache_key}")
        else:
            # Wyczyść cały cache pytań (niebezpieczne!)
            print("⚠️ Clearing all question cache not implemented for safety")