# Generated manually for advanced quiz settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz_app', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizsession',
            name='questions_count',
            field=models.IntegerField(default=10),
        ),
        migrations.AddField(
            model_name='quizsession',
            name='time_per_question',
            field=models.IntegerField(default=30),
        ),
        migrations.AddField(
            model_name='quizsession',
            name='use_adaptive_difficulty',
            field=models.BooleanField(default=True),
        ),
    ]
