from llm_integration.question_generator import QuestionGenerator
from llm_integration.difficulty_adapter import DifficultyAdapter
from .question_service import QuestionService

generator = QuestionGenerator()
difficulty_adapter = DifficultyAdapter()
question_service = QuestionService()


class QuizService:
    """Logika biznesowa dla tworzenia i zarządzania quizami"""

    def generate_initial_batch(self, session, to_generate, initial_difficulty, user):
        """Generuje pierwszą partię pytań dla nowej sesji quizu"""
        all_questions_data = generator.generate_multiple_questions(
            session.topic,
            initial_difficulty,
            to_generate,
            subtopic=session.subtopic if session.subtopic else None,
            knowledge_level=session.knowledge_level
        )

        difficulty_text = difficulty_adapter.get_difficulty_level(initial_difficulty)

        created_count = 0
        reused_count = 0

        for order, question_data in enumerate(all_questions_data):
            question, was_created = question_service.find_or_create_global_question(
                session.topic,
                question_data,
                difficulty_text,
                user=user,
                subtopic=session.subtopic if session.subtopic else None,
                knowledge_level=session.knowledge_level
            )

            if was_created:
                created_count += 1
            else:
                reused_count += 1

            question_service.add_question_to_session(session, question, order=order)

        session.questions_generated_count = to_generate
        session.save(update_fields=['questions_generated_count'])

        print(f"✅ First batch: {created_count} new, {reused_count} reused")