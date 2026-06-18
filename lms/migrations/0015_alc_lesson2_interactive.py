from django.db import migrations


ALC_TITLE = "ALC Book 4 Lesson 2 Support English - SSPA Protection Officers"

INTERACTIVE_DESCRIPTION = """Interactive CEFR A1 lesson for SSPA Mongolia protection officers.

ALC Book 4 Lesson 2: He's in the Army now

Interactive lesson sections:
- military personnel, bases, uniform, duty, ranks, and insignia vocabulary
- regular past tense pronunciation: /t/, /d/, and /id/
- irregular past tense verb practice
- past tense questions with did + base verb
- military time and the 24-hour clock
- original SSPA reading and career timeline task
- 10-question final quiz with instant feedback
- homework timeline saved in the learner's browser

The PDF and editable teacher pack remain available as optional reference materials."""


def update_alc_lesson(apps, schema_editor):
    Lesson = apps.get_model("lms", "Lesson")
    Lesson.objects.filter(title=ALC_TITLE).update(
        description=INTERACTIVE_DESCRIPTION,
        order=3,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("lms", "0014_alc_book4_lesson2_support"),
    ]

    operations = [
        migrations.RunPython(update_alc_lesson, reverse_code=migrations.RunPython.noop),
    ]
