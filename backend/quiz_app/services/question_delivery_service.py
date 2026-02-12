import logging
import time
import threading

from django.db import DatabaseError

from cache_manager import QuizCacheService
from llm_integration.difficulty_adapter import DifficultyAdapter

from ..models import Answer, QuizSessionQuestion
from ..utils.constants import QUESTION_WAIT_MAX_SECONDS, QUESTION_WAIT_POLL_SECONDS
from ..utils.helpers import build_question_payload, get_used_question_refs
from .background_generation_service import BackgroundGenerationService

logger = logging.getLogger(__name__)

difficulty_adapter = DifficultyAdapter()
bg_generator = BackgroundGenerationService()


def select_next_session_question(session, answered_question_ids, answered_texts, used_hashes):
    return (
        QuizSessionQuestion.objects.filter(session=session)
        .exclude(question_id__in=answered_question_ids)
        .exclude(question__question_text__in=answered_texts)
        .exclude(question__content_hash__in=used_hashes)
        .select_related('question')
        .order_by('order')
        .first()
    )


def _maybe_pregenerate_next_level(session):
    if not session.use_adaptive_difficulty or session.total_questions >= session.questions_count:
        return

    recent_answers_objs = Answer.objects.filter(
        session=session
    ).order_by('-answered_at')[:difficulty_adapter.streak_threshold]
    recent_answers = [ans.is_correct for ans in reversed(list(recent_answers_objs))]

    pregenerate_check = difficulty_adapter.should_pregenerate_next_level(
        session.current_difficulty,
        recent_answers,
        session.total_questions,
        session.questions_count
    )

    if not pregenerate_check['should_pregenerate']:
        return

    target_level = pregenerate_check['target_level']
    current_level = difficulty_adapter.get_difficulty_level(session.current_difficulty)
    logger.info(
        "Pre-generating questions for level change: %s -> %s",
        current_level,
        target_level
    )

    answered_ids = Answer.objects.filter(
        session=session
    ).values_list('question_id', flat=True)

    existing_target_questions = QuizSessionQuestion.objects.filter(
        session=session,
        question__difficulty_level=target_level
    ).exclude(question_id__in=answered_ids).count()

    if existing_target_questions != 0:
        logger.debug(
            "Pre-gen skipped: %s questions already exist",
            existing_target_questions
        )
        return

    questions_remaining = session.questions_count - (session.total_questions + 1)
    current_questions_in_session = QuizSessionQuestion.objects.filter(
        session=session
    ).count()
    actual_space_left = session.questions_count - current_questions_in_session
    questions_to_generate = min(3, questions_remaining, max(0, actual_space_left))

    if questions_to_generate <= 0:
        logger.debug("Pre-gen skipped: %s questions remaining", questions_remaining)
        return

    logger.info(
        "Pre-generating %s questions at level '%s'",
        questions_to_generate,
        target_level
    )

    def async_pregenerate():
        try:
            bg_generator.generate_adaptive_questions_sync(
                session=session,
                new_difficulty_level=target_level,
                count=questions_to_generate
            )
        except (DatabaseError, RuntimeError, TypeError, ValueError) as e:
            logger.error("Async pre-generation failed: %s", e)

    thread = threading.Thread(target=async_pregenerate, daemon=True)
    thread.start()


def _maybe_generate_initial_questions(session):
    try:
        current_in_session = QuizSessionQuestion.objects.filter(
            session=session
        ).count()
        remaining_slots = max(0, session.questions_count - current_in_session)
        if remaining_slots > 0:
            to_generate = min(2, remaining_slots)
            bg_generator.generate_initial_questions_sync(session, count=to_generate)
    except (DatabaseError, RuntimeError, TypeError, ValueError) as e:
        logger.error(
            "Immediate fallback generation failed for session %s: %s",
            session.id,
            e
        )


def _wait_for_question(session, answered_question_ids, answered_texts, used_hashes):
    waited = 0
    while waited < QUESTION_WAIT_MAX_SECONDS:
        time.sleep(QUESTION_WAIT_POLL_SECONDS)
        waited += QUESTION_WAIT_POLL_SECONDS
        session_question = select_next_session_question(
            session,
            answered_question_ids,
            answered_texts,
            used_hashes
        )
        if session_question:
            logger.debug("Question generated after %ss", waited)
            return session_question
    return None


def get_next_question_payload(session):
    cached = QuizCacheService.get_cached_question(session.id)
    if cached:
        QuizCacheService.delete_cached_question(session.id)
        logger.info("Served cached question for session %s", session.id)
        return cached, None

    answered_question_ids, answered_texts, used_hashes = get_used_question_refs(
        session
    )

    session_question = select_next_session_question(
        session,
        answered_question_ids,
        answered_texts,
        used_hashes
    )

    if not session_question:
        _maybe_generate_initial_questions(session)
        session_question = _wait_for_question(
            session,
            answered_question_ids,
            answered_texts,
            used_hashes
        )

    if not session_question:
        logger.warning(
            "No question available after %ss wait for session %s",
            QUESTION_WAIT_MAX_SECONDS,
            session.id
        )
        return None, "No more questions available"

    question = session_question.question
    _maybe_pregenerate_next_level(session)

    payload = build_question_payload(session, question, "pre_generated")
    return payload, None


