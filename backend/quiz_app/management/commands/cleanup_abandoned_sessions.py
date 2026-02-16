import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction
from django.utils import timezone

from quiz_app.models import Answer, QuizSession, QuizSessionQuestion
from quiz_app.services.cleanup_service import cleanup_orphaned_questions

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Cleans abandoned quiz sessions (unfinished, old) with related data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--age-minutes",
            type=int,
            default=60,
            help="Minimum age (minutes) of an unfinished session to delete",
        )

    def handle(self, *args, **options):
        age_minutes = options.get("age_minutes", 60)
        cutoff = timezone.now() - timedelta(minutes=age_minutes)

        stale_sessions = QuizSession.objects.filter(is_completed=False, started_at__lt=cutoff)

        if not stale_sessions.exists():
            self.stdout.write(self.style.SUCCESS("No abandoned sessions to clean."))
            return

        self.stdout.write(
            f"Cleaning {stale_sessions.count()} abandoned sessions (> {age_minutes} min)"
        )

        for session in stale_sessions:
            try:
                with transaction.atomic():
                    self._rollback_session(session)
                self.stdout.write(self.style.SUCCESS(f"Deleted session {session.id}"))
            except DatabaseError as e:
                logger.error(f"Cleanup failed for session {session.id}: {e}")
                self.stderr.write(self.style.ERROR(f"Error for session {session.id}: {e}"))

    def _rollback_session(self, session):
        answers = self._collect_answers(session)
        total_answers_delta, total_correct_delta = self._rollback_answers(answers)
        session_question_ids = self._delete_session_questions(session)
        self._delete_orphaned_questions(session_question_ids)
        self._update_profile(session, total_answers_delta, total_correct_delta)
        session.delete()

    def _collect_answers(self, session):
        return list(Answer.objects.filter(session=session).select_related("question"))

    def _rollback_answers(self, answers):
        total_answers_delta = len(answers)
        total_correct_delta = sum(1 for ans in answers if ans.is_correct)

        for ans in answers:
            q = ans.question
            if q.total_answers > 0:
                q.total_answers = max(0, q.total_answers - 1)
            if ans.is_correct and q.correct_answers_count > 0:
                q.correct_answers_count = max(0, q.correct_answers_count - 1)
            q.times_used = q.total_answers
            q.save(update_fields=["total_answers", "correct_answers_count", "times_used"])

        Answer.objects.filter(id__in=[a.id for a in answers]).delete()
        return total_answers_delta, total_correct_delta

    def _delete_session_questions(self, session):
        session_question_ids = list(
            QuizSessionQuestion.objects.filter(session=session).values_list("question_id", flat=True)
        )
        QuizSessionQuestion.objects.filter(session=session).delete()
        return session_question_ids

    def _delete_orphaned_questions(self, session_question_ids):
        cleanup_orphaned_questions(session_question_ids, reason="cleanup_job")

    def _update_profile(self, session, total_answers_delta, total_correct_delta):
        profile = session.user.profile
        profile.total_questions_answered = max(0, profile.total_questions_answered - total_answers_delta)
        profile.total_correct_answers = max(0, profile.total_correct_answers - total_correct_delta)
        profile.save(update_fields=["total_questions_answered", "total_correct_answers"])
