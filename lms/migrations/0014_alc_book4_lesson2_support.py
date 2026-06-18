from django.db import migrations


ALC_TITLE = "ALC Book 4 Lesson 2 Support English - SSPA Protection Officers"

ALC_DESCRIPTION = """Original CEFR A1 support lesson for SSPA Mongolia protection officers.

This lesson is designed to connect with ALC Book 4 Lesson 2 classroom study without reproducing copyrighted ALC textbook text.

Topic: Checkpoint English - badge, ID, access permission, and simple officer instructions.

Includes:
- 90-minute teacher lesson plan
- 24-word checkpoint vocabulary bank with Mongolian support
- can / cannot for access permission
- must / must not for rules
- polite imperatives with please
- pronunciation practice
- listening scripts
- learner worksheets
- role-play cards
- homework and answer key

Main task:
The officer checks a person at a gate and gives a clear decision: enter, wait, stop, or call a supervisor.

Download the editable DOCX classroom pack from the button on this lesson page:
SSPA_ALC_Book4_Lesson2_A1_Support_Pack.docx

Open the supplied 27-page ALC lesson PDF from the second resource button:
ALC_Book4_Lesson2.pdf"""


def add_alc_lesson(apps, schema_editor):
    Lesson = apps.get_model("lms", "Lesson")
    existing = Lesson.objects.filter(title=ALC_TITLE).first()
    defaults = {
        "title": ALC_TITLE,
        "description": ALC_DESCRIPTION,
        "order": 3,
    }
    if existing:
        for field, value in defaults.items():
            setattr(existing, field, value)
        existing.save(update_fields=list(defaults))
        return

    if Lesson.objects.filter(id=3).exists():
        Lesson.objects.create(**defaults)
        return

    Lesson.objects.create(id=3, **defaults)


def remove_alc_lesson(apps, schema_editor):
    Lesson = apps.get_model("lms", "Lesson")
    Lesson.objects.filter(title=ALC_TITLE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("lms", "0013_cop17_resource_lesson"),
    ]

    operations = [
        migrations.RunPython(add_alc_lesson, reverse_code=remove_alc_lesson),
    ]
