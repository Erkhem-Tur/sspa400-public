from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0007_logentry_tasag'),
    ]

    operations = [
        migrations.CreateModel(
            name='TlOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=200, verbose_name='Хуудасны зам')),
                ('key', models.CharField(max_length=100, verbose_name='Түлхүүр')),
                ('text', models.TextField(verbose_name='Монгол орчуулга')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Орчуулгын засвар',
                'verbose_name_plural': 'Орчуулгын засварууд',
                'ordering': ['path', 'key'],
                'unique_together': {('path', 'key')},
            },
        ),
    ]
