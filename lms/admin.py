from django.contrib import admin
from .models import Department, Lesson, QuizResult, UserProgress, Video


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
    list_display       = ('title', 'order', 'youtube_id', 'is_published', 'created_at')
    list_display_links = ('title',)
    list_editable      = ('order', 'is_published')
    list_filter   = ('is_published',)
    search_fields = ('title', 'description')
    ordering      = ('order', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'youtube_id', 'order', 'is_published'),
        }),
    )
