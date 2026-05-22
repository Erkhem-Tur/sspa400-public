from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from lms.models import Department, Lesson


class Command(BaseCommand):
    help = 'Seed initial data'

    def handle(self, *args, **kwargs):
        depts = [
            (1, 'Хамгаалалтын 6-р хэлтэс'),
            (2, 'Төрийн Ордны хамгаалалтын хэлтэс'),
        ]
        for order, name in depts:
            Department.objects.get_or_create(name=name, defaults={'order': order})

        Lesson.objects.get_or_create(id=1, defaults={
            'title': 'SSPA Operation English — 400 questions',
            'description': 'Vocabulary, Grammar, Flashcards, Listening',
            'order': 1,
        })

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', '2b32oh@gmail.com', 'admin1234')

        self.stdout.write(self.style.SUCCESS('Seed completed successfully'))
