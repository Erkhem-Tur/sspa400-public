"""Creates 12 demo student accounts with realistic progress data."""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from lms.models import UserProgress, Department, Lesson, QuizResult

STUDENTS = [
    ("Б.Мөнхбаяр",  "munkh001",  "Ахмад | Captain",                   1),
    ("Д.Энхбаяр",   "enkh002",   "Хошууч | Major",                    1),
    ("Г.Батзориг",  "batzor003", "Дэслэгч | First Lieutenant",       1),
    ("Н.Солонго",   "solon004",  "Ахлагч | Sergeant",                 1),
    ("Т.Батбаяр",   "batbay005", "Дэд ахлагч | Junior Sergeant",      1),
    ("О.Номин",     "nomin006",  "Энгийн | Civilian",                 1),
    ("Ц.Болдбаатар","bold007",   "Ахлах дэслэгч | Senior Lieutenant", 2),
    ("Э.Мөнхцэцэг", "munkh008",  "Ахмад | Captain",                   2),
    ("Б.Ганболд",   "ganb009",   "Дэд хурандаа | Lieutenant Colonel", 2),
    ("Х.Түвшинбаяр","tuvshin010","Хошууч | Major",                    2),
    ("С.Анар",      "anar011",   "Ахлах ахлагч | Senior Sergeant",    2),
    ("Р.Баатарсүх", "baatar012", "Дэслэгч | First Lieutenant",       2),
]

class Command(BaseCommand):
    help = 'Create demo student data'

    def handle(self, *args, **kwargs):
        depts = list(Department.objects.all())
        if not depts:
            self.stdout.write(self.style.ERROR('No departments found. Run seed first.'))
            return

        lesson = Lesson.objects.first()
        if not lesson:
            self.stdout.write(self.style.ERROR('No lesson found. Run seed first.'))
            return

        created = 0
        for full_name, username, rank, dept_idx in STUDENTS:
            if User.objects.filter(username=username).exists():
                continue

            user = User.objects.create_user(username=username, password='demo1234')
            dept = depts[dept_idx - 1] if dept_idx - 1 < len(depts) else depts[0]

            days_ago = random.randint(5, 60)
            user.date_joined = timezone.now() - timedelta(days=days_ago)
            user.save()

            missions = random.randint(2, 15)
            total_score = 0
            for i in range(missions):
                score = random.randint(5, 10)
                total = 10
                taken_at = timezone.now() - timedelta(
                    days=random.randint(0, days_ago),
                    hours=random.randint(0, 12)
                )
                QuizResult.objects.create(
                    user=user, lesson=lesson,
                    batch_index=i, score=score, total=total,
                    taken_at=taken_at
                )
                total_score += score

            study_minutes = random.randint(30, 600)

            progress = UserProgress.objects.create(
                user=user,
                department=dept,
                full_name=full_name,
                rank=rank,
                profile_complete=True,
                total_score=total_score,
                missions_completed=missions,
                study_minutes=study_minutes,
            )
            progress.last_accessed = timezone.now() - timedelta(
                hours=random.randint(0, 72)
            )
            progress.save()
            created += 1
            self.stdout.write(f'  Created: {username}')

        self.stdout.write(self.style.SUCCESS(f'Done: {created} demo students. Password: demo1234'))
