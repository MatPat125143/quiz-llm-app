from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from quiz_app.models import Question, QuizSessionQuestion
from quiz_app.services.cleanup_service import cleanup_orphaned_questions


class Command(BaseCommand):
    help = 'Cleans orphaned questions (no answers) from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show what would be deleted, do not delete',
        )
        parser.add_argument(
            '--age-hours',
            type=int,
            default=24,
            help='Delete only questions older than X hours (default: 24)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        age_hours = options['age_hours']

        self.stdout.write(
            self.style.SUCCESS(f'\nSearching for orphaned questions (older than {age_hours}h)...\n')
        )

        cutoff_time = timezone.now() - timedelta(hours=age_hours)

        orphaned_candidates = Question.objects.filter(
            total_answers=0,
            created_at__lt=cutoff_time
        )

        total_candidates = orphaned_candidates.count()
        self.stdout.write(f'Found {total_candidates} deletion candidates\n')

        if total_candidates == 0:
            self.stdout.write(self.style.SUCCESS('Database is clean. No orphaned questions.\n'))
            return

        to_delete = []
        to_keep = []

        for question in orphaned_candidates:
            used_in_active = QuizSessionQuestion.objects.filter(
                question=question,
                session__is_completed=False
            ).exists()
            if used_in_active:
                to_keep.append(question)
            else:
                to_delete.append(question)

        self.stdout.write('\nSUMMARY:')
        self.stdout.write(f'  - To delete: {len(to_delete)} questions')
        self.stdout.write(f'  - To keep (active sessions): {len(to_keep)} questions\n')

        if len(to_delete) == 0:
            self.stdout.write(self.style.SUCCESS('No questions to delete.\n'))
            return

        if to_delete:
            self.stdout.write('\nQUESTIONS TO DELETE:')
            for i, q in enumerate(to_delete[:10], 1):
                age_days = (timezone.now() - q.created_at).days
                self.stdout.write(
                    f'  {i}. ID={q.id} | {q.topic} | {q.difficulty_level} | '
                    f'Age: {age_days}d | "{q.question_text[:50]}..."'
                )
            if len(to_delete) > 10:
                self.stdout.write(f'  ... and {len(to_delete) - 10} more')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - nothing was deleted'))
            self.stdout.write(f'Run without --dry-run to delete {len(to_delete)} questions\n')
        else:
            self.stdout.write(self.style.WARNING(f'\nDeleting {len(to_delete)} questions...'))

            deleted_count = cleanup_orphaned_questions(
                [q.id for q in to_delete],
                reason="manual_cleanup",
            )

            self.stdout.write(self.style.SUCCESS(f'\nDeleted {deleted_count} orphaned questions.\n'))

        remaining_orphaned = Question.objects.filter(total_answers=0).count()
        total_questions = Question.objects.count()
        self.stdout.write('\nDATABASE STATS:')
        self.stdout.write(f'  - Total questions: {total_questions}')
        self.stdout.write(f'  - Orphaned (total_answers=0): {remaining_orphaned}')
        self.stdout.write(f'  - With answers: {total_questions - remaining_orphaned}\n')
