"""
Serwis do asynchronicznego generowania pytań w tle
"""
import logging
import threading
from django.db import transaction
from llm_integration.question_generator import QuestionGenerator
from llm_integration.difficulty_adapter import DifficultyAdapter
from .question_service import QuestionService
from ..models import QuizSession, QuizSessionQuestion

logger = logging.getLogger(__name__)


class BackgroundQuestionGenerator:
    """
    Generuje pytania w tle używając threading.
    Strategia: Generuj 2-3 pytania SYNC, resztę ASYNC
    """

    def __init__(self):
        self.generator = QuestionGenerator()
        self.difficulty_adapter = DifficultyAdapter()
        self.question_service = QuestionService()

    def generate_initial_questions_sync(self, session, count=2):
        """
        Generuje początkowe pytania SYNCHRONICZNIE.

        Args:
            session: QuizSession object
            count: Ile pytań wygenerować (domyślnie 2)

        Returns:
            list: Lista utworzonych Question objects
        """
        logger.info(f"Generating {count} questions synchronously for session {session.id}")

        difficulty_text = self.difficulty_adapter.get_difficulty_level(session.current_difficulty)

        # Generuj NIEWIELE więcej niż potrzeba (+10% lub +1) jako bufor na odrzucone
        # UWAGA: Zmniejszono z +30% na +10% aby zmniejszyć ilość orphaned questions
        buffer_count = max(count + 1, int(count * 1.1))
        logger.debug(f"Generating {buffer_count} questions (target: {count}, buffer: +{buffer_count - count} for rejections)")

        # Generuj pytania
        questions_data = self.generator.generate_multiple_questions(
            topic=session.topic,
            difficulty=difficulty_text,
            count=buffer_count,
            subtopic=session.subtopic,
            knowledge_level=session.knowledge_level,
            existing_questions=None
        )

        created_questions = []
        order = 0

        for q_data in questions_data:
            # KRYTYCZNE: Sprawdź limit PRZED przetwarzaniem
            current_total_in_session = QuizSessionQuestion.objects.filter(session=session).count()
            if current_total_in_session >= session.questions_count:
                logger.warning(f"Session already has {current_total_in_session} questions (limit: {session.questions_count}), stopping")
                break

            # ZATRZYMAJ SIĘ gdy osiągniesz cel lokalny
            if len(created_questions) >= count:
                logger.debug(f"Reached target count ({count}), stopping")
                break

            try:
                # Znajdź lub utwórz pytanie w bazie
                question, is_new = self.question_service.find_or_create_global_question(
                    topic=session.topic,
                    question_data=q_data,
                    difficulty_text=difficulty_text,
                    user=session.user,
                    subtopic=session.subtopic,
                    knowledge_level=session.knowledge_level
                )

                # Dodaj do sesji
                session_question = self.question_service.add_question_to_session(
                    session=session,
                    question=question,
                    order=order
                )

                if session_question:
                    created_questions.append(question)
                    order += 1
                    logger.debug(f"Added question {question.id} to session {session.id} (order={order}, progress={len(created_questions)}/{count})")
                else:
                    logger.warning(f"Question {question.id} rejected (duplicate or too similar)")

            except Exception as e:
                logger.error(f"Error creating question: {e}")
                continue

        # Aktualizuj licznik wygenerowanych pytań
        session.questions_generated_count = len(created_questions)
        session.save(update_fields=['questions_generated_count'])

        logger.info(f"Generated {len(created_questions)} questions synchronously")
        return created_questions

    def generate_remaining_questions_async(self, session_id, total_needed, already_generated):
        """
        Generuje pozostałe pytania ASYNCHRONICZNIE w background thread.

        Args:
            session_id: ID sesji quizowej
            total_needed: Całkowita liczba pytań potrzebnych w grze
            already_generated: Ile pytań już wygenerowano
        """
        remaining = total_needed - already_generated

        if remaining <= 0:
            logger.info(f"All questions already generated for session {session_id}")
            return

        logger.info(f"Starting async generation of {remaining} questions for session {session_id}")

        # Uruchom w osobnym wątku
        thread = threading.Thread(
            target=self._generate_questions_in_background,
            args=(session_id, remaining, already_generated),
            daemon=True
        )
        thread.start()
        logger.debug(f"Background thread started for session {session_id}")

    def _generate_questions_in_background(self, session_id, count, start_order):
        """
        Wewnętrzna metoda do generowania pytań w tle.
        UWAGA: Działa w osobnym wątku!
        """
        try:
            # Pobierz sesję (w osobnym wątku, więc nowe połączenie DB)
            from django.db import connection
            connection.close()  # Zamknij stare połączenie

            session = QuizSession.objects.get(id=session_id)
            difficulty_text = self.difficulty_adapter.get_difficulty_level(session.current_difficulty)

            # KRYTYCZNE: Sprawdź ile pytań już jest w sesji
            current_question_count = QuizSessionQuestion.objects.filter(session=session).count()
            max_questions_allowed = session.questions_count

            # Oblicz ile faktycznie potrzeba
            actual_needed = max_questions_allowed - current_question_count

            if actual_needed <= 0:
                logger.info(f"Background: Session {session_id} already has enough questions ({current_question_count}/{max_questions_allowed})")
                return

            # Ogranicz count do rzeczywistej potrzeby
            count = min(count, actual_needed)

            # Pobierz już zadane pytania (dla kontekstu)
            existing_session_questions = QuizSessionQuestion.objects.filter(
                session=session
            ).select_related('question').values_list('question__question_text', flat=True)

            existing_questions_list = list(existing_session_questions) if existing_session_questions else None

            logger.info(f"Background: Generating {count} questions for session {session_id} (currently: {current_question_count}/{max_questions_allowed})")
            logger.debug(f"Background: Context - {len(existing_questions_list) if existing_questions_list else 0} existing questions")

            # Generuj pytania batch'ami po 5 (żeby nie przeciążyć API)
            batch_size = min(5, count)
            total_generated = 0
            order = start_order

            while total_generated < count:
                # DODATKOWE SPRAWDZENIE - czy nie przekroczyliśmy limitu
                current_count_check = QuizSessionQuestion.objects.filter(session=session).count()
                if current_count_check >= max_questions_allowed:
                    logger.warning(f"Background: Limit reached ({current_count_check}/{max_questions_allowed}), stopping generation")
                    break

                remaining = count - total_generated
                current_batch = min(batch_size, remaining)

                # Generuj z małym buforem (+1) dla odrzuconych
                # UWAGA: Zmniejszono bufor aby zmniejszyć orphaned questions
                buffer_batch = min(current_batch + 1, remaining + 1)

                logger.debug(f"Background: Generating batch of {buffer_batch} questions (target: {current_batch}, progress: {total_generated}/{count})")

                questions_data = self.generator.generate_multiple_questions(
                    topic=session.topic,
                    difficulty=difficulty_text,
                    count=buffer_batch,
                    subtopic=session.subtopic,
                    knowledge_level=session.knowledge_level,
                    existing_questions=existing_questions_list
                )

                # Zapisz pytania do bazy (tylko do osiągnięcia celu)
                batch_added = 0
                for q_data in questions_data:
                    # SPRAWDZENIE: Czy osiągnęliśmy cel dla tego batcha?
                    if batch_added >= current_batch:
                        logger.debug(f"Background: Reached batch target ({batch_added}/{current_batch}), moving to next batch")
                        break

                    # SPRAWDZENIE: Czy nie przekroczyliśmy już limitu total?
                    if total_generated >= count:
                        logger.warning(f"Background: Reached total target count ({total_generated}/{count}), stopping")
                        break

                    # SPRAWDZENIE: Czy sesja nie ma już za dużo pytań?
                    current_total = QuizSessionQuestion.objects.filter(session=session).count()
                    if current_total >= max_questions_allowed:
                        logger.warning(f"Background: Session limit reached ({current_total}/{max_questions_allowed}), stopping")
                        break

                    try:
                        with transaction.atomic():
                            question, is_new = self.question_service.find_or_create_global_question(
                                topic=session.topic,
                                question_data=q_data,
                                difficulty_text=difficulty_text,
                                user=session.user,
                                subtopic=session.subtopic,
                                knowledge_level=session.knowledge_level
                            )

                            session_question = self.question_service.add_question_to_session(
                                session=session,
                                question=question,
                                order=order
                            )

                            if session_question:
                                order += 1
                                total_generated += 1
                                batch_added += 1

                                # Dodaj do kontekstu
                                if existing_questions_list is None:
                                    existing_questions_list = []
                                existing_questions_list.append(q_data['question'])

                                logger.debug(f"Background: Added question {question.id} (batch: {batch_added}/{current_batch}, total: {total_generated}/{count})")
                            else:
                                logger.warning(f"Background: Question {question.id} rejected (duplicate or similar)")
                    except Exception as e:
                        logger.error(f"Background: Error creating question: {e}")
                        continue

            # Aktualizuj licznik
            session.questions_generated_count = start_order + total_generated
            session.save(update_fields=['questions_generated_count'])

            logger.info(f"Background: Completed! Generated {total_generated} questions for session {session_id}")

        except Exception as e:
            logger.error(f"Background generation failed for session {session_id}: {e}")
            import traceback
            traceback.print_exc()

    def generate_adaptive_questions_sync(self, session, new_difficulty_level, count=5):
        """
        Generuje pytania dla nowego poziomu trudności (przy adaptacji).
        Używane gdy gracz zmienia poziom trudności.

        Args:
            session: QuizSession object
            new_difficulty_level: Nowy poziom trudności ('łatwy', 'średni', 'trudny')
            count: Ile pytań wygenerować

        Returns:
            int: Liczba wygenerowanych pytań
        """
        logger.info(f"Generating {count} adaptive questions for level: {new_difficulty_level}")

        # Pobierz już zadane pytania (dla kontekstu)
        existing_session_questions = QuizSessionQuestion.objects.filter(
            session=session
        ).select_related('question').values_list('question__question_text', flat=True)

        existing_questions_list = list(existing_session_questions) if existing_session_questions else None

        # Generuj NIEWIELE więcej niż potrzeba (+10% lub +1) jako bufor na odrzucone
        # UWAGA: Zmniejszono z +30% na +10% aby zmniejszyć orphaned questions
        buffer_count = max(count + 1, int(count * 1.1))
        logger.debug(f"Generating {buffer_count} adaptive questions (target: {count}, buffer: +{buffer_count - count} for rejections)")

        # Generuj pytania
        questions_data = self.generator.generate_multiple_questions(
            topic=session.topic,
            difficulty=new_difficulty_level,
            count=buffer_count,
            subtopic=session.subtopic,
            knowledge_level=session.knowledge_level,
            existing_questions=existing_questions_list
        )

        # Oblicz następny order
        max_order = QuizSessionQuestion.objects.filter(session=session).count()
        order = max_order

        generated_count = 0

        for q_data in questions_data:
            # KRYTYCZNE: Sprawdź limit PRZED przetwarzaniem
            current_total_in_session = QuizSessionQuestion.objects.filter(session=session).count()
            if current_total_in_session >= session.questions_count:
                logger.warning(f"Session already has {current_total_in_session} questions (limit: {session.questions_count}), stopping adaptive generation")
                break

            # ZATRZYMAJ SIĘ gdy osiągniesz cel lokalny
            if generated_count >= count:
                logger.debug(f"Reached target adaptive count ({count}), stopping")
                break

            try:
                question, is_new = self.question_service.find_or_create_global_question(
                    topic=session.topic,
                    question_data=q_data,
                    difficulty_text=new_difficulty_level,
                    user=session.user,
                    subtopic=session.subtopic,
                    knowledge_level=session.knowledge_level
                )

                session_question = self.question_service.add_question_to_session(
                    session=session,
                    question=question,
                    order=order
                )

                if session_question:
                    order += 1
                    generated_count += 1
                    logger.debug(f"Added adaptive question {question.id} (level={new_difficulty_level}, progress={generated_count}/{count})")
                else:
                    logger.warning(f"Adaptive question {question.id} rejected (duplicate or too similar)")

            except Exception as e:
                logger.error(f"Error creating adaptive question: {e}")
                continue

        logger.info(f"Generated {generated_count} adaptive questions")
        return generated_count
