from django.db import migrations


# Default ТТХГ department names — seeded on every fresh deploy so the
# logbook dropdown is never empty even on Render's ephemeral SQLite.
DEFAULT_DEPARTMENTS = [
    "Хамгаалалтын хэлтэс",
    "Тагнуулын хэлтэс",
    "Тусгай даалгаврын хэлтэс",
    "Техникийн хамгаалалтын хэлтэс",
    "Мэдээлэл, шинжилгээний хэлтэс",
    "Захиргаа, удирдлагын хэлтэс",
    "Сургалт, бэлтгэлийн хэлтэс",
    "Авто тээврийн хэлтэс",
    "Харилцаа холбооны хэлтэс",
    "Эмнэлгийн хэлтэс",
]


def seed_departments(apps, schema_editor):
    Department = apps.get_model('lms', 'Department')
    for i, name in enumerate(DEFAULT_DEPARTMENTS):
        Department.objects.get_or_create(name=name, defaults={'order': i})


def unseed_departments(apps, schema_editor):
    # Reverse: remove only the seeded defaults (don't touch user-created ones)
    Department = apps.get_model('lms', 'Department')
    Department.objects.filter(name__in=DEFAULT_DEPARTMENTS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0008_tloverride'),
    ]

    operations = [
        migrations.RunPython(seed_departments, reverse_code=unseed_departments),
    ]
