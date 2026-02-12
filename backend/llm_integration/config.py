import os


class LLMConfig:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
    OPENAI_MAX_TOKENS_MULTIPLE = int(os.getenv("OPENAI_MAX_TOKENS_MULTIPLE", "2000"))

    EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")

    TEMPERATURE_SINGLE = 0.8
    TEMPERATURE_MULTIPLE = 0.9

    @classmethod
    def is_openai_available(cls):
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != "sk-your-openai-api-key-here")

    @classmethod
    def get_openai_params_single(cls):
        return {
            'model': cls.OPENAI_MODEL,
            'temperature': cls.TEMPERATURE_SINGLE,
            'max_tokens': cls.OPENAI_MAX_TOKENS
        }

    @classmethod
    def get_openai_params_multiple(cls):
        return {
            'model': cls.OPENAI_MODEL,
            'temperature': cls.TEMPERATURE_MULTIPLE,
            'max_tokens': cls.OPENAI_MAX_TOKENS_MULTIPLE
        }
