import logging
import threading

from django.db import DatabaseError

from cache_manager import QuizCacheService
from ..models import Answer, Question, QuizSession, QuizSessionQuestion
from ..utils.constants import SYNC_QUESTION_COUNT
from ..utils.helpers import build_question_payload, get_used_question_refs
from .question_delivery_service import select_next_session_question

logger = logging.getLogger(__name__)


def handle_adaptive_difficulty_change(session, difficulty_adapter, bg_generator):
    previous_difficulty_level = None
    new_difficulty_level = None
    level_changed = False

    if not session.use_adaptive_difficulty:
        return level_changed, previous_difficulty_level, new_difficulty_level

    recent_answers_objs = Answer.objects.filter(
        session=session
    ).order_by('-answered_at')[:difficulty_adapter.streak_threshold]
    recent_answers = [ans.is_correct for ans in reversed(list(recent_answers_objs))]

    difficulty_result = difficulty_adapter.adjust_difficulty_with_level_check(
        session.current_difficulty,
        recent_answers
    )

    if not difficulty_result['difficulty_changed']:
        return level_changed, previous_difficulty_level, new_difficulty_level

    session.current_difficulty = difficulty_result['new_difficulty']

    if not difficulty_result['level_changed']:
        return level_changed, previous_difficulty_level, new_difficulty_level

    level_changed = True
    previous_difficulty_level = difficulty_result['previous_level']
    new_difficulty_level = difficulty_result['new_level']
    logger.info(
        "Level change: %s -> %s",
        previous_difficulty_level,
        new_difficulty_level
    )

    answered_question_ids = list(
        Answer.objects.filter(session=session).values_list('question_id', flat=True)
    )

    _cleanup_old_level_questions(
        session=session,
        previous_level=previous_difficulty_level,
        answered_question_ids=answered_question_ids,
    )

    questions_answered = session.total_questions
    questions_remaining = session.questions_count - questions_answered

    if questions_remaining <= 0:
        logger.info(
            "Quiz ending - skipping question generation (remaining=%s)",
            questions_remaining
        )
        return level_changed, previous_difficulty_level, new_difficulty_level

    actually_needed, unused_questions_count = _compute_needed_questions(
        session=session,
        answered_question_ids=answered_question_ids,
        questions_remaining=questions_remaining,
    )

    if actually_needed <= 0:
        logger.info(
            "No need to generate questions - enough in queue (need: %s, have: %s)",
            actually_needed,
            unused_questions_count
        )
        return level_changed, previous_difficulty_level, new_difficulty_level

    _schedule_level_generation(
        session=session,
        new_difficulty_level=new_difficulty_level,
        actually_needed=actually_needed,
        bg_generator=bg_generator,
    )

    return level_changed, previous_difficulty_level, new_difficulty_level


def prefetch_next_question_cache(session):
    cached = QuizCacheService.get_cached_question(session.id)
    if cached:
        return

    answered_question_ids, answered_texts, used_hashes = get_used_question_refs(
        session
    )

    next_session_question = select_next_session_question(
        session,
        answered_question_ids,
        answered_texts,
        used_hashes
    )

    if next_session_question:
        payload = build_question_payload(
            session, next_session_question.question, "cached"
        )
        QuizCacheService.cache_next_payload(session.id, payload)


def update_profile_stats_on_completion(user):
    profile = user.profile
    completed_sessions = QuizSession.objects.filter(
        user=user,
        is_completed=True
    )
    profile.total_quizzes_played = completed_sessions.count()

    completed_answers = Answer.objects.filter(
        user=user,
        session__is_completed=True
    )
    profile.total_questions_answered = completed_answers.count()
    profile.total_correct_answers = completed_answers.filter(is_correct=True).count()

    max_streak = 0
    for session in completed_sessions:
        session_answers = Answer.objects.filter(
            session=session
        ).order_by('answered_at')
        current_streak = 0
        for ans in session_answers:
            if ans.is_correct:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
    profile.highest_streak = max_streak
    profile.save()


def _cleanup_old_level_questions(session, previous_level, answered_question_ids):
    questions_to_delete = QuizSessionQuestion.objects.filter(
        session=session,
        question__difficulty_level=previous_level
    ).exclude(
        question_id__in=answered_question_ids
    )

    deleted_question_ids = list(questions_to_delete.values_list('question_id', flat=True))
    deleted_count = questions_to_delete.delete()[0]

    if deleted_count <= 0 or not deleted_question_ids:
        return

    orphaned_from_difficulty_change = Question.objects.filter(
        id__in=deleted_question_ids,
        total_answers=0
    )

    for orphan_q in orphaned_from_difficulty_change:
        used_in_active = QuizSessionQuestion.objects.filter(
            question=orphan_q,
            session__is_completed=False
        ).exists()

        if not used_in_active:
            logger.info(
                "Deleting orphaned Question ID=%s (difficulty change, total_answers=0)",
                orphan_q.id
            )
            orphan_q.delete()


def _compute_needed_questions(session, answered_question_ids, questions_remaining):
    unused_questions_count = QuizSessionQuestion.objects.filter(
        session=session
    ).exclude(
        question_id__in=answered_question_ids
    ).count()

    actually_needed = max(0, questions_remaining - unused_questions_count)
    return actually_needed, unused_questions_count


def _schedule_level_generation(session, new_difficulty_level, actually_needed, bg_generator):
    sync_count = min(SYNC_QUESTION_COUNT, actually_needed)

    def generate_for_new_level():
        try:
            from django.db import connection
            connection.close()
        except DatabaseError as e:
            logger.debug("Database connection close failed in async thread: %s", e)
        try:
            generated = bg_generator.generate_adaptive_questions_sync(
                session=session,
                new_difficulty_level=new_difficulty_level,
                count=sync_count
            )
            logger.info(
                "Generated %s questions sync for level '%s' (async thread)",
                generated,
                new_difficulty_level
            )

            if actually_needed > sync_count:
                async_count = actually_needed - sync_count
                logger.info(
                    "Starting async generation of %s more questions for level '%s' (async thread)",
                    async_count,
                    new_difficulty_level
                )

                current_total = QuizSessionQuestion.objects.filter(
                    session=session
                ).count()
                bg_generator.generate_remaining_questions_async(
                    session_id=session.id,
                    total_needed=session.questions_count,
                    already_generated=current_total
                )
        except (DatabaseError, RuntimeError, TypeError, ValueError) as e:
            logger.error("Error generating adaptive questions (async): %s", e)

    threading.Thread(target=generate_for_new_level, daemon=True).start()


