"""
Konfiguracja dla integracji z LLM (Large Language Models)
"""
import os


class LLMConfig:
    """Konfiguracja dla OpenAI i innych modeli LLM"""

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.8"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
    OPENAI_MAX_TOKENS_MULTIPLE = int(os.getenv("OPENAI_MAX_TOKENS_MULTIPLE", "2000"))

    # Embeddings Configuration
    EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    EMBEDDINGS_SIMILARITY_THRESHOLD = float(os.getenv("EMBEDDINGS_SIMILARITY_THRESHOLD", "0.90"))

    # Question Generation Settings
    TEMPERATURE_SINGLE = 0.8  # Dla pojedynczych pytań
    TEMPERATURE_MULTIPLE = 0.9  # Dla wielu pytań (więcej różnorodności)

    @classmethod
    def is_openai_available(cls):
        """Sprawdź czy klucz OpenAI jest dostępny"""
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != "sk-your-openai-api-key-here")

    @classmethod
    def get_openai_params_single(cls):
        """Pobierz parametry dla pojedynczego pytania"""
        return {
            'model': cls.OPENAI_MODEL,
            'temperature': cls.TEMPERATURE_SINGLE,
            'max_tokens': cls.OPENAI_MAX_TOKENS
        }

    @classmethod
    def get_openai_params_multiple(cls):
        """Pobierz parametry dla wielu pytań"""
        return {
            'model': cls.OPENAI_MODEL,
            'temperature': cls.TEMPERATURE_MULTIPLE,
            'max_tokens': cls.OPENAI_MAX_TOKENS_MULTIPLE
        }