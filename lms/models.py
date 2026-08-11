import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


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
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    full_name = models.CharField(max_length=200, blank=True)
    rank = models.CharField(max_length=100, blank=True, choices=RANK_CHOICES)
    profile_complete = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    instructor_requested = models.BooleanField(default=False)
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


class CourseCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'course categories'

    def __str__(self):
        return self.name


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = 'A1', 'Beginner (A1)'
        ELEMENTARY = 'A2', 'Elementary (A2)'
        INTERMEDIATE = 'B1', 'Intermediate (B1)'
        MIXED = 'MIXED', 'Mixed level'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=280, blank=True)
    description = models.TextField(blank=True)
    learning_outcomes = models.TextField(blank=True, help_text='One outcome per line.')
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_taught',
    )
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.BEGINNER)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    estimated_minutes = models.PositiveIntegerField(default=60)
    order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        indexes = [
            models.Index(fields=['status', 'level']),
            models.Index(fields=['instructor', 'status']),
        ]

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def module_count(self):
        return self.modules.count()

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['course', 'order'], name='unique_course_module_order'),
        ]

    def __str__(self):
        return f'{self.course.title}: {self.title}'


class CourseUnit(models.Model):
    class Kind(models.TextChoices):
        TEXT = 'TEXT', 'Text lesson'
        VIDEO = 'VIDEO', 'Video lesson'
        LISTENING = 'LISTENING', 'Listening practice'
        QUIZ = 'QUIZ', 'Quiz'
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'
        LIVE = 'LIVE', 'Live session'

    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=280, blank=True)
    body = models.TextField(blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.TEXT)
    order = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=10)
    video_url = models.URLField(blank=True, max_length=500)
    audio_script = models.TextField(blank=True)
    resource_url = models.URLField(blank=True, max_length=500)
    meeting_url = models.URLField(blank=True, max_length=500)
    pass_percent = models.PositiveSmallIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_required = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['module', 'order'], name='unique_module_unit_order'),
        ]

    @property
    def course(self):
        return self.module.course

    def get_absolute_url(self):
        return reverse('course_player', kwargs={'slug': self.module.course.slug, 'unit_id': self.pk})

    def __str__(self):
        return f'{self.module.course.title}: {self.title}'


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_accessed_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='unique_course_enrollment'),
        ]
        indexes = [models.Index(fields=['course', 'status'])]

    def __str__(self):
        return f'{self.user.username} in {self.course.title}'


class CourseUnitProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unit_progress')
    unit = models.ForeignKey(CourseUnit, on_delete=models.CASCADE, related_name='progress_records')
    percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_complete = models.BooleanField(default=False)
    seconds_spent = models.PositiveIntegerField(default=0)
    last_position_seconds = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'unit'], name='unique_user_unit_progress'),
        ]
        indexes = [models.Index(fields=['user', 'is_complete'])]

    def __str__(self):
        return f'{self.user.username}: {self.unit.title} ({self.percent}%)'


class QuizQuestion(models.Model):
    class Kind(models.TextChoices):
        MULTIPLE_CHOICE = 'MC', 'Multiple choice'
        TRUE_FALSE = 'TF', 'True / false'
        ESSAY = 'ESSAY', 'Essay'

    unit = models.ForeignKey(CourseUnit, on_delete=models.CASCADE, related_name='questions')
    prompt = models.TextField()
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.MULTIPLE_CHOICE)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['unit', 'order'], name='unique_unit_question_order'),
        ]

    @property
    def is_auto_gradable(self):
        return self.kind != self.Kind.ESSAY

    def __str__(self):
        return self.prompt[:80]


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_quiz_attempts')
    unit = models.ForeignKey(CourseUnit, on_delete=models.CASCADE, related_name='quiz_attempts')
    answers = models.JSONField(default=dict)
    score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    passed = models.BooleanField(default=False)
    requires_review = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_quiz_attempts',
    )

    class Meta:
        ordering = ['-submitted_at']
        indexes = [models.Index(fields=['unit', 'user', '-submitted_at'])]

    def __str__(self):
        return f'{self.user.username}: {self.unit.title} ({self.percentage}%)'


class Assignment(models.Model):
    unit = models.OneToOneField(CourseUnit, on_delete=models.CASCADE, related_name='assignment')
    instructions = models.TextField()
    due_at = models.DateTimeField(null=True, blank=True)
    max_points = models.PositiveSmallIntegerField(default=100)
    rubric = models.JSONField(default=list, blank=True)
    allow_resubmission = models.BooleanField(default=True)

    def __str__(self):
        return self.unit.title


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        NEEDS_REVISION = 'REVISION', 'Needs revision'
        GRADED = 'GRADED', 'Graded'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    response_text = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True, max_length=500)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    grade = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions',
    )

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['assignment', 'student'], name='unique_assignment_submission'),
        ]

    def __str__(self):
        return f'{self.student.username}: {self.assignment.unit.title}'


class DiscussionPost(models.Model):
    unit = models.ForeignKey(CourseUnit, on_delete=models.CASCADE, related_name='discussion_posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_discussion_posts')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    body = models.TextField(max_length=2000)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['unit', 'is_hidden', 'created_at'])]

    def __str__(self):
        return f'{self.author.username}: {self.body[:60]}'


class Certificate(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'course'], name='unique_course_certificate'),
        ]

    def get_absolute_url(self):
        return reverse('certificate_detail', kwargs={'code': self.code})

    def __str__(self):
        return f'{self.user.username}: {self.course.title}'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lms_notifications')
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read', '-created_at'])]

    def __str__(self):
        return self.title


class PathwayProgress(models.Model):
    """Server copy of progress for the existing static learning pathways."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pathway_progress')
    pathway = models.SlugField(max_length=80)
    completed = models.JSONField(default=list, blank=True)
    drafts = models.JSONField(default=dict, blank=True)
    scores = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['pathway']
        constraints = [
            models.UniqueConstraint(fields=['user', 'pathway'], name='unique_user_pathway'),
        ]

    @property
    def completion_count(self):
        return len(self.completed)

    def __str__(self):
        return f'{self.user.username}: {self.pathway}'
