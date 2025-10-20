from sentence_transformers import SentenceTransformer


class EmbeddingsService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def encode_question(self, question_text):
        embedding = self.model.encode(question_text)
        return embedding.tolist()