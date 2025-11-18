import hashlib
import numpy as np
from llm_integration.embeddings_service import EmbeddingsService
from ..models import Question, QuizSessionQuestion

embeddings_service = EmbeddingsService()


class QuestionService:
    """Logika biznesowa dla generowania i zarządzania pytaniami"""

    def find_or_create_global_question(self, topic, question_data, difficulty_text, user=None, subtopic=None,
                                        knowledge_level=None):
        """Znajduje lub tworzy globalne pytanie z deduplikacją"""
        try:
            content = f"{question_data['question']}{question_data['correct_answer']}{topic}{subtopic or ''}{knowledge_level or ''}{difficulty_text}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            question, created = Question.objects.get_or_create(
                content_hash=content_hash,
                defaults={
                    'topic': topic,
                    'subtopic': subtopic,
                    'knowledge_level': knowledge_level,
                    'question_text': question_data['question'],
                    'correct_answer': question_data['correct_answer'],
                    'wrong_answer_1': question_data['wrong_answers'][0],
                    'wrong_answer_2': question_data['wrong_answers'][1],
                    'wrong_answer_3': question_data['wrong_answers'][2],
                    'explanation': question_data['explanation'],
                    'difficulty_level': difficulty_text,
                    'created_by': user
                }
            )

            if created and embeddings_service.is_available():
                try:
                    embedding = embeddings_service.encode_question(question_data['question'])
                    if embedding is not None:
                        print(f"📝 Created question ID={question.id} with embedding")
                    else:
                        print(f"📝 Created question ID={question.id} without embedding")
                except Exception as e:
                    print(f"⚠️ Embedding failed: {e}")
            elif created:
                print(f"📝 Created question ID={question.id}")
            else:
                print(f"✅ Reusing question ID={question.id} ({question.times_used}x)")
                question.times_used += 1
                question.save(update_fields=['times_used'])

            return question, created

        except KeyError as e:
            print(f"❌ Missing key in question_data: {e}")
            raise ValueError(f"Invalid question_data format: missing {e}")
        except Exception as e:
            print(f"❌ Error in find_or_create_global_question: {e}")
            raise

    def add_question_to_session(self, session, question, order=0):
        """Dodaje pytanie do sesji z sprawdzeniem duplikatów i podobieństwa"""
        existing = QuizSessionQuestion.objects.filter(
            session=session,
            question=question
        ).exists()

        if existing:
            print(f"⚠️ Question {question.id} already in session {session.id}")
            return None

        if embeddings_service.is_available():
            try:
                session_questions = QuizSessionQuestion.objects.filter(session=session).select_related('question')

                if session_questions.exists():
                    new_embedding = embeddings_service.encode_question(question.question_text)

                    if new_embedding is not None:
                        for sq in session_questions:
                            existing_embedding = embeddings_service.encode_question(sq.question.question_text)

                            if existing_embedding is not None:
                                similarity = np.dot(new_embedding, existing_embedding) / (
                                        np.linalg.norm(new_embedding) * np.linalg.norm(existing_embedding)
                                )

                                if similarity > 0.90:
                                    print(f"⚠️ Question {question.id} too similar to {sq.question.id} ({similarity:.2f})")
                                    return None

            except Exception as e:
                print(f"⚠️ Similarity check failed: {e}")

        session_question = QuizSessionQuestion.objects.create(
            session=session,
            question=question,
            order=order
        )

        print(f"✅ Added question {question.id} to session {session.id}")
        return session_question