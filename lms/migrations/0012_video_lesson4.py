from django.db import migrations


def add_video(apps, schema_editor):
    Video = apps.get_model('lms', 'Video')
    Video.objects.get_or_create(
        youtube_id='K-WX_KW9ANE',
        defaults={
            'title': 'ALC Book 1 Lesson 4 Монгол тайлбартай',
            'description': '',
            'order': 4,
            'is_published': True,
        }
    )


def remove_video(apps, schema_editor):
    Video = apps.get_model('lms', 'Video')
    Video.objects.filter(youtube_id='K-WX_KW9ANE').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0011_wallpost'),
    ]

    operations = [
        migrations.RunPython(add_video, reverse_code=remove_video),
    ]
