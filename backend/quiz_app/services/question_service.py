import hashlib
import numpy as np
import logging
from llm_integration.embeddings_service import EmbeddingsService
from ..models import Question, QuizSessionQuestion
from ..utils.deduplicator import UniversalDeduplicator

logger = logging.getLogger(__name__)
embeddings_service = EmbeddingsService()
deduplicator = UniversalDeduplicator()


class QuestionService:
    """Logika biznesowa dla generowania i zarządzania pytaniami"""

    def _find_similar_question_in_database(self, question_text, answers_list, topic, difficulty_text, knowledge_level=None):
        """
        Szuka podobnego pytania w bazie danych używając UNIVERSAL multi-level deduplication.
        Works for ALL question types: math, history, geography, definitions, etc.

        Args:
            question_text: Tekst nowego pytania
            answers_list: Lista wszystkich odpowiedzi [correct, wrong1, wrong2, wrong3]
            topic: Temat
            difficulty_text: Poziom trudności
            knowledge_level: Poziom wiedzy

        Returns:
            Question object jeśli znaleziono podobne, None w przeciwnym razie
        """
        if not embeddings_service.is_available():
            return None

        try:
            adaptive_threshold = deduplicator.get_adaptive_threshold(question_text)
            logger.debug(f"Adaptive similarity threshold: {adaptive_threshold:.2f}")

            # Wygeneruj embedding dla nowego pytania
            new_embedding = embeddings_service.encode_question(question_text)
            if new_embedding is None:
                return None

            # Pobierz podobne pytania z bazy (ten sam temat i poziom trudności)
            candidate_questions = Question.objects.filter(
                topic=topic,
                difficulty_level=difficulty_text,
                knowledge_level=knowledge_level
            ).exclude(
                embedding_vector__isnull=True
            )[:100]  # Ogranicz do 100 najnowszych dla wydajności

            best_match = None
            best_similarity = adaptive_threshold
            best_reason = None

            for candidate in candidate_questions:
                if candidate.embedding_vector:
                    candidate_embedding = np.array(candidate.embedding_vector)
                    semantic_similarity = np.dot(new_embedding, candidate_embedding) / (
                        np.linalg.norm(new_embedding) * np.linalg.norm(candidate_embedding)
                    )

                    # Get candidate answers
                    candidate_answers = [
                        candidate.correct_answer,
                        candidate.wrong_answer_1,
                        candidate.wrong_answer_2,
                        candidate.wrong_answer_3
                    ]

                    # UNIVERSAL MULTI-LEVEL CHECK
                    is_dup, reason, confidence = deduplicator.is_duplicate(
                        question_text,
                        answers_list,
                        candidate.question_text,
                        candidate_answers,
                        semantic_similarity
                    )

                    if is_dup and confidence > best_similarity:
                        best_similarity = confidence
                        best_match = candidate
                        best_reason = reason

            if best_match:
                logger.info(f"Found similar question {best_match.id}, similarity={best_similarity:.3f}, reason={best_reason}")
                return best_match

        except Exception as e:
            logger.error(f"Error searching for similar questions: {e}")

        return None

    def find_or_create_global_question(self, topic, question_data, difficulty_text, user=None, subtopic=None,
                                        knowledge_level=None):
        """Znajduje lub tworzy globalne pytanie z UNIVERSAL multi-level deduplikacją"""
        try:
            content = f"{question_data['question']}{question_data['correct_answer']}{topic}{subtopic or ''}{knowledge_level or ''}{difficulty_text}"
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            try:
                question = Question.objects.get(content_hash=content_hash)
                logger.debug(f"Exact match found: question {question.id}, used {question.times_used}x")
                question.times_used += 1
                question.save(update_fields=['times_used'])
                return question, False
            except Question.DoesNotExist:
                pass

            # Prepare answers list for universal deduplicator
            answers_list = [
                question_data['correct_answer'],
                question_data['wrong_answers'][0],
                question_data['wrong_answers'][1],
                question_data['wrong_answers'][2]
            ]

            # KROK 2: UNIVERSAL multi-level similarity check
            similar_question = self._find_similar_question_in_database(
                question_data['question'],
                answers_list,
                topic,
                difficulty_text,
                knowledge_level
            )

            if similar_question:
                logger.info(f"Reusing similar question {similar_question.id}")
                similar_question.times_used += 1
                similar_question.save(update_fields=['times_used'])
                return similar_question, False

            # KROK 3: Utwórz nowe pytanie
            question = Question.objects.create(
                content_hash=content_hash,
                topic=topic,
                subtopic=subtopic,
                knowledge_level=knowledge_level,
                question_text=question_data['question'],
                correct_answer=question_data['correct_answer'],
                wrong_answer_1=question_data['wrong_answers'][0],
                wrong_answer_2=question_data['wrong_answers'][1],
                wrong_answer_3=question_data['wrong_answers'][2],
                explanation=question_data['explanation'],
                difficulty_level=difficulty_text,
                created_by=user
            )

            if embeddings_service.is_available():
                try:
                    embedding = embeddings_service.encode_question(question_data['question'])
                    if embedding is not None:
                        question.embedding_vector = embedding
                        question.save(update_fields=['embedding_vector'])
                        logger.info(f"Created question {question.id} with embedding")
                    else:
                        logger.debug(f"Created question {question.id} without embedding")
                except Exception as e:
                    logger.warning(f"Embedding generation failed: {e}")
            else:
                logger.debug(f"Created question {question.id}")

            return question, True

        except KeyError as e:
            logger.error(f"Missing key in question_data: {e}")
            raise ValueError(f"Invalid question_data format: missing {e}")
        except Exception as e:
            logger.error(f"Error in find_or_create_global_question: {e}")
            raise

    def add_question_to_session(self, session, question, order=0):
        """Dodaje pytanie do sesji z UNIVERSAL multi-level sprawdzeniem duplikatów"""
        existing = QuizSessionQuestion.objects.filter(
            session=session,
            question=question
        ).exists()

        if existing:
            logger.debug(f"Question {question.id} already in session {session.id}")
            self._cleanup_rejected_question(question)
            return None

        if embeddings_service.is_available():
            try:
                session_questions = QuizSessionQuestion.objects.filter(session=session).select_related('question')

                if session_questions.exists():
                    new_embedding = embeddings_service.encode_question(question.question_text)

                    if new_embedding is not None:
                        # Prepare new question answers
                        new_answers = [
                            question.correct_answer,
                            question.wrong_answer_1,
                            question.wrong_answer_2,
                            question.wrong_answer_3
                        ]

                        for sq in session_questions:
                            existing_embedding = embeddings_service.encode_question(sq.question.question_text)

                            if existing_embedding is not None:
                                semantic_similarity = np.dot(new_embedding, existing_embedding) / (
                                        np.linalg.norm(new_embedding) * np.linalg.norm(existing_embedding)
                                )

                                # Prepare existing question answers
                                existing_answers = [
                                    sq.question.correct_answer,
                                    sq.question.wrong_answer_1,
                                    sq.question.wrong_answer_2,
                                    sq.question.wrong_answer_3
                                ]

                                # UNIVERSAL multi-level duplicate check
                                is_dup, reason, confidence = deduplicator.is_duplicate(
                                    question.question_text,
                                    new_answers,
                                    sq.question.question_text,
                                    existing_answers,
                                    semantic_similarity
                                )

                                if is_dup:
                                    logger.debug(f"Question {question.id} is duplicate of {sq.question.id}, reason: {reason}, confidence: {confidence:.2f}")
                                    self._cleanup_rejected_question(question)
                                    return None

            except Exception as e:
                logger.warning(f"Similarity check failed: {e}")

        session_question = QuizSessionQuestion.objects.create(
            session=session,
            question=question,
            order=order
        )

        logger.debug(f"Added question {question.id} to session {session.id}")
        return session_question

    def _cleanup_rejected_question(self, question):
        """Usuwa odrzucone pytanie jeśli nie ma żadnych odpowiedzi"""
        if question.total_answers == 0:
            used_in_active = QuizSessionQuestion.objects.filter(
                question=question,
                session__is_completed=False
            ).exists()

            if not used_in_active:
                logger.debug(f"Deleting orphaned question {question.id}")
                question.delete()
            else:
                logger.debug(f"Keeping question {question.id}, used in active session")