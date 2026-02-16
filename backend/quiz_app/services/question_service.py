import hashlib
import logging
import numpy as np
from django.core.exceptions import MultipleObjectsReturned
from django.db import DatabaseError
from llm_integration.embeddings_service import EmbeddingsService
from ..models import Question, QuizSessionQuestion, Answer
from ..utils.deduplicator import UniversalDeduplicator
from .cleanup_service import cleanup_rejected_question

logger = logging.getLogger(__name__)
embeddings_service = EmbeddingsService()
deduplicator = UniversalDeduplicator()


class QuestionService:

    def _compute_similarity(self, embedding_a, embedding_b):
        return np.dot(embedding_a, embedding_b) / (
            np.linalg.norm(embedding_a) * np.linalg.norm(embedding_b)
        )

    def _answers_from_data(self, question_data):
        return [
            question_data['correct_answer'],
            question_data['wrong_answers'][0],
            question_data['wrong_answers'][1],
            question_data['wrong_answers'][2],
        ]

    def _answers_from_question(self, question):
        return [
            question.correct_answer,
            question.wrong_answer_1,
            question.wrong_answer_2,
            question.wrong_answer_3,
        ]

    def _get_candidate_questions(self, topic, difficulty_text, knowledge_level):
        return Question.objects.filter(
            topic=topic,
            difficulty_level=difficulty_text,
            knowledge_level=knowledge_level,
        ).exclude(embedding_vector__isnull=True)[:100]

    def _get_session_questions(self, session):
        return QuizSessionQuestion.objects.filter(
            session=session
        ).select_related('question')

    def _is_hash_used_in_session(self, session, content_hash):
        existing_by_hash = QuizSessionQuestion.objects.filter(
            session=session,
            question__content_hash=content_hash,
        ).exists()
        answered_by_hash = Answer.objects.filter(
            session=session,
            question__content_hash=content_hash,
        ).exists()
        return existing_by_hash or answered_by_hash

    def _find_similar_question_in_database(
        self,
        question_text,
        answers_list,
        topic,
        difficulty_text,
        knowledge_level=None,
    ):
        if not embeddings_service.is_available():
            return None

        try:
            adaptive_threshold = deduplicator.get_adaptive_threshold(question_text)
            logger.debug(f"Adaptive similarity threshold: {adaptive_threshold :.2f}")

            new_embedding = embeddings_service.encode_question(question_text)
            if new_embedding is None:
                return None

            candidate_questions = self._get_candidate_questions(
                topic=topic,
                difficulty_text=difficulty_text,
                knowledge_level=knowledge_level,
            )

            best_match = None
            best_similarity = adaptive_threshold
            best_reason = None

            for candidate in candidate_questions:
                if candidate.embedding_vector:
                    candidate_embedding = np.array(candidate.embedding_vector)
                    semantic_similarity = self._compute_similarity(
                        new_embedding, candidate_embedding
                    )
                    candidate_answers = self._answers_from_question(candidate)

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
                logger.info(
                    f"Found similar question {best_match.id}, "
                    f"similarity={best_similarity :.3f}, reason={best_reason}"
                )
                return best_match

        except (DatabaseError, ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Error searching for similar questions: {e}")

        return None

    def find_or_create_global_question(
        self,
        topic,
        question_data,
        difficulty_text,
        user=None,
        subtopic=None,
        knowledge_level=None,
    ):
        try:
            content_hash = Question.build_content_hash(
                question_text=question_data['question'],
                correct_answer=question_data['correct_answer'],
                topic=topic,
                subtopic=subtopic,
                knowledge_level=knowledge_level,
                difficulty_level=difficulty_text,
            )

            try:
                question = Question.objects.get(content_hash=content_hash)
                logger.debug(
                    f"Exact match found: question {question.id}, used {question.times_used}x"
                )
                return question, False
            except Question.DoesNotExist:
                pass

            answers_list = self._answers_from_data(question_data)

            similar_question = self._find_similar_question_in_database(
                question_data['question'],
                answers_list,
                topic,
                difficulty_text,
                knowledge_level
            )

            if similar_question:
                logger.info(f"Reusing similar question {similar_question.id}")
                return similar_question, False

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
                except (RuntimeError, TypeError, ValueError) as e:
                    logger.warning(f"Embedding generation failed: {e}")
            else:
                logger.debug(f"Created question {question.id}")

            return question, True

        except KeyError as e:
            logger.error(f"Missing key in question_data: {e}")
            raise ValueError(f"Invalid question_data format: missing {e}")
        except (DatabaseError, MultipleObjectsReturned, ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Error in find_or_create_global_question: {e}")
            raise

    def add_question_to_session(self, session, question, order=0):
        if self._is_hash_used_in_session(session, question.content_hash):
            logger.debug(
                f"Question hash {question.content_hash} already used in session {session.id}"
            )
            cleanup_rejected_question(question, reason="hash_used_in_session")
            return None

        if embeddings_service.is_available():
            try:
                session_questions = self._get_session_questions(session)

                if session_questions.exists():
                    new_embedding = embeddings_service.encode_question(question.question_text)

                    if new_embedding is not None:

                        new_answers = self._answers_from_question(question)

                        for sq in session_questions:
                            existing_embedding = embeddings_service.encode_question(sq.question.question_text)

                            if existing_embedding is not None:
                                semantic_similarity = self._compute_similarity(
                                    new_embedding, existing_embedding
                                )
                                existing_answers = self._answers_from_question(sq.question)

                                is_dup, reason, confidence = deduplicator.is_duplicate(
                                    question.question_text,
                                    new_answers,
                                    sq.question.question_text,
                                    existing_answers,
                                    semantic_similarity
                                )

                                if is_dup:
                                    logger.debug(
                                        f"Question {question.id} is duplicate of {sq.question.id}, "
                                        f"reason: {reason}, confidence: {confidence :.2f}"
                                    )
                                    cleanup_rejected_question(
                                        question, reason="similar_in_session"
                                    )
                                    return None

            except (DatabaseError, ValueError, TypeError, RuntimeError) as e:
                logger.warning(f"Similarity check failed: {e}")

        session_question = QuizSessionQuestion.objects.create(
            session=session,
            question=question,
            order=order
        )

        logger.debug(f"Added question {question.id} to session {session.id}")
        return session_question
