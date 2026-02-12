from pathlib import Path

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase


class QuizAppMigrationRegressionTests(TestCase):
    def test_quiz_app_has_only_initial_migration_file(self):
        migrations_dir = Path(__file__).resolve().parents[1] / 'migrations'
        files = {p.name for p in migrations_dir.glob('*.py')}
        self.assertEqual(files, {'0001_initial.py', '__init__.py'})

    def test_no_pending_migrations_for_quiz_app(self):
        call_command('makemigrations', 'quiz_app', '--check', '--dry-run', verbosity=0)


class QuizAppMigrationExecutorSmokeTests(TransactionTestCase):
    reset_sequences = True

    def test_quiz_app_can_migrate_down_and_up(self):
        executor = MigrationExecutor(connection)
        executor.migrate([('quiz_app', None)])
        executor.loader.build_graph()
        executor.migrate([('quiz_app', '0001_initial')])

        tables = connection.introspection.table_names()
        self.assertIn('quiz_app_quizsession', tables)
        self.assertIn('quiz_app_question', tables)
        self.assertIn('quiz_app_answer', tables)
