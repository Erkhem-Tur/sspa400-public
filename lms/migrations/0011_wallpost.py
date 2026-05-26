from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0010_default_videos'),
    ]

    operations = [
        migrations.CreateModel(
            name='WallPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_name', models.CharField(max_length=100, verbose_name='Нэр')),
                ('prompt', models.CharField(
                    max_length=20,
                    choices=[
                        ('learned',   'Өнөөдөр би сурсан зүйл...'),
                        ('difficult', 'Надад хэцүү байсан...'),
                        ('question',  'Би асуухыг хүссэн...'),
                        ('next',      'Дараагийн удаа би...'),
                    ],
                    verbose_name='Асуулт',
                )),
                ('content', models.TextField(max_length=300, verbose_name='Хариулт')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Хана нийтлэл',
                'verbose_name_plural': 'Хана нийтлэлүүд',
                'ordering': ['-created_at'],
            },
        ),
    ]
