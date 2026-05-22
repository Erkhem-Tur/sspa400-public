import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Sum
from django.utils import timezone

from .models import Lesson, QuizResult, UserProgress, Department, Video


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
