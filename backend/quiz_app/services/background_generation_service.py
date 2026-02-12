import logging
import threading
from django.db import DatabaseError, IntegrityError, transaction
from ..models import QuizSession, QuizSessionQuestion
from ..utils.constants import BACKGROUND_BATCH_SIZE
from .question_generation_service import QuestionGenerationService

logger = logging.getLogger(__name__)


class BackgroundGenerationService:

    def __init__(self):
        self.core = QuestionGenerationService()

    def generate_initial_questions_sync(self, session, count=2):
        logger.info(f"Generating {count} questions synchronously for session {session.id}")

        difficulty_text = self.core.get_difficulty_text(session)
        buffer_count = self.core.compute_buffer_count(count)
        logger.debug(
            f"Generating {buffer_count} questions (target: {count}, "
            f"buffer: +{buffer_count - count} for rejections)"
        )

        questions_data = self.core.generate_questions_data(
            session=session,
            difficulty_text=difficulty_text,
            count=buffer_count,
            existing_questions=None,
        )

        created_questions = []
        used_hashes = self.core.get_used_hashes(session)
        order = 0

        for q_data in questions_data:

            current_total_in_session = QuizSessionQuestion.objects.filter(session=session).count()
            if current_total_in_session >= session.questions_count:
                logger.warning(
                    f"Session already has {current_total_in_session} questions "
                    f"(limit: {session.questions_count}), stopping"
                )
                break

            if len(created_questions) >= count:
                logger.debug(f"Reached target count ({count}), stopping")
                break

            try:

                question, order = self.core.add_question_from_data(
                    session=session,
                    q_data=q_data,
                    difficulty_text=difficulty_text,
                    order=order,
                    used_hashes=used_hashes,
                )

                if question:
                    created_questions.append(question)
                    logger.debug(
                        f"Added question {question.id} to session {session.id} "
                        f"(order={order}, progress={len(created_questions)}/{count})"
                    )
                else:
                    logger.warning("Question rejected (duplicate or too similar)")

            except (DatabaseError, IntegrityError, ValueError, TypeError, RuntimeError, KeyError) as e:
                logger.error(f"Error creating question: {e}")
                continue

        session.questions_generated_count = len(created_questions)
        session.save(update_fields=['questions_generated_count'])

        logger.info(f"Generated {len(created_questions)} questions synchronously")
        return created_questions

    def generate_remaining_questions_async(self, session_id, total_needed, already_generated):
        remaining = total_needed - already_generated

        if remaining <= 0:
            logger.info(f"All questions already generated for session {session_id}")
            return

        logger.info(f"Starting async generation of {remaining} questions for session {session_id}")

        thread = threading.Thread(
            target=self._generate_questions_in_background,
            args=(session_id, remaining, already_generated),
            daemon=True
        )
        thread.start()
        logger.debug(f"Background thread started for session {session_id}")

    def _generate_questions_in_background(self, session_id, count, start_order):
        try:

            from django.db import connection
            connection.close()

            session = QuizSession.objects.get(id=session_id)
            difficulty_text = self.core.get_difficulty_text(session)

            current_question_count = QuizSessionQuestion.objects.filter(session=session).count()
            max_questions_allowed = session.questions_count

            actual_needed = max_questions_allowed - current_question_count

            if actual_needed <= 0:
                logger.info(
                    f"Background: Session {session_id} already has enough questions "
                    f"({current_question_count}/{max_questions_allowed})"
                )
                return

            count = min(count, actual_needed)

            existing_questions_list = self.core.get_existing_questions_list(session)
            used_hashes = self.core.get_used_hashes(session)

            logger.info(
                f"Background: Generating {count} questions for session {session_id} "
                f"(currently: {current_question_count}/{max_questions_allowed})"
            )
            logger.debug(
                f"Background: Context - "
                f"{len(existing_questions_list) if existing_questions_list else 0} existing questions"
            )

            batch_size = min(BACKGROUND_BATCH_SIZE, count)
            total_generated = 0
            order = start_order

            while total_generated < count:

                current_count_check = QuizSessionQuestion.objects.filter(session=session).count()
                if current_count_check >= max_questions_allowed:
                    logger.warning(
                        f"Background: Limit reached "
                        f"({current_count_check}/{max_questions_allowed}), stopping generation"
                    )
                    break

                remaining = count - total_generated
                current_batch = min(batch_size, remaining)

                buffer_batch = min(current_batch + 1, remaining + 1)

                logger.debug(
                    f"Background: Generating batch of {buffer_batch} questions "
                    f"(target: {current_batch}, progress: {total_generated}/{count})"
                )

                questions_data = self.core.generate_questions_data(
                    session=session,
                    difficulty_text=difficulty_text,
                    count=buffer_batch,
                    existing_questions=existing_questions_list,
                )

                batch_added = 0
                for q_data in questions_data:

                    if batch_added >= current_batch:
                        logger.debug(
                            f"Background: Reached batch target ({batch_added}/{current_batch}), "
                            f"moving to next batch"
                        )
                        break

                    if total_generated >= count:
                        logger.warning(
                            f"Background: Reached total target count ({total_generated}/{count}), stopping"
                        )
                        break

                    current_total = QuizSessionQuestion.objects.filter(session=session).count()
                    if current_total >= max_questions_allowed:
                        logger.warning(
                            f"Background: Session limit reached "
                            f"({current_total}/{max_questions_allowed}), stopping"
                        )
                        break

                    try:
                        with transaction.atomic():
                            question, order = self.core.add_question_from_data(
                                session=session,
                                q_data=q_data,
                                difficulty_text=difficulty_text,
                                order=order,
                                used_hashes=used_hashes,
                            )

                            if question:
                                total_generated += 1
                                batch_added += 1

                                if existing_questions_list is None:
                                    existing_questions_list = []
                                existing_questions_list.append(q_data['question'])

                                logger.debug(
                                    f"Background: Added question {question.id} "
                                    f"(batch: {batch_added}/{current_batch}, total: {total_generated}/{count})"
                                )
                            else:
                                logger.warning(
                                    "Background: Question rejected (duplicate or similar)"
                                )
                    except (DatabaseError, IntegrityError, ValueError, TypeError, RuntimeError, KeyError) as e:
                        logger.error(f"Background: Error creating question: {e}")
                        continue

            session.questions_generated_count = start_order + total_generated
            session.save(update_fields=['questions_generated_count'])

            logger.info(
                f"Background: Completed! Generated {total_generated} questions for session {session_id}"
            )

        except (DatabaseError, IntegrityError, ValueError, TypeError, RuntimeError, QuizSession.DoesNotExist) as e:
            logger.error(f"Background generation failed for session {session_id}: {e}")
            import traceback
            traceback.print_exc()

    def generate_adaptive_questions_sync(self, session, new_difficulty_level, count=5):
        logger.info(
            f"Generating {count} adaptive questions for level: {new_difficulty_level}"
        )

        existing_questions_list = self.core.get_existing_questions_list(session)
        used_hashes = self.core.get_used_hashes(session)

        buffer_count = self.core.compute_buffer_count(count)
        logger.debug(
            f"Generating {buffer_count} adaptive questions (target: {count}, "
            f"buffer: +{buffer_count - count} for rejections)"
        )

        questions_data = self.core.generate_questions_data(
            session=session,
            difficulty_text=new_difficulty_level,
            count=buffer_count,
            existing_questions=existing_questions_list,
        )

        max_order = QuizSessionQuestion.objects.filter(session=session).count()
        order = max_order

        generated_count = 0

        for q_data in questions_data:

            current_total_in_session = QuizSessionQuestion.objects.filter(session=session).count()
            if current_total_in_session >= session.questions_count:
                logger.warning(
                    f"Session already has {current_total_in_session} questions "
                    f"(limit: {session.questions_count}), stopping adaptive generation"
                )
                break

            if generated_count >= count:
                logger.debug(f"Reached target adaptive count ({count}), stopping")
                break

            try:
                question, order = self.core.add_question_from_data(
                    session=session,
                    q_data=q_data,
                    difficulty_text=new_difficulty_level,
                    order=order,
                    used_hashes=used_hashes,
                )

                if question:
                    generated_count += 1
                    logger.debug(
                        f"Added adaptive question {question.id} "
                        f"(level={new_difficulty_level}, progress={generated_count}/{count})"
                    )
                else:
                    logger.warning(
                        "Adaptive question rejected (duplicate or too similar)"
                    )

            except (DatabaseError, IntegrityError, ValueError, TypeError, RuntimeError, KeyError) as e:
                logger.error(f"Error creating adaptive question: {e}")
                continue

        logger.info(f"Generated {generated_count} adaptive questions")
        return generated_count
