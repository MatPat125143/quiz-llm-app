from llm_integration.question_generator import QuestionGenerator
from llm_integration.difficulty_adapter import DifficultyAdapter

from ..models import QuizSessionQuestion
from ..utils.constants import GENERATION_BUFFER_MIN_EXTRA, GENERATION_BUFFER_RATIO
from ..utils.helpers import get_used_hashes
from .question_service import QuestionService
from .cleanup_service import cleanup_rejected_question


class QuestionGenerationService:
    def __init__(self):
        self.generator = QuestionGenerator()
        self.difficulty_adapter = DifficultyAdapter()
        self.question_service = QuestionService()

    def compute_buffer_count(self, target_count):
        return max(
            target_count + GENERATION_BUFFER_MIN_EXTRA,
            int(target_count * GENERATION_BUFFER_RATIO),
        )

    def get_used_hashes(self, session):
        return get_used_hashes(session)

    def get_existing_questions_list(self, session):
        existing_session_questions = QuizSessionQuestion.objects.filter(
            session=session
        ).select_related('question').values_list('question__question_text', flat=True)
        return list(existing_session_questions) if existing_session_questions else None

    def get_difficulty_text(self, session):
        return self.difficulty_adapter.get_difficulty_level(session.current_difficulty)

    def generate_questions_data(
        self,
        session,
        difficulty_text,
        count,
        existing_questions,
    ):
        return self.generator.generate_multiple_questions(
            topic=session.topic,
            difficulty=difficulty_text,
            count=count,
            subtopic=session.subtopic,
            knowledge_level=session.knowledge_level,
            existing_questions=existing_questions,
        )

    def add_question_from_data(
        self,
        session,
        q_data,
        difficulty_text,
        order,
        used_hashes,
    ):
        question, _is_new = self.question_service.find_or_create_global_question(
            topic=session.topic,
            question_data=q_data,
            difficulty_text=difficulty_text,
            user=session.user,
            subtopic=session.subtopic,
            knowledge_level=session.knowledge_level,
        )

        if question.content_hash in used_hashes:
            cleanup_rejected_question(question, reason="hash_used_in_session")
            return None, order

        session_question = self.question_service.add_question_to_session(
            session=session,
            question=question,
            order=order,
        )

        if not session_question:
            cleanup_rejected_question(question, reason="duplicate_or_similar")
            return None, order

        used_hashes.add(question.content_hash)
        return question, order + 1
