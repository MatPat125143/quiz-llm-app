import logging
from .config import LLMConfig

logger = logging.getLogger(__name__)


class EmbeddingsService:
    def __init__(self):
        self.model = None
        self.available = False

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(LLMConfig.EMBEDDINGS_MODEL)
            self.available = True
            logger.info(
                "EmbeddingsService initialized successfully with sentence-transformers"
            )
        except ImportError:
            logger.warning(
                "sentence-transformers not installed - semantic deduplication disabled. "
                "Install with: pip install sentence-transformers"
            )
            self.available = False
        except (RuntimeError, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to initialize EmbeddingsService: {e}")
            self.available = False

    def encode_question(self, question_text):
        if not self.available or self.model is None:
            return None

        try:
            embedding = self.model.encode(question_text)
            return embedding.tolist()
        except (RuntimeError, ValueError, TypeError) as e:
            logger.error(f"Error encoding question: {e}")
            return None

    def is_available(self):
        return self.available
