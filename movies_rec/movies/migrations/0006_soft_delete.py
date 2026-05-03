from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0005_movie_trailer_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='genre',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
