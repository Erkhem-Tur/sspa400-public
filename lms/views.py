import json
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Lesson, QuizResult, UserProgress, Department, Video, LogEntry, TlOverride, WallPost, RANK_CHOICES, PROMPT_CHOICES


# ── Public views (no login required) ────────────────────────────────────────

def dashboard_view(request):
    lessons = Lesson.objects.all()
    videos  = Video.objects.filter(is_published=True)
    ctx = {'lessons': lessons, 'videos': videos}
    return render(request, 'lms/dashboard.html', ctx)


def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if lesson.pk == 1:
        return render(request, 'lms/index.html', {'lesson': lesson})

    resource_file = ''
    if (
        'COP17' in lesson.title
        or 'SSPA_COP17_A1_English_Resource_Pack.docx' in lesson.description
    ):
        resource_file = 'lms/resources/SSPA_COP17_A1_English_Resource_Pack.docx'

    return render(request, 'lms/lesson_detail.html', {
        'lesson': lesson,
        'resource_file': resource_file,
    })


def worksheets_view(request):
    return render(request, 'lms/worksheets.html')


def tl_fetch(request):
    """Return all translation overrides for a given URL path as JSON."""
    path = request.GET.get('path', '')
    data = {o.key: o.text for o in TlOverride.objects.filter(path=path)}
    return JsonResponse(data)


@require_POST
@user_passes_test(lambda u: u.is_staff, login_url='/admin/login/')
def tl_save(request):
    """Save a single translation override (staff only)."""
    try:
        body = json.loads(request.body)
        path = body.get('path', '').strip()
        key  = body.get('key', '').strip()
        text = body.get('text', '').strip()
        if path and key and text:
            TlOverride.objects.update_or_create(
                path=path, key=key,
                defaults={'text': text}
            )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def past_tense_view(request):
    return render(request, 'lms/past_tense.html')


def present_simple_view(request):
    return render(request, 'lms/present_simple.html')


def past_continuous_view(request):
    return render(request, 'lms/past_continuous.html')


def usss_report_view(request):
    return render(request, 'lms/usss_report.html')


def gspr_article_view(request):
    return render(request, 'lms/gspr_article.html')


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

    # Today's entries — use localtime so Mongolia midnight is correct
    today = timezone.localtime(timezone.now()).date()
    today_entries = LogEntry.objects.filter(logged_at__date=today).select_related('department')

    return render(request, 'lms/logbook.html', {
        'departments': departments,
        'today_entries': today_entries,
        'success': success,
        'error': error,
        'RANK_CHOICES': [(r, l) for r, l in RANK_CHOICES if r],
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def logbook_admin_view(request):
    from django.utils import timezone
    from datetime import date

    date_str  = request.GET.get('date', '')
    month_str = request.GET.get('month', '')   # YYYY-MM
    dept_id   = request.GET.get('dept', '')

    entries = LogEntry.objects.select_related('department').all()

    if date_str:
        try:
            d = date.fromisoformat(date_str)
            entries = entries.filter(logged_at__date=d)
        except ValueError:
            pass
    elif month_str:
        try:
            year, mon = month_str.split('-')
            entries = entries.filter(logged_at__year=int(year), logged_at__month=int(mon))
        except (ValueError, AttributeError):
            pass

    if dept_id:
        entries = entries.filter(department_id=dept_id)

    # Stats
    today = timezone.now().date()
    today_count = LogEntry.objects.filter(logged_at__date=today).count()
    total_count = LogEntry.objects.count()

    # Monthly summary (last 6 months)
    from django.db.models.functions import TruncMonth
    from django.db.models import Count
    monthly = (LogEntry.objects
               .annotate(month=TruncMonth('logged_at'))
               .values('month')
               .annotate(cnt=Count('id'))
               .order_by('-month')[:6])

    return render(request, 'lms/logbook_admin.html', {
        'entries': entries,
        'departments': Department.objects.all(),
        'today_count': today_count,
        'total_count': total_count,
        'date_filter': date_str,
        'month_filter': month_str,
        'dept_filter': dept_id,
        'monthly': monthly,
    })


# ── Stub views (kept for URL reverse compatibility) ─────────────────────────

def padlet_view(request):
    error = None
    success = False
    if request.method == 'POST':
        author_name = request.POST.get('author_name', '').strip()
        prompt      = request.POST.get('prompt', '').strip()
        content     = request.POST.get('content', '').strip()
        valid_keys  = [k for k, _ in PROMPT_CHOICES]
        if not author_name:
            error = 'Нэрээ оруулна уу.'
        elif prompt not in valid_keys:
            error = 'Асуулт сонгоно уу.'
        elif not content:
            error = 'Хариултаа бичнэ үү.'
        else:
            ip = (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                  or request.META.get('REMOTE_ADDR'))
            WallPost.objects.create(
                author_name=author_name, prompt=prompt,
                content=content, ip=ip or None,
            )
            success = True

    posts = WallPost.objects.all()
    return render(request, 'lms/padlet.html', {
        'posts': posts,
        'error': error,
        'success': success,
        'PROMPT_CHOICES': PROMPT_CHOICES,
    })


@require_POST
@user_passes_test(lambda u: u.is_staff, login_url='/admin/login/')
def padlet_delete_view(request, post_id):
    get_object_or_404(WallPost, pk=post_id).delete()
    return redirect('padlet')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    from .forms import LoginForm
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get('next') or 'dashboard')
    return render(request, 'lms/login.html', {
        'form': form,
        'firebase_config': settings.FIREBASE_WEB_CONFIG,
    })


@require_POST
def firebase_auth_view(request):
    """Verify a Firebase ID token and establish a Django session."""
    from .firebase_utils import verify_id_token
    try:
        body = json.loads(request.body)
        id_token = body.get('idToken', '')
        if not id_token:
            return JsonResponse({'ok': False, 'error': 'idToken missing'}, status=400)

        decoded = verify_id_token(id_token)
        uid   = decoded['uid']
        email = decoded.get('email', '')
        name  = decoded.get('name', '')

        # Use a prefixed UID as the Django username so it never collides with
        # manually-created accounts.  UIDs are 28 chars; prefix keeps us < 150.
        username = f'fb_{uid}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'first_name': name.split()[0] if name else ''},
        )
        if not created and email and user.email != email:
            user.email = email
            user.save(update_fields=['email'])
        if created:
            user.set_unusable_password()
            user.save(update_fields=['password'])

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return JsonResponse({'ok': True, 'created': created})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


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
