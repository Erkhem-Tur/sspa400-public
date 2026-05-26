from django.db import migrations


DEFAULT_VIDEOS = [
    {
        'title': 'ALC Book 1 Lesson 1 Монгол тайлбартай',
        'youtube_id': 'Tev9SFEPF58',
        'description': '',
        'order': 1,
    },
    {
        'title': 'ALC Book 1 Lesson 1.2 Монгол тайлбартай',
        'youtube_id': 'qRiL9lnpAO8',
        'description': '',
        'order': 2,
    },
    {
        'title': 'ALC Book 1 Lesson 3 Монгол тайлбартай',
        'youtube_id': 'TAGhfG_15do',
        'description': '',
        'order': 3,
    },
]


def seed_videos(apps, schema_editor):
    Video = apps.get_model('lms', 'Video')
    for v in DEFAULT_VIDEOS:
        Video.objects.get_or_create(
            youtube_id=v['youtube_id'],
            defaults={
                'title': v['title'],
                'description': v['description'],
                'order': v['order'],
                'is_published': True,
            }
        )


def unseed_videos(apps, schema_editor):
    Video = apps.get_model('lms', 'Video')
    ids = [v['youtube_id'] for v in DEFAULT_VIDEOS]
    Video.objects.filter(youtube_id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0009_default_departments'),
    ]

    operations = [
        migrations.RunPython(seed_videos, reverse_code=unseed_videos),
    ]
