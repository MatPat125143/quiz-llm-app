"""
Management command do czyszczenia pytań bez odpowiedzi (orphaned questions).

Uruchomienie:
    python manage.py cleanup_orphaned_questions

Opcje:
    --dry-run : Tylko pokaż co zostanie usunięte, nie usuwaj
    --age-hours : Usuń tylko pytania starsze niż X godzin (domyślnie 24)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from quiz_app.models import Question, QuizSessionQuestion


class Command(BaseCommand):
    help = 'Czyści pytania bez odpowiedzi (orphaned questions) z bazy danych'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Tylko pokaż co zostanie usunięte, nie usuwaj',
        )
        parser.add_argument(
            '--age-hours',
            type=int,
            default=24,
            help='Usuń tylko pytania starsze niż X godzin (domyślnie 24)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        age_hours = options['age_hours']

        self.stdout.write(self.style.SUCCESS(f'\n🔍 Szukam orphaned questions (starszych niż {age_hours}h)...\n'))

        # Oblicz cutoff time
        cutoff_time = timezone.now() - timedelta(hours=age_hours)

        # Znajdź pytania które:
        # 1. total_answers = 0 (NIKT nie odpowiedział)
        # 2. created_at < cutoff_time (są wystarczająco stare)
        orphaned_candidates = Question.objects.filter(
            total_answers=0,
            created_at__lt=cutoff_time
        )

        total_candidates = orphaned_candidates.count()
        self.stdout.write(f'📊 Znaleziono {total_candidates} kandydatów do usunięcia\n')

        if total_candidates == 0:
            self.stdout.write(self.style.SUCCESS('✅ Baza jest czysta! Brak orphaned questions.\n'))
            return

        # Sprawdź każde pytanie czy nie jest używane w aktywnych sesjach
        to_delete = []
        to_keep = []

        for question in orphaned_candidates:
            # Sprawdź czy pytanie jest w jakiejś AKTYWNEJ sesji
            used_in_active = QuizSessionQuestion.objects.filter(
                question=question,
                session__is_completed=False
            ).exists()

            if used_in_active:
                to_keep.append(question)
            else:
                to_delete.append(question)

        # Podsumowanie
        self.stdout.write(f'\n📈 PODSUMOWANIE:')
        self.stdout.write(f'  • Do usunięcia: {len(to_delete)} pytań')
        self.stdout.write(f'  • Do zachowania (aktywne sesje): {len(to_keep)} pytań\n')

        if len(to_delete) == 0:
            self.stdout.write(self.style.SUCCESS('✅ Brak pytań do usunięcia.\n'))
            return

        # Pokaż szczegóły
        if to_delete:
            self.stdout.write('\n🗑️ PYTANIA DO USUNIĘCIA:')
            for i, q in enumerate(to_delete[:10], 1):  # Pokaż max 10
                age_days = (timezone.now() - q.created_at).days
                self.stdout.write(
                    f'  {i}. ID={q.id} | {q.topic} | {q.difficulty_level} | '
                    f'Wiek: {age_days}d | "{q.question_text[:50]}..."'
                )
            if len(to_delete) > 10:
                self.stdout.write(f'  ... i {len(to_delete) - 10} więcej')

        # Wykonaj usuwanie
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n⚠️ DRY RUN - nic nie zostało usunięte'))
            self.stdout.write(f'Uruchom bez --dry-run aby faktycznie usunąć {len(to_delete)} pytań\n')
        else:
            self.stdout.write(self.style.WARNING(f'\n🚀 Usuwam {len(to_delete)} pytań...'))

            deleted_count = 0
            for question in to_delete:
                try:
                    question.delete()
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Błąd usuwania ID={question.id}: {e}'))

            self.stdout.write(self.style.SUCCESS(f'\n✅ Usunięto {deleted_count} orphaned questions!\n'))

        # Statystyki końcowe
        remaining_orphaned = Question.objects.filter(total_answers=0).count()
        total_questions = Question.objects.count()
        self.stdout.write(f'\n📊 STATYSTYKI BAZY:')
        self.stdout.write(f'  • Wszystkich pytań: {total_questions}')
        self.stdout.write(f'  • Orphaned (total_answers=0): {remaining_orphaned}')
        self.stdout.write(f'  • Z odpowiedziami: {total_questions - remaining_orphaned}\n')
