import logging

from ..models import Answer, Question, QuizSessionQuestion

logger = logging.getLogger(__name__)


def cleanup_orphaned_questions(question_ids, reason="cleanup"):
    if not question_ids:
        return 0

    orphaned_questions = Question.objects.filter(
        id__in=question_ids,
        total_answers=0,
    )

    deleted_count = 0
    for orphan_q in orphaned_questions:
        used_in_active = QuizSessionQuestion.objects.filter(
            question=orphan_q,
            session__is_completed=False,
        ).exists()

        if not used_in_active:
            logger.info(
                "Deleting orphaned Question ID=%s (reason=%s)",
                orphan_q.id,
                reason,
            )
            orphan_q.delete()
            deleted_count += 1
        else:
            logger.debug(
                "Keeping Question ID=%s (used in active session)",
                orphan_q.id,
            )

    return deleted_count


def cleanup_rejected_question(question, reason="duplicate"):
    if question.total_answers != 0:
        return False

    used_in_active = QuizSessionQuestion.objects.filter(
        question=question,
        session__is_completed=False,
    ).exists()

    if not used_in_active:
        logger.debug(
            "Deleting orphaned question %s (reason=%s)",
            question.id,
            reason,
        )
        question.delete()
        return True

    logger.debug(
        "Keeping question %s (used in active session)",
        question.id,
    )
    return False


def cleanup_unused_session_questions(session):
    answered_ids = Answer.objects.filter(session=session).values_list(
        "question_id", flat=True
    )
    unused_session_questions = QuizSessionQuestion.objects.filter(
        session=session
    ).exclude(
        question_id__in=answered_ids
    )

    unused_question_ids = list(
        unused_session_questions.values_list("question_id", flat=True)
    )

    unused_count = unused_session_questions.count()
    if unused_count > 0:
        unused_session_questions.delete()
        logger.info("Cleaned up %s QuizSessionQuestion entries", unused_count)

    deleted_orphans = cleanup_orphaned_questions(
        unused_question_ids,
        reason="session_complete",
    )
    return unused_count, deleted_orphans


def rollback_session(session):
    answers = list(
        Answer.objects.filter(session=session).select_related('question')
    )

    total_answers_delta = len(answers)
    total_correct_delta = sum(1 for ans in answers if ans.is_correct)

    for ans in answers:
        question = ans.question
        if question.total_answers > 0:
            question.total_answers = max(0, question.total_answers - 1)
        if ans.is_correct and question.correct_answers_count > 0:
            question.correct_answers_count = max(
                0, question.correct_answers_count - 1
            )
        question.save(update_fields=['total_answers', 'correct_answers_count'])

    Answer.objects.filter(session=session).delete()

    session_question_ids = list(
        QuizSessionQuestion.objects.filter(session=session)
        .values_list('question_id', flat=True)
    )
    QuizSessionQuestion.objects.filter(session=session).delete()

    if session_question_ids:
        orphaned_questions = Question.objects.filter(
            id__in=session_question_ids,
            total_answers=0,
        )

        for orphan_q in orphaned_questions:
            used_in_active = QuizSessionQuestion.objects.filter(
                question=orphan_q,
                session__is_completed=False,
            ).exists()

            if not used_in_active:
                logger.info(
                    "Deleting orphaned Question ID=%s (session rollback)",
                    orphan_q.id,
                )
                orphan_q.delete()

    profile = session.user.profile
    profile.total_questions_answered = max(
        0, profile.total_questions_answered - total_answers_delta
    )
    profile.total_correct_answers = max(
        0, profile.total_correct_answers - total_correct_delta
    )
    profile.save(update_fields=['total_questions_answered', 'total_correct_answers'])

    session.delete()


