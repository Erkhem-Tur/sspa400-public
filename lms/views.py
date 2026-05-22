import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Sum
from django.utils import timezone

from .models import Lesson, QuizResult, UserProgress, Department, Video, LogEntry


# ── Public views (no login required) ────────────────────────────────────────

def dashboard_view(request):
    lessons = Lesson.objects.all()
    videos  = Video.objects.filter(is_published=True)
    ctx = {'lessons': lessons, 'videos': videos}
    return render(request, 'lms/dashboard.html', ctx)


def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    return render(request, 'lms/index.html', {'lesson': lesson})


def worksheets_view(request):
    return render(request, 'lms/worksheets.html')


def videos_view(request):
    videos = Video.objects.filter(is_published=True)
    return render(request, 'lms/videos.html', {'videos': videos})


# Quiz submit — save only if logged in, otherwise just return ok
@require_POST
def submit_quiz(request):
    try:
        data = json.loads(request.body)
        score = int(data.get('score', 0))
        total = int(data.get('total', 10))
        return JsonResponse({'status': 'ok', 'score': score, 'total': total})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# Study time — no-op on public version
@require_POST
def track_study_time(request):
    return JsonResponse({'status': 'ok'})


# ── Admin-only views (still protected) ──────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def dept_manage_view(request):
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            error = 'Хэлтсийн нэр хоосон байна.'
        elif Department.objects.filter(name__iexact=name).exists():
            error = f'"{name}" нэртэй хэлтэс аль хэдийн байна.'
        else:
            Department.objects.create(name=name, order=Department.objects.count())
            return redirect('dept_manage')
    return render(request, 'lms/dept_manage.html', {
        'departments': Department.objects.all(),
        'error': error,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def dept_edit_view(request, dept_id):
    dept = get_object_or_404(Department, pk=dept_id)
    error = None
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            dept.delete()
            return redirect('dept_manage')
        name = request.POST.get('name', '').strip()
        if not name:
            error = 'Нэр хоосон байна.'
        elif Department.objects.filter(name__iexact=name).exclude(pk=dept_id).exists():
            error = f'"{name}" нэртэй хэлтэс аль хэдийн байна.'
        else:
            dept.name = name
            dept.order = int(request.POST.get('order', dept.order))
            dept.save()
            return redirect('dept_manage')
    return render(request, 'lms/dept_edit.html', {'dept': dept, 'error': error})


# ── Logbook (public, no login) ───────────────────────────────────────────────

def logbook_view(request):
    departments = Department.objects.all()
    success = False
    error = None

    if request.method == 'POST':
        full_name    = request.POST.get('full_name', '').strip()
        rank         = request.POST.get('rank', '').strip()
        dept_id      = request.POST.get('department', '').strip()
        tasag        = request.POST.get('tasag', '').strip()
        tl_english   = request.POST.get('tl_english', '').strip()
        tl_mongolian = request.POST.get('tl_mongolian', '').strip()
        note         = request.POST.get('note', '').strip()

        if not full_name:
            error = 'Нэрээ оруулна уу.'
        else:
            parts = []
            if tl_english:
                parts.append(f'[EN] {tl_english}')
            if tl_mongolian:
                parts.append(f'[MN] {tl_mongolian}')
            if note:
                parts.append(note)
            combined_note = ' | '.join(parts)

            dept = Department.objects.filter(pk=dept_id).first() if dept_id else None
            ip   = (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                    or request.META.get('REMOTE_ADDR'))
            LogEntry.objects.create(
                full_name=full_name, rank=rank, tasag=tasag,
                department=dept, note=combined_note, ip=ip or None,
            )
            success = True

    # Today's entries
    from django.utils import timezone
    today = timezone.now().date()
    today_entries = LogEntry.objects.filter(logged_at__date=today).select_related('department')

    return render(request, 'lms/logbook.html', {
        'departments': departments,
        'today_entries': today_entries,
        'success': success,
        'error': error,
        'RANK_CHOICES': [r for r in __import__('lms.models', fromlist=['RANK_CHOICES']).RANK_CHOICES if r[0]],
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def logbook_admin_view(request):
    from django.utils import timezone
    date_str = request.GET.get('date', '')
    dept_id  = request.GET.get('dept', '')

    entries = LogEntry.objects.select_related('department').all()
    if date_str:
        try:
            from datetime import date
            d = date.fromisoformat(date_str)
            entries = entries.filter(logged_at__date=d)
        except ValueError:
            pass
    if dept_id:
        entries = entries.filter(department_id=dept_id)

    # Stats
    today = timezone.now().date()
    today_count = LogEntry.objects.filter(logged_at__date=today).count()
    total_count = LogEntry.objects.count()

    return render(request, 'lms/logbook_admin.html', {
        'entries': entries,
        'departments': Department.objects.all(),
        'today_count': today_count,
        'total_count': total_count,
        'date_filter': date_str,
        'dept_filter': dept_id,
    })


# ── Stub views (kept for URL reverse compatibility) ─────────────────────────

def login_view(request):
    return redirect('dashboard')

def logout_view(request):
    logout(request)
    return redirect('dashboard')

def register_view(request):
    return redirect('dashboard')

def setup_profile(request):
    return redirect('dashboard')

def profile_view(request):
    return redirect('dashboard')

def department_view(request):
    return redirect('dashboard')
