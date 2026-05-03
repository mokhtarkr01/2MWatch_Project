from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0007_match_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(max_length=20, choices=[
                    ('rating', '⭐ New Rating'),
                    ('comment', '💬 New Comment'),
                    ('register', '👤 New Registration'),
                ])),
                ('message', models.CharField(max_length=300)),
                ('read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
