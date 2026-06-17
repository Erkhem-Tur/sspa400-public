from django.db import migrations


COP17_DESCRIPTION = """90-minute CEFR A1 lesson resource pack for SSPA Mongolia protection officers.

Topic: COP17 Registration & Access Control English

Includes:
- Teacher guide and minute-by-minute 90-minute lesson plan
- Vocabulary bank with Mongolian support
- Officer phrase bank and pronunciation practice
- Listening scripts and teacher prompts
- Learner worksheets and controlled practice
- Badge color cards, role cards, and checkpoint scenarios
- Speaking assessment checklist
- Homework sheet and answer key

Main task:
Officers practise how to check a badge and ID, scan a badge, give simple directions, stop entry politely, and call a supervisor when needed.

Download the editable DOCX classroom pack from the button on this lesson page."""


def add_cop17_lesson(apps, schema_editor):
    Lesson = apps.get_model("lms", "Lesson")
    Lesson.objects.update_or_create(
        id=2,
        defaults={
            "title": "COP17 Registration & Access Control English - A1 Resource Pack",
            "description": COP17_DESCRIPTION,
            "order": 2,
        },
    )


def remove_cop17_lesson(apps, schema_editor):
    Lesson = apps.get_model("lms", "Lesson")
    Lesson.objects.filter(
        id=2,
        title__icontains="COP17 Registration",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("lms", "0012_video_lesson4"),
    ]

    operations = [
        migrations.RunPython(add_cop17_lesson, reverse_code=remove_cop17_lesson),
    ]
