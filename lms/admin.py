import re
from django import forms
from django.contrib import admin
from .models import Department, Lesson, QuizResult, UserProgress, Video, LogEntry, TlOverride


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
    class Meta:
        model = Video
        fields = '__all__'
        widgets = {
            'youtube_id': forms.TextInput(attrs={
                'placeholder': 'URL эсвэл ID — жишээ: https://youtu.be/qRiL9lnpAO8',
                'style': 'width:100%;max-width:520px;',
            }),
        }
        help_texts = {
            'youtube_id': (
                'Бүтэн YouTube URL эсвэл зөвхөн ID хэлбэрээр оруулж болно.<br>'
                '✅ https://youtu.be/qRiL9lnpAO8<br>'
                '✅ https://www.youtube.com/watch?v=qRiL9lnpAO8<br>'
                '✅ qRiL9lnpAO8'
            ),
        }

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
    list_display = ('user', 'full_name', 'rank', 'department', 'total_score', 'missions_completed', 'study_minutes')
    list_filter = ('department', 'rank')
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
