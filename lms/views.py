import json
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Lesson, QuizResult, UserProgress, Department, Video, LogEntry, TlOverride, WallPost, RANK_CHOICES, PROMPT_CHOICES
from .course_catalog import get_course_lessons, get_course_modules
from .forms import LoginForm, LogbookEntryForm, WallPostForm


LESSON_RESOURCE_FILES = [
    (
        ('COP17', 'SSPA_COP17_A1_English_Resource_Pack.docx'),
        [
            {
                'path': 'lms/resources/SSPA_COP17_A1_English_Resource_Pack.docx',
                'title': 'Download classroom pack',
                'description': 'Editable Word document for printing and trainer preparation.',
                'button': 'Download DOCX',
            },
        ],
    ),
    (
        ('ALC Book 4 Lesson 2', 'SSPA_ALC_Book4_Lesson2_A1_Support_Pack.docx'),
        [
            {
                'path': 'lms/resources/SSPA_ALC_Book4_Lesson2_A1_Support_Pack.docx',
                'title': 'Download A1 support pack',
                'description': 'Editable lesson plan, worksheets, role-play cards, homework, and answer key.',
                'button': 'Download DOCX',
            },
            {
                'path': 'lms/resources/ALC_Book4_Lesson2.pdf',
                'title': 'Open ALC Book 4 Lesson 2',
                'description': 'The 27-page source lesson supplied for this course.',
                'button': 'Open PDF',
            },
        ],
    ),
]


def _client_ip(request):
    return (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR')
        or None
    )


def _first_form_error(form):
    for errors in form.errors.values():
        if errors:
            return errors[0]
    return None


# ── Public views (no login required) ────────────────────────────────────────

def dashboard_view(request):
    lessons = Lesson.objects.all()
    videos  = Video.objects.filter(is_published=True)
    ctx = {
        'lessons': lessons,
        'videos': videos,
        'course_modules': get_course_modules(),
        'course_lesson_total': len(get_course_lessons()),
    }
    return render(request, 'lms/dashboard.html', ctx)


def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if lesson.pk == 1:
        return render(request, 'lms/index.html', {'lesson': lesson})

    resource_files = []
    lesson_text = f'{lesson.title}\n{lesson.description}'
    for markers, files in LESSON_RESOURCE_FILES:
        if any(marker in lesson_text for marker in markers):
            resource_files = files
            break

    template_name = 'lms/lesson_detail.html'
    if 'ALC Book 4 Lesson 2' in lesson_text:
        template_name = 'lms/alc_lesson2.html'

    return render(request, template_name, {
        'lesson': lesson,
        'resource_files': resource_files,
        'lesson_outline': build_lesson_outline(lesson.description),
    })


def worksheets_view(request):
    if request.GET.get('tab') == 'vocabulary':
        return redirect('terminology')
    if request.GET.get('tab') == 'listening':
        return redirect('/terminology/?mode=listening')
    return render(request, 'lms/worksheets.html')


def terminology_view(request):
    return render(request, 'lms/terminology.html')


def course_library_view(request):
    lessons = get_course_lessons()
    return render(request, 'lms/course_library.html', {
        'course_lessons': lessons,
        'course_modules': get_course_modules(),
        'alc_lesson': Lesson.objects.filter(title__icontains='ALC Book 4 Lesson 2').first(),
        'course_counts': {
            level: sum(lesson['level'] == level for lesson in lessons)
            for level in ('A1', 'A2', 'B1')
        },
    })


def build_lesson_outline(description):
    """Split plain lesson descriptions into readable page sections."""
    lines = [line.strip() for line in (description or '').splitlines()]
    intro = []
    sections = []
    current = None

    for line in lines:
        if not line:
            continue
        if line.endswith(':') and not line.startswith('-'):
            current = {'title': line[:-1], 'copy': [], 'bullets': []}
            sections.append(current)
            continue
        if line.startswith('-'):
            if current is None:
                current = {'title': 'Key points', 'copy': [], 'bullets': []}
                sections.append(current)
            current['bullets'].append(line[1:].strip())
            continue
        if current is None:
            intro.append(line)
        else:
            current['copy'].append(line)

    return {
        'intro': intro,
        'sections': sections,
    }


def intermediate_course_view(request):
    operational_lessons = []
    for pathway_number, lesson in enumerate(
        (item for item in get_course_lessons() if item['level'] == 'B1'),
        start=9,
    ):
        combined = dict(lesson)
        combined['pathway_number'] = pathway_number
        operational_lessons.append(combined)
    return render(request, 'lms/intermediate_course.html', {
        'operational_lessons': operational_lessons,
    })


def beginner_course_view(request):
    return render(request, 'lms/beginner_course.html', {
        'beginner_lessons': [
            {
                'number': 0,
                'slug': 'alc_book4_summary',
                'book': 'Book 4 · Study Guide',
                'title': 'ALC Book 4 Speaking & Study Guide',
                'focus': 'Four speaking sessions, grammar, vocabulary, skills, ranks, and military time',
            },
            {
                'number': 1,
                'slug': 'bk4_l1',
                'book': 'Book 4 · Lesson 1',
                'title': 'Sports Event Protection + Simple Past',
                'focus': 'Sports vocabulary, regular past -ed, Did questions, SITREP reporting',
            },
            {
                'number': 2,
                'slug': 'bk4_l2',
                'book': 'Book 4 · Lesson 2',
                'title': 'Ranks, Duty, Military Time + Self-Introduction',
                'focus': 'Ranks, irregular past, Did questions, and 24-hour time',
            },
            {
                'number': 3,
                'slug': 'bk4_l3',
                'book': 'Book 4 · Lesson 3',
                'title': 'Clothes, Uniform Rules, Can/Must/May',
                'focus': 'Uniform vocabulary, ability, requirements, prohibition, and permission',
            },
            {
                'number': 4,
                'slug': 'bk5_l1',
                'book': 'Book 5 · Lesson 1',
                'title': 'Body, Doctor Visit, and Food Safety',
                'focus': 'Body, sickness, food choices, allergies, which/one/or',
            },
        ],
    })


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
        if path and key:
            if text:
                TlOverride.objects.update_or_create(
                    path=path, key=key,
                    defaults={'text': text}
                )
            else:
                TlOverride.objects.filter(path=path, key=key).delete()
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


# Legacy static-lesson quiz endpoint. Anonymous practice remains available, while
# signed-in attempts are also recorded on the learner profile.
@require_POST
def submit_quiz(request):
    try:
        data = json.loads(request.body)
        score = int(data.get('score', 0))
        total = int(data.get('total', 10))
        batch_index = int(data.get('batch_index', 0))
        if total <= 0 or total > 1000 or score < 0 or score > total or batch_index < 0:
            raise ValueError('Invalid quiz score.')
        saved = False
        lesson_id = data.get('lesson_id')
        if request.user.is_authenticated and lesson_id:
            lesson = get_object_or_404(Lesson, pk=lesson_id)
            QuizResult.objects.create(
                user=request.user,
                lesson=lesson,
                batch_index=batch_index,
                score=score,
                total=total,
            )
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            progress.total_score += score
            progress.missions_completed += 1
            progress.save(update_fields=['total_score', 'missions_completed', 'last_accessed'])
            saved = True
        return JsonResponse({'status': 'ok', 'score': score, 'total': total, 'saved': saved})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_POST
def track_study_time(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'ok', 'saved': False})
    try:
        data = json.loads(request.body or '{}')
        minutes = int(data.get('minutes', 0))
        if not 0 <= minutes <= 120:
            raise ValueError('Minutes must be between 0 and 120.')
        if minutes:
            progress, _ = UserProgress.objects.get_or_create(user=request.user)
            progress.study_minutes += minutes
            progress.save(update_fields=['study_minutes', 'last_accessed'])
        return JsonResponse({'status': 'ok', 'saved': bool(minutes)})
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=400)


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
            order_value = request.POST.get('order', str(dept.order)).strip()
            try:
                dept.order = int(order_value)
            except (TypeError, ValueError):
                error = 'Order must be a whole number.'
            else:
                dept.save()
                return redirect('dept_manage')
    return render(request, 'lms/dept_edit.html', {'dept': dept, 'error': error})


# ── Logbook (public, no login) ───────────────────────────────────────────────

def logbook_view(request):
    departments = Department.objects.all()
    success = False
    error = None
    form = LogbookEntryForm()

    if request.method == 'POST':
        form = LogbookEntryForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            LogEntry.objects.create(
                full_name=data['full_name'],
                rank=data.get('rank', ''),
                tasag=data.get('tasag', ''),
                department=data.get('department'),
                note=form.combined_note(),
                ip=_client_ip(request),
            )
            success = True
            form = LogbookEntryForm()
        else:
            error = _first_form_error(form)

    # Today's entries — use localtime so Mongolia midnight is correct
    today = timezone.localtime(timezone.now()).date()
    today_entries = LogEntry.objects.filter(logged_at__date=today).select_related('department')

    return render(request, 'lms/logbook.html', {
        'departments': departments,
        'today_entries': today_entries,
        'success': success,
        'error': error,
        'form': form,
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
        if dept_id.isdecimal():
            entries = entries.filter(department_id=int(dept_id))
        else:
            dept_id = ''

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
    form = WallPostForm()
    if request.method == 'POST':
        form = WallPostForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            WallPost.objects.create(
                author_name=data['author_name'],
                prompt=data['prompt'],
                content=data['content'],
                ip=_client_ip(request),
            )
            success = True
            form = WallPostForm()
        else:
            error = _first_form_error(form)

    posts = WallPost.objects.all()
    return render(request, 'lms/padlet.html', {
        'posts': posts,
        'error': error,
        'success': success,
        'form': form,
        'PROMPT_CHOICES': PROMPT_CHOICES,
    })


@require_POST
@user_passes_test(lambda u: u.is_staff, login_url='/admin/login/')
def padlet_delete_view(request, post_id):
    get_object_or_404(WallPost, pk=post_id).delete()
    return redirect('padlet')


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_account_home(request.user))
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect(_account_home(form.get_user()))
    return render(request, 'lms/login.html', {
        'form': form,
        'firebase_config': settings.FIREBASE_WEB_CONFIG,
        'next': request.GET.get('next', ''),
    })


def _account_home(user):
    if user.is_staff:
        return 'admin_dashboard'
    progress, _ = UserProgress.objects.get_or_create(user=user)
    if not progress.profile_complete:
        return 'setup_profile'
    if progress.role == UserProgress.Role.INSTRUCTOR:
        return 'instructor_dashboard'
    return 'learning_dashboard'


@require_POST
def firebase_auth_view(request):
    """Verify a Firebase ID token and establish a Django session."""
    from .firebase_utils import verify_id_token
    try:
        body = json.loads(request.body)
        id_token = body.get('idToken', '')
        if not isinstance(id_token, str) or not id_token or len(id_token) > 20000:
            return JsonResponse({'ok': False, 'error': 'idToken missing'}, status=400)

        decoded = verify_id_token(id_token)
        uid   = str(decoded['uid'])[:128]
        email = str(decoded.get('email', ''))[:254]
        name  = str(decoded.get('name', ''))[:200]

        # Use a prefixed UID as the Django username so it never collides with
        # manually-created accounts.  UIDs are 28 chars; prefix keeps us < 150.
        username = f'fb_{uid}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'first_name': name.split()[0][:150] if name else ''},
        )
        if not created and email and user.email != email:
            user.email = email
            user.save(update_fields=['email'])
        if created:
            user.set_unusable_password()
            user.save(update_fields=['password'])

        progress, _ = UserProgress.objects.get_or_create(
            user=user,
            defaults={'full_name': name, 'role': UserProgress.Role.STUDENT},
        )
        if name and not progress.full_name:
            progress.full_name = name
            progress.save(update_fields=['full_name', 'last_accessed'])

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        next_url = body.get('next', '')
        if not next_url or not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = '/setup-profile/' if not progress.profile_complete else '/learning/'
        return JsonResponse({'ok': True, 'created': created, 'redirect': next_url})
    except Exception as error:
        message = str(error) if settings.DEBUG else 'Google sign-in could not be verified. Please try again or use password login.'
        return JsonResponse({'ok': False, 'error': message}, status=400)


def logout_view(request):
    logout(request)
    return redirect('dashboard')
