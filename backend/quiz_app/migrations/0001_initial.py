from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QuizSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=200)),
                ('subtopic', models.CharField(blank=True, max_length=200, null=True)),
                ('knowledge_level', models.CharField(
                    choices=[('elementary', 'Szkoła podstawowa'), ('high_school', 'Liceum'), ('university', 'Studia'),
                             ('expert', 'Ekspert')], default='high_school', max_length=20)),
                ('initial_difficulty', models.CharField(max_length=20)),
                ('current_difficulty', models.FloatField(default=1.0)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('total_questions', models.IntegerField(default=0)),
                ('correct_answers', models.IntegerField(default=0)),
                ('current_streak', models.IntegerField(default=0)),
                ('questions_count', models.IntegerField(default=10)),
                ('time_per_question', models.IntegerField(default=30)),
                ('use_adaptive_difficulty', models.BooleanField(default=True)),
                ('questions_generated_count', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_sessions',
                                           to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Quiz Session',
                'verbose_name_plural': 'Quiz Sessions',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(db_index=True, max_length=200)),
                ('subtopic', models.CharField(blank=True, db_index=True, max_length=200, null=True)),
                ('knowledge_level', models.CharField(blank=True, choices=[('elementary', 'Szkoła podstawowa'),
                                                                          ('high_school', 'Liceum'),
                                                                          ('university', 'Studia'),
                                                                          ('expert', 'Ekspert')], max_length=20,
                                                     null=True)),
                ('question_text', models.TextField()),
                ('correct_answer', models.CharField(max_length=500)),
                ('wrong_answer_1', models.CharField(max_length=500)),
                ('wrong_answer_2', models.CharField(max_length=500)),
                ('wrong_answer_3', models.CharField(max_length=500)),
                ('explanation', models.TextField()),
                ('difficulty_level',
                 models.CharField(choices=[('łatwy', 'Łatwy'), ('średni', 'Średni'), ('trudny', 'Trudny')],
                                  default='średni', max_length=20)),
                ('embedding_vector', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('edited_at', models.DateTimeField(blank=True, null=True)),
                ('total_answers', models.IntegerField(default=0)),
                ('correct_answers_count', models.IntegerField(default=0)),
                ('times_used', models.IntegerField(default=0)),
                ('content_hash', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                 related_name='created_questions', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                              related_name='questions', to='quiz_app.quizsession')),
            ],
            options={
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_answer', models.CharField(max_length=500)),
                ('is_correct', models.BooleanField()),
                ('response_time', models.FloatField()),
                ('answered_at', models.DateTimeField(auto_now_add=True)),
                ('difficulty_at_answer', models.FloatField(default=5.0)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers',
                                               to='quiz_app.question')),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                              related_name='answers', to='quiz_app.quizsession')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Answer',
                'verbose_name_plural': 'Answers',
                'ordering': ['-answered_at'],
            },
        ),
        migrations.CreateModel(
            name='QuizSessionQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0)),
                ('shown_at', models.DateTimeField(auto_now_add=True)),
                ('question',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_sessions',
                                   to='quiz_app.question')),
                ('session',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_questions',
                                   to='quiz_app.quizsession')),
            ],
            options={
                'verbose_name': 'Quiz Session Question',
                'verbose_name_plural': 'Quiz Session Questions',
                'ordering': ['order'],
                'indexes': [models.Index(fields=['session', 'order'], name='quiz_app_qu_session_11e1b5_idx')],
                'unique_together': {('session', 'question')},
            },
        ),
        migrations.AddIndex(
            model_name='quizsession',
            index=models.Index(fields=['-started_at'], name='quiz_app_qu_started_2be838_idx'),
        ),
        migrations.AddIndex(
            model_name='quizsession',
            index=models.Index(fields=['user', 'is_completed'], name='quiz_app_qu_user_id_67c182_idx'),
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['topic', 'difficulty_level'], name='quiz_app_qu_topic_b5f1a8_idx'),
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['content_hash'], name='quiz_app_qu_content_ae2e16_idx'),
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['-times_used'], name='quiz_app_qu_times_u_6ec7bc_idx'),
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['session', 'created_at'], name='quiz_app_qu_session_45d5ed_idx'),
        ),
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['question', 'user'], name='quiz_app_an_questio_99a372_idx'),
        ),
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['session', '-answered_at'], name='quiz_app_an_session_8e0008_idx'),
        ),
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['-answered_at'], name='quiz_app_an_answere_1b0db3_idx'),
        ),
        migrations.AddConstraint(
            model_name='answer',
            constraint=models.UniqueConstraint(fields=('question', 'user', 'session'),
                                               name='unique_answer_per_question_session'),
        ),
    ]
