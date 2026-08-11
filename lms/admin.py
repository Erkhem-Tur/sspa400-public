import re
from django import forms
from django.contrib import admin
from .models import (
    Assignment,
    Certificate,
    Course,
    CourseCategory,
    CourseModule,
    CourseUnit,
    CourseUnitProgress,
    Department,
    DiscussionPost,
    Enrollment,
    Lesson,
    LogEntry,
    Notification,
    PathwayProgress,
    QuizAttempt,
    QuizQuestion,
    QuizResult,
    Submission,
    TlOverride,
    UserProgress,
    Video,
    WallPost,
)


def extract_youtube_id(raw):
    """Accept full YouTube URLs or bare IDs and return just the 11-char ID."""
    raw = raw.strip()
    # youtu.be/ID  or  youtube.com/watch?v=ID  or  youtube.com/embed/ID
    patterns = [
        r'(?:youtu\.be/)([A-Za-z0-9_-]{11})',
        r'(?:youtube\.com/watch\?.*v=)([A-Za-z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})',
    ]
    for pat in patterns:
        m = re.search(pat, raw)
        if m:
            return m.group(1)
    # Already a bare ID (11 chars, alphanumeric + _ -)
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', raw):
        return raw
    return raw  # return as-is; validation will catch bad values


class VideoAdminForm(forms.ModelForm):
    # Override the field so full URLs (> 20 chars) pass field-level validation;
    # clean_youtube_id() then extracts the 11-char ID before saving to the model.
    youtube_id = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'placeholder': 'URL эсвэл ID — жишээ: https://youtu.be/qRiL9lnpAO8',
            'style': 'width:100%;max-width:520px;',
        }),
        help_text=(
            'Бүтэн YouTube URL эсвэл зөвхөн ID хэлбэрээр оруулж болно.<br>'
            '✅ https://youtu.be/qRiL9lnpAO8<br>'
            '✅ https://www.youtube.com/watch?v=qRiL9lnpAO8<br>'
            '✅ qRiL9lnpAO8'
        ),
    )

    class Meta:
        model = Video
        fields = '__all__'

    def clean_youtube_id(self):
        raw = self.cleaned_data.get('youtube_id', '')
        vid = extract_youtube_id(raw)
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
            raise forms.ValidationError(
                'YouTube ID олдсонгүй. URL эсвэл 11 тэмдэгтийн ID оруулна уу.'
            )
        return vid


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'created_at')
    ordering = ('order',)


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'batch_index', 'score', 'total', 'taken_at')
    list_filter = ('lesson',)
    ordering = ('-taken_at',)


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'role', 'instructor_requested', 'rank', 'department', 'total_score', 'missions_completed', 'study_minutes')
    list_filter = ('role', 'instructor_requested', 'department', 'rank')
    search_fields = ('user__username', 'full_name')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    form               = VideoAdminForm
    list_display       = ('title', 'order', 'youtube_id', 'is_published', 'created_at')
    list_display_links = ('title',)
    list_editable      = ('order', 'is_published')
    list_filter        = ('is_published',)
    search_fields      = ('title', 'description')
    ordering           = ('order', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'youtube_id', 'order', 'is_published'),
        }),
    )


@admin.register(TlOverride)
class TlOverrideAdmin(admin.ModelAdmin):
    list_display  = ('path', 'key', 'text', 'updated_at')
    list_filter   = ('path',)
    search_fields = ('key', 'text')
    ordering      = ('path', 'key')


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'rank', 'department', 'tasag', 'note', 'logged_at', 'ip')
    list_filter   = ('department', 'logged_at')
    search_fields = ('full_name', 'note')
    ordering      = ('-logged_at',)
    date_hierarchy = 'logged_at'


class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 0
    fields = ('title', 'order')


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'status', 'instructor', 'estimated_minutes', 'updated_at')
    list_filter = ('status', 'level', 'category')
    search_fields = ('title', 'description', 'instructor__username')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (CourseModuleInline,)


class CourseUnitInline(admin.TabularInline):
    model = CourseUnit
    extra = 0
    fields = ('title', 'kind', 'order', 'duration_minutes', 'is_published')


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = (CourseUnitInline,)


@admin.register(CourseUnit)
class CourseUnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'kind', 'order', 'is_published')
    list_filter = ('kind', 'is_published', 'module__course')
    search_fields = ('title', 'body', 'module__course__title')


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('prompt_preview', 'unit', 'kind', 'points', 'order')
    list_filter = ('kind', 'unit__module__course')

    @admin.display(description='Question')
    def prompt_preview(self, obj):
        return obj.prompt[:80]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'progress_percent', 'last_accessed_at')
    list_filter = ('status', 'course')
    search_fields = ('user__username', 'user__email', 'course__title')


@admin.register(CourseUnitProgress)
class CourseUnitProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'unit', 'percent', 'is_complete', 'updated_at')
    list_filter = ('is_complete', 'unit__module__course')
    search_fields = ('user__username', 'unit__title')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'unit', 'percentage', 'passed', 'requires_review', 'submitted_at')
    list_filter = ('passed', 'requires_review', 'unit__module__course')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('unit', 'due_at', 'max_points', 'allow_resubmission')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'grade', 'updated_at')
    list_filter = ('status', 'assignment__unit__module__course')
    search_fields = ('student__username', 'assignment__unit__title')


@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('author', 'unit', 'created_at', 'is_hidden')
    list_filter = ('is_hidden', 'unit__module__course')
    search_fields = ('author__username', 'body')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'code', 'issued_at')
    search_fields = ('user__username', 'course__title', 'code')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read',)


@admin.register(PathwayProgress)
class PathwayProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'pathway', 'completion_count', 'updated_at')
    list_filter = ('pathway',)


@admin.register(WallPost)
class WallPostAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'prompt', 'created_at')
    list_filter = ('prompt',)
    search_fields = ('author_name', 'content')
