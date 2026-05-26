from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Lesson(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_results')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quiz_results')
    batch_index = models.IntegerField()
    score = models.IntegerField()
    total = models.IntegerField(default=10)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at']

    def percentage(self):
        return round(self.score / self.total * 100) if self.total else 0

    def __str__(self):
        return f"{self.user.username} – Mission {self.batch_index + 1}: {self.score}/{self.total}"


RANK_CHOICES = [
    ('', '-- Цолоо сонгоно уу --'),
    ('Энгийн | Civilian',                    'Энгийн | Civilian'),
    ('Дэд ахлагч | Junior Sergeant',         'Дэд ахлагч | Junior Sergeant'),
    ('Ахлагч | Sergeant',                    'Ахлагч | Sergeant'),
    ('Ахлах ахлагч | Senior Sergeant',       'Ахлах ахлагч | Senior Sergeant'),
    ('Дэслэгч | Second Lieutenant',          'Дэслэгч | Second Lieutenant'),
    ('Ахлах дэслэгч | First Lieutenant',     'Ахлах дэслэгч | First Lieutenant'),
    ('Ахмад | Captain',                      'Ахмад | Captain'),
    ('Хошууч | Major',                       'Хошууч | Major'),
    ('Дэд хурандаа | Lieutenant Colonel',    'Дэд хурандаа | Lieutenant Colonel'),
    ('Хурандаа | Colonel',                   'Хурандаа | Colonel'),
    ('Бригадын генерал | Brigadier General', 'Бригадын генерал | Brigadier General'),
]


class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    full_name = models.CharField(max_length=200, blank=True)
    rank = models.CharField(max_length=100, blank=True, choices=RANK_CHOICES)
    profile_complete = models.BooleanField(default=False)
    total_score = models.IntegerField(default=0)
    missions_completed = models.IntegerField(default=0)
    study_minutes = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)

    def study_days(self):
        from django.utils import timezone
        delta = timezone.now() - self.user.date_joined
        return delta.days

    def study_hours(self):
        return round(self.study_minutes / 60, 1)

    def __str__(self):
        dept = self.department.name if self.department else 'Хэлтэсгүй'
        return f"{self.user.username} ({dept}) – {self.total_score} оноо"


class Video(models.Model):
    title        = models.CharField(max_length=300, verbose_name='Гарчиг')
    description  = models.TextField(blank=True, verbose_name='Тайлбар')
    youtube_id   = models.CharField(
        max_length=20,
        verbose_name='YouTube видео ID',
        help_text='YouTube URL-аас авна. Жишээ: youtu.be/dQw4w9WgXcQ → dQw4w9WgXcQ',
    )
    order        = models.IntegerField(default=0, verbose_name='Дараалал')
    is_published = models.BooleanField(default=True, verbose_name='Нийтлэгдсэн')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Видео'
        verbose_name_plural = 'Видеонууд'

    def embed_url(self):
        return f'https://www.youtube.com/embed/{self.youtube_id}?rel=0&modestbranding=1'

    def thumbnail_url(self):
        return f'https://img.youtube.com/vi/{self.youtube_id}/hqdefault.jpg'

    def __str__(self):
        return self.title


class LogEntry(models.Model):
    full_name  = models.CharField(max_length=200, verbose_name='Нэр')
    rank       = models.CharField(max_length=100, blank=True, choices=RANK_CHOICES, verbose_name='Цол')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='Хэлтэс')
    tasag      = models.CharField(max_length=200, blank=True, verbose_name='Тасаг')
    note       = models.TextField(blank=True, verbose_name='Тэмдэглэл')
    logged_at  = models.DateTimeField(auto_now_add=True)
    ip         = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-logged_at']
        verbose_name = 'Бүртгэл'
        verbose_name_plural = 'Ирцийн бүртгэл'

    def __str__(self):
        return f"{self.full_name} – {self.logged_at.strftime('%Y-%m-%d %H:%M')}"


PROMPT_CHOICES = [
    ('learned',   'Өнөөдөр би сурсан зүйл...'),
    ('difficult', 'Надад хэцүү байсан...'),
    ('question',  'Би асуухыг хүссэн...'),
    ('next',      'Дараагийн удаа би...'),
]


class WallPost(models.Model):
    PROMPT_CHOICES = PROMPT_CHOICES
    author_name = models.CharField(max_length=100, verbose_name='Нэр')
    prompt      = models.CharField(max_length=20, choices=PROMPT_CHOICES, verbose_name='Асуулт')
    content     = models.TextField(max_length=300, verbose_name='Хариулт')
    created_at  = models.DateTimeField(auto_now_add=True)
    ip          = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Хана нийтлэл'
        verbose_name_plural = 'Хана нийтлэлүүд'

    def __str__(self):
        return f"{self.author_name} – {self.get_prompt_display()}"


class TlOverride(models.Model):
    """Inline-editable Mongolian translation overrides for lesson pages."""
    path       = models.CharField(max_length=200, verbose_name='Хуудасны зам')
    key        = models.CharField(max_length=100, verbose_name='Түлхүүр')
    text       = models.TextField(verbose_name='Монгол орчуулга')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('path', 'key')
        ordering = ['path', 'key']
        verbose_name = 'Орчуулгын засвар'
        verbose_name_plural = 'Орчуулгын засварууд'

    def __str__(self):
        return f'{self.path} | {self.key}'
