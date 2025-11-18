"""
Serwis do generowania embeddingów pytań dla wykrywania duplikatów semantycznych.
"""


class EmbeddingsService:
    def __init__(self):
        """
        Inicjalizuje serwis embeddingów.
        Jeśli sentence-transformers nie jest zainstalowany, serwis będzie działał w trybie fallback.
        """
        self.model = None
        self.available = False

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.available = True
            print("✅ EmbeddingsService initialized successfully with sentence-transformers")
        except ImportError:
            print("⚠️  sentence-transformers not installed - semantic deduplication disabled")
            print("   Install with: pip install sentence-transformers")
            self.available = False
        except Exception as e:
            print(f"⚠️  Failed to initialize EmbeddingsService: {e}")
            self.available = False

    def encode_question(self, question_text):
        """
        Generuje embedding dla tekstu pytania.

        Args:
            question_text (str): Tekst pytania

        Returns:
            list: Embedding jako lista floatów, lub None jeśli serwis niedostępny
        """
        if not self.available or self.model is None:
            # Fallback: zwróć None jeśli embeddingi niedostępne
            return None

        try:
            embedding = self.model.encode(question_text)
            return embedding.tolist()
        except Exception as e:
            print(f"⚠️  Error encoding question: {e}")
            return None

    def is_available(self):
        """
        Sprawdza czy serwis embeddingów jest dostępny.

        Returns:
            bool: True jeśli embeddingi są dostępne
        """
        return self.available