import json
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Max, Prefetch, Q, Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from .forms import (
    AssignmentForm,
    CourseCategoryForm,
    CourseForm,
    CourseModuleForm,
    CourseUnitForm,
    DiscussionPostForm,
    ProfileForm,
    QuizQuestionForm,
    RegisterForm,
    SubmissionForm,
    SubmissionGradeForm,
)
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
    Notification,
    PathwayProgress,
    QuizAttempt,
    QuizQuestion,
    QuizResult,
    Submission,
    UserProgress,
)
from .services import (
    can_manage_course,
    course_units,
    ensure_user_progress,
    grade_quiz,
    grade_quiz_attempt,
    is_instructor,
    recalculate_enrollment,
    update_unit_progress,
)


def instructor_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not is_instructor(request.user):
            raise PermissionDenied('Instructor access is required.')
        return view_func(request, *args, **kwargs)

    return wrapped


def _unique_slug(model, value, instance=None):
    base = slugify(value)[:190] or 'course'
    slug = base
    counter = 2
    queryset = model.objects.all()
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


def _managed_course(request, slug):
    course = get_object_or_404(Course.objects.select_related('instructor', 'category'), slug=slug)
    if not can_manage_course(request.user, course):
        raise PermissionDenied('You cannot manage this course.')
    return course


def _visible_course(request, slug):
    course = get_object_or_404(Course.objects.select_related('instructor', 'category'), slug=slug)
    if course.status != Course.Status.PUBLISHED and not can_manage_course(request.user, course):
        raise Http404('Course not found.')
    return course


def _student_can_open(request, course):
    if can_manage_course(request.user, course):
        return True
    return Enrollment.objects.filter(
        user=request.user,
        course=course,
        status__in=[Enrollment.Status.ACTIVE, Enrollment.Status.COMPLETED],
    ).exists()


def _next_order(queryset):
    max_order = queryset.aggregate(max_order=Max('order'))['max_order']
    return 0 if max_order is None else max_order + 1


def _refresh_course_enrollments(course):
    for user_id in course.enrollments.exclude(status=Enrollment.Status.WITHDRAWN).values_list('user_id', flat=True):
        recalculate_enrollment(User.objects.get(pk=user_id), course)


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('learning_dashboard')

    initial_role = request.GET.get('role', UserProgress.Role.STUDENT).upper()
    if initial_role not in UserProgress.Role.values:
        initial_role = UserProgress.Role.STUDENT
    form = RegisterForm(request.POST or None, initial={'role': initial_role})
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        requested_role = form.cleaned_data['role']
        progress = ensure_user_progress(
            user,
            full_name=form.cleaned_data['full_name'],
            role=UserProgress.Role.STUDENT,
        )
        progress.full_name = form.cleaned_data['full_name']
        progress.instructor_requested = requested_role == UserProgress.Role.INSTRUCTOR
        progress.save(update_fields=['full_name', 'role', 'instructor_requested'])
        if progress.instructor_requested:
            for admin_id in User.objects.filter(is_staff=True, is_active=True).values_list('id', flat=True):
                Notification.objects.create(
                    user_id=admin_id,
                    title='Instructor access requested',
                    message=f'{progress.full_name or user.username} requested instructor access.',
                    link=reverse('admin_users'),
                )
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        if progress.instructor_requested:
            messages.info(request, 'Your account is ready. An administrator will review your instructor access request.')
        else:
            messages.success(request, 'Your account is ready. Complete your profile to begin.')
        return redirect('setup_profile')
    return render(request, 'lms/register.html', {'form': form, 'selected_role': initial_role})


@login_required
@require_http_methods(['GET', 'POST'])
def setup_profile(request):
    progress = ensure_user_progress(request.user, full_name=request.user.get_full_name())
    form = ProfileForm(request.POST or None, instance=progress)
    if request.method == 'POST' and form.is_valid():
        progress = form.save(commit=False)
        progress.profile_complete = True
        progress.save()
        if progress.full_name and request.user.first_name != progress.full_name:
            request.user.first_name = progress.full_name
            request.user.save(update_fields=['first_name'])
        messages.success(request, 'Profile saved.')
        return redirect('instructor_dashboard' if is_instructor(request.user) else 'learning_dashboard')
    return render(request, 'lms/setup_profile.html', {'form': form, 'progress': progress})


@login_required
@require_http_methods(['GET', 'POST'])
def profile_view(request):
    progress = ensure_user_progress(request.user, full_name=request.user.get_full_name())
    form = ProfileForm(request.POST or None, instance=progress)
    if request.method == 'POST' and form.is_valid():
        progress = form.save(commit=False)
        progress.profile_complete = True
        progress.save()
        request.user.first_name = progress.full_name
        request.user.save(update_fields=['first_name'])
        messages.success(request, 'Profile updated.')
        return redirect('profile')

    legacy_results = request.user.quiz_results.select_related('lesson').all()
    enrollments = request.user.enrollments.select_related('course').all()
    certificates = request.user.certificates.select_related('course').all()
    return render(request, 'lms/profile.html', {
        'progress': progress,
        'form': form,
        'results': legacy_results,
        'enrollments': enrollments,
        'certificates': certificates,
    })


@login_required
def learning_dashboard(request):
    progress = ensure_user_progress(request.user)
    enrollments = list(
        Enrollment.objects.filter(user=request.user)
        .select_related('course', 'course__instructor')
        .exclude(status=Enrollment.Status.WITHDRAWN)
    )
    enrolled_ids = [item.course_id for item in enrollments]
    recommended = (
        Course.objects.filter(status=Course.Status.PUBLISHED)
        .exclude(pk__in=enrolled_ids)
        .select_related('category', 'instructor')
        .order_by('-is_featured', 'order', 'title')[:4]
    )
    notifications = request.user.lms_notifications.filter(is_read=False)[:6]
    pathway_records = request.user.pathway_progress.all()
    return render(request, 'lms/learning_dashboard.html', {
        'profile': progress,
        'enrollments': enrollments,
        'recommended_courses': recommended,
        'certificates': request.user.certificates.select_related('course')[:4],
        'notifications': notifications,
        'pathway_records': pathway_records,
        'completed_count': sum(item.status == Enrollment.Status.COMPLETED for item in enrollments),
        'recent_quiz_attempts': request.user.course_quiz_attempts.select_related(
            'unit', 'unit__module__course'
        )[:5],
        'recent_submissions': request.user.assignment_submissions.filter(
            status=Submission.Status.GRADED
        ).select_related('assignment__unit', 'assignment__unit__module__course')[:5],
    })


def course_catalog(request):
    courses = Course.objects.filter(status=Course.Status.PUBLISHED).select_related('category', 'instructor')
    query = request.GET.get('q', '').strip()
    level = request.GET.get('level', '').strip()
    category = request.GET.get('category', '').strip()
    if query:
        courses = courses.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
        )
    if level in Course.Level.values:
        courses = courses.filter(level=level)
    if category.isdecimal():
        courses = courses.filter(category_id=int(category))
    courses = courses.annotate(
        module_total=Count('modules', distinct=True),
        learner_total=Count('enrollments', distinct=True),
    )

    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(request.user.enrollments.values_list('course_id', flat=True))
    return render(request, 'lms/catalog.html', {
        'courses': courses,
        'categories': CourseCategory.objects.filter(is_active=True),
        'levels': Course.Level.choices,
        'query': query,
        'selected_level': level,
        'selected_category': category,
        'enrolled_ids': enrolled_ids,
    })


def course_detail(request, slug):
    course = _visible_course(request, slug)
    modules = course.modules.prefetch_related(
        Prefetch('units', queryset=CourseUnit.objects.filter(is_published=True).order_by('order', 'id'))
    )
    enrollment = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    return render(request, 'lms/course_detail.html', {
        'course': course,
        'modules': modules,
        'enrollment': enrollment,
        'learning_outcomes': [line.strip() for line in course.learning_outcomes.splitlines() if line.strip()],
        'can_manage': can_manage_course(request.user, course),
    })


def public_law_quiz(request):
    """Public, device-local practice mode for the law question bank."""
    return render(request, 'lms/public_law_quiz.html')


@login_required
@require_POST
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)
    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
    if enrollment.status == Enrollment.Status.WITHDRAWN:
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.save(update_fields=['status', 'last_accessed_at'])
    if created:
        Notification.objects.create(
            user=request.user,
            title='Course added',
            message=f'{course.title} is now on your learning dashboard.',
            link=course.get_absolute_url(),
        )
    first_unit = course_units(course).first()
    messages.success(request, 'Course added to your dashboard.')
    return redirect(first_unit.get_absolute_url() if first_unit else course.get_absolute_url())


@login_required
def course_player(request, slug, unit_id=None):
    course = _visible_course(request, slug)
    if not _student_can_open(request, course):
        messages.info(request, 'Enroll in this free course before opening its lessons.')
        return redirect('course_detail', slug=slug)

    manager = can_manage_course(request.user, course)
    units = list(course_units(course, published_only=not manager))
    if not units:
        messages.info(request, 'This course does not have lessons yet.')
        return redirect('course_detail', slug=slug)

    if unit_id is None:
        unit = units[0]
    else:
        unit = get_object_or_404(CourseUnit.objects.select_related('module', 'module__course'), pk=unit_id)
        if unit.module.course_id != course.id or (not unit.is_published and not manager):
            raise Http404('Lesson not found.')

    current_index = next((index for index, item in enumerate(units) if item.pk == unit.pk), None)
    if current_index is None:
        raise Http404('Lesson not found.')

    progress_record = None
    progress_map = {}
    enrollment = None
    if not manager:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
        progress_record, _ = CourseUnitProgress.objects.get_or_create(user=request.user, unit=unit)
        progress_map = {
            item.unit_id: item
            for item in CourseUnitProgress.objects.filter(user=request.user, unit__module__course=course)
        }
        Enrollment.objects.filter(user=request.user, course=course).update(last_accessed_at=timezone.now())
    for item in units:
        item.user_progress = progress_map.get(item.pk)

    posts = DiscussionPost.objects.filter(unit=unit, parent__isnull=True, is_hidden=False).select_related(
        'author'
    ).prefetch_related(
        Prefetch(
            'replies',
            queryset=DiscussionPost.objects.filter(is_hidden=False).select_related('author'),
        )
    )
    assignment = Assignment.objects.filter(unit=unit).first()
    submission = None
    if assignment and not manager:
        submission = Submission.objects.filter(assignment=assignment, student=request.user).first()

    latest_attempt = None
    quiz_feedback = {}
    if not manager:
        attempt_id = request.GET.get('attempt', '')
        if attempt_id.isdecimal():
            latest_attempt = QuizAttempt.objects.filter(
                pk=int(attempt_id),
                user=request.user,
                unit=unit,
            ).first()
            feedback_items = request.session.pop(f'quiz_feedback_{attempt_id}', [])
            quiz_feedback = {str(item['question_id']): item for item in feedback_items}
        if latest_attempt is None:
            latest_attempt = QuizAttempt.objects.filter(user=request.user, unit=unit).first()
        if latest_attempt is not None and not quiz_feedback:
            for question in unit.questions.all():
                selected = latest_attempt.answers.get(str(question.pk), '')
                correct = selected.strip().casefold() == question.correct_answer.strip().casefold()
                quiz_feedback[str(question.pk)] = {
                    'question_id': question.pk,
                    'correct': correct,
                    'selected_answer': selected,
                    'correct_answer': question.correct_answer,
                    'explanation': question.explanation,
                }

    return render(request, 'lms/course_player.html', {
        'course': course,
        'unit': unit,
        'units': units,
        'previous_unit': units[current_index - 1] if current_index > 0 else None,
        'next_unit': units[current_index + 1] if current_index + 1 < len(units) else None,
        'progress_record': progress_record,
        'enrollment': enrollment,
        'progress_map': progress_map,
        'posts': posts,
        'discussion_form': DiscussionPostForm(),
        'assignment': assignment,
        'submission': submission,
        'submission_form': SubmissionForm(instance=submission),
        'latest_attempt': latest_attempt,
        'quiz_feedback': quiz_feedback,
        'can_manage': manager,
    })


@login_required
@require_POST
def update_progress(request, unit_id):
    unit = get_object_or_404(CourseUnit.objects.select_related('module', 'module__course'), pk=unit_id)
    course = unit.module.course
    if not _student_can_open(request, course):
        raise PermissionDenied('Enrollment required.')
    if can_manage_course(request.user, course):
        return JsonResponse({'ok': False, 'error': 'Instructor preview does not change progress.'}, status=400)
    if unit.kind in {CourseUnit.Kind.QUIZ, CourseUnit.Kind.ASSIGNMENT}:
        return JsonResponse({'ok': False, 'error': 'Complete this activity through its form.'}, status=400)

    try:
        data = json.loads(request.body or '{}')
        progress, enrollment = update_unit_progress(
            request.user,
            unit,
            percent=data.get('percent'),
            complete=data.get('complete') is True,
            seconds=data.get('seconds', 0),
            position=data.get('position'),
        )
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        return JsonResponse({'ok': False, 'error': str(error)}, status=400)
    return JsonResponse({
        'ok': True,
        'unit_percent': progress.percent,
        'complete': progress.is_complete,
        'course_percent': enrollment.progress_percent,
    })


@login_required
@require_POST
def submit_course_quiz(request, unit_id):
    unit = get_object_or_404(
        CourseUnit.objects.select_related('module', 'module__course').prefetch_related('questions'),
        pk=unit_id,
        kind=CourseUnit.Kind.QUIZ,
        is_published=True,
    )
    if not _student_can_open(request, unit.module.course) or can_manage_course(request.user, unit.module.course):
        raise PermissionDenied('Student enrollment required.')
    answers = {
        str(question.pk): request.POST.get(f'question_{question.pk}', '').strip()
        for question in unit.questions.all()
    }
    attempt, details = grade_quiz(request.user, unit, answers)
    if attempt.requires_review:
        messages.info(request, 'Submitted. Your instructor will review the written response.')
    elif attempt.passed:
        messages.success(request, f'Passed with {attempt.percentage}%.')
    else:
        messages.warning(request, f'{attempt.percentage}%. Review the feedback and try again.')
    request.session[f'quiz_feedback_{attempt.pk}'] = details
    return redirect(f'{unit.get_absolute_url()}?attempt={attempt.pk}#quiz')


@login_required
@require_POST
def post_discussion(request, unit_id):
    unit = get_object_or_404(CourseUnit.objects.select_related('module', 'module__course'), pk=unit_id)
    if not _student_can_open(request, unit.module.course):
        raise PermissionDenied('Course access required.')
    form = DiscussionPostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.unit = unit
        post.author = request.user
        parent_id = request.POST.get('parent_id', '')
        if parent_id.isdecimal():
            post.parent = get_object_or_404(DiscussionPost, pk=int(parent_id), unit=unit)
        post.save()
        if post.parent and post.parent.author_id != request.user.id:
            Notification.objects.create(
                user=post.parent.author,
                title='New discussion reply',
                message=f'{request.user.get_full_name() or request.user.username} replied in {unit.title}.',
                link=f'{unit.get_absolute_url()}#discussion',
            )
        messages.success(request, 'Your message was posted.')
    else:
        messages.error(request, 'Write a message between 1 and 2,000 characters.')
    return redirect(f'{unit.get_absolute_url()}#discussion')


@login_required
@require_POST
def submit_assignment(request, unit_id):
    assignment = get_object_or_404(
        Assignment.objects.select_related('unit', 'unit__module', 'unit__module__course'),
        unit_id=unit_id,
    )
    if not _student_can_open(request, assignment.unit.module.course) or can_manage_course(
        request.user, assignment.unit.module.course
    ):
        raise PermissionDenied('Student enrollment required.')
    submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    if submission and not assignment.allow_resubmission:
        messages.error(request, 'This assignment does not allow resubmission.')
        return redirect(assignment.unit.get_absolute_url())
    form = SubmissionForm(request.POST, instance=submission)
    if form.is_valid():
        submission = form.save(commit=False)
        submission.assignment = assignment
        submission.student = request.user
        submission.status = Submission.Status.SUBMITTED
        submission.grade = None
        submission.feedback = ''
        submission.graded_at = None
        submission.graded_by = None
        submission.save()
        instructor = assignment.unit.module.course.instructor
        if instructor and instructor != request.user:
            Notification.objects.create(
                user=instructor,
                title='Assignment submitted',
                message=f'{request.user.get_full_name() or request.user.username} submitted {assignment.unit.title}.',
                link=reverse('instructor_dashboard'),
            )
        messages.success(request, 'Assignment submitted.')
    else:
        messages.error(request, form.non_field_errors()[0] if form.non_field_errors() else 'Check your submission.')
    return redirect(f'{assignment.unit.get_absolute_url()}#assignment')


def certificate_detail(request, code):
    certificate = get_object_or_404(
        Certificate.objects.select_related('user', 'course', 'course__instructor'),
        code=code,
    )
    return render(request, 'lms/certificate.html', {'certificate': certificate})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(notification.link or 'learning_dashboard')


@instructor_required
def instructor_dashboard(request):
    courses = Course.objects.all() if request.user.is_staff else Course.objects.filter(instructor=request.user)
    courses = courses.select_related('category').annotate(
        learner_count=Count('enrollments', distinct=True),
        module_count_value=Count('modules', distinct=True),
    )
    course_filter = Q(assignment__unit__module__course__instructor=request.user)
    quiz_filter = Q(unit__module__course__instructor=request.user)
    if request.user.is_staff:
        course_filter = Q()
        quiz_filter = Q()
    pending_submissions = Submission.objects.filter(course_filter, status=Submission.Status.SUBMITTED).select_related(
        'student', 'assignment__unit', 'assignment__unit__module__course'
    )[:8]
    pending_quizzes = QuizAttempt.objects.filter(quiz_filter, requires_review=True).select_related(
        'user', 'unit', 'unit__module__course'
    )[:8]
    return render(request, 'lms/instructor_dashboard.html', {
        'courses': courses,
        'pending_submissions': pending_submissions,
        'pending_quizzes': pending_quizzes,
        'learner_total': Enrollment.objects.filter(course__in=courses).values('user').distinct().count(),
    })


@instructor_required
@require_http_methods(['GET', 'POST'])
def course_create(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.slug = _unique_slug(Course, course.title)
        course.status = Course.Status.DRAFT
        course.save()
        messages.success(request, 'Course created. Add the first module and lesson.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/course_form.html', {'form': form, 'page_title': 'Create course'})


@instructor_required
@require_http_methods(['GET', 'POST'])
def course_edit(request, slug):
    course = _managed_course(request, slug)
    original_status = course.status
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['status'] == Course.Status.PUBLISHED:
            published_units = CourseUnit.objects.filter(module__course=course, is_published=True)
            if not published_units.exists():
                form.add_error('status', 'Add at least one published lesson before publishing the course.')
            empty_quizzes = published_units.filter(kind=CourseUnit.Kind.QUIZ, questions__isnull=True)
            if empty_quizzes.exists():
                form.add_error('status', 'Every published quiz needs at least one question.')
        if form.errors:
            return render(request, 'lms/course_form.html', {
                'form': form,
                'course': course,
                'page_title': 'Edit course',
            })
        course = form.save(commit=False)
        course.slug = _unique_slug(Course, course.title, course)
        course.save()
        if course.status == Course.Status.PUBLISHED and original_status != course.status:
            for user_id in course.enrollments.values_list('user_id', flat=True):
                Notification.objects.create(
                    user_id=user_id,
                    title='Course updated',
                    message=f'{course.title} has new or updated material.',
                    link=course.get_absolute_url(),
                )
        _refresh_course_enrollments(course)
        messages.success(request, 'Course details saved.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/course_form.html', {
        'form': form,
        'course': course,
        'page_title': 'Edit course',
    })


@instructor_required
@require_POST
def course_archive(request, slug):
    course = _managed_course(request, slug)
    course.status = Course.Status.ARCHIVED
    course.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Course archived. Existing learner records were preserved.')
    return redirect('instructor_dashboard')


@instructor_required
def course_builder(request, slug):
    course = _managed_course(request, slug)
    modules = course.modules.prefetch_related(
        Prefetch('units', queryset=CourseUnit.objects.prefetch_related('questions').order_by('order', 'id'))
    )
    return render(request, 'lms/course_builder.html', {
        'course': course,
        'modules': modules,
    })


@instructor_required
@require_http_methods(['GET', 'POST'])
def module_create(request, slug):
    course = _managed_course(request, slug)
    form = CourseModuleForm(
        request.POST or None,
        initial={'order': _next_order(course.modules.all())},
    )
    if request.method == 'POST' and form.is_valid():
        module = form.save(commit=False)
        module.course = course
        module.save()
        messages.success(request, 'Module added.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/module_form.html', {'form': form, 'course': course, 'page_title': 'Add module'})


@instructor_required
@require_http_methods(['GET', 'POST'])
def module_edit(request, slug, module_id):
    course = _managed_course(request, slug)
    module = get_object_or_404(CourseModule, pk=module_id, course=course)
    form = CourseModuleForm(request.POST or None, instance=module)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Module saved.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/module_form.html', {
        'form': form,
        'course': course,
        'module': module,
        'page_title': 'Edit module',
    })


@instructor_required
@require_POST
def module_delete(request, slug, module_id):
    course = _managed_course(request, slug)
    module = get_object_or_404(CourseModule, pk=module_id, course=course)
    module.delete()
    _refresh_course_enrollments(course)
    messages.success(request, 'Module deleted.')
    return redirect('course_builder', slug=course.slug)


@instructor_required
@require_http_methods(['GET', 'POST'])
def unit_create(request, slug, module_id):
    course = _managed_course(request, slug)
    module = get_object_or_404(CourseModule, pk=module_id, course=course)
    form = CourseUnitForm(
        request.POST or None,
        initial={'order': _next_order(module.units.all())},
    )
    if request.method == 'POST' and form.is_valid():
        unit = form.save(commit=False)
        unit.module = module
        unit.save()
        if unit.kind == CourseUnit.Kind.ASSIGNMENT:
            Assignment.objects.get_or_create(unit=unit, defaults={'instructions': unit.body or 'Complete this assignment.'})
        _refresh_course_enrollments(course)
        messages.success(request, 'Lesson added.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/unit_form.html', {
        'form': form,
        'course': course,
        'module': module,
        'page_title': 'Add lesson or activity',
    })


@instructor_required
@require_http_methods(['GET', 'POST'])
def unit_edit(request, slug, unit_id):
    course = _managed_course(request, slug)
    unit = get_object_or_404(CourseUnit.objects.select_related('module'), pk=unit_id, module__course=course)
    form = CourseUnitForm(request.POST or None, instance=unit)
    if request.method == 'POST' and form.is_valid():
        unit = form.save()
        if unit.kind == CourseUnit.Kind.ASSIGNMENT:
            Assignment.objects.get_or_create(unit=unit, defaults={'instructions': unit.body or 'Complete this assignment.'})
        _refresh_course_enrollments(course)
        messages.success(request, 'Lesson saved.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/unit_form.html', {
        'form': form,
        'course': course,
        'module': unit.module,
        'unit': unit,
        'page_title': 'Edit lesson or activity',
    })


@instructor_required
@require_POST
def unit_delete(request, slug, unit_id):
    course = _managed_course(request, slug)
    unit = get_object_or_404(CourseUnit, pk=unit_id, module__course=course)
    unit.delete()
    _refresh_course_enrollments(course)
    messages.success(request, 'Lesson deleted.')
    return redirect('course_builder', slug=course.slug)


@instructor_required
@require_http_methods(['GET', 'POST'])
def question_create(request, slug, unit_id):
    course = _managed_course(request, slug)
    unit = get_object_or_404(CourseUnit, pk=unit_id, module__course=course, kind=CourseUnit.Kind.QUIZ)
    form = QuizQuestionForm(
        request.POST or None,
        initial={'order': _next_order(unit.questions.all())},
    )
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.unit = unit
        question.save()
        messages.success(request, 'Question added.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/question_form.html', {
        'form': form,
        'course': course,
        'unit': unit,
        'page_title': 'Add quiz question',
    })


@instructor_required
@require_http_methods(['GET', 'POST'])
def question_edit(request, slug, question_id):
    course = _managed_course(request, slug)
    question = get_object_or_404(QuizQuestion, pk=question_id, unit__module__course=course)
    form = QuizQuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Question saved.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/question_form.html', {
        'form': form,
        'course': course,
        'unit': question.unit,
        'question': question,
        'page_title': 'Edit quiz question',
    })


@instructor_required
@require_POST
def question_delete(request, slug, question_id):
    course = _managed_course(request, slug)
    question = get_object_or_404(QuizQuestion, pk=question_id, unit__module__course=course)
    question.delete()
    messages.success(request, 'Question deleted.')
    return redirect('course_builder', slug=course.slug)


@instructor_required
@require_http_methods(['GET', 'POST'])
def assignment_edit(request, slug, unit_id):
    course = _managed_course(request, slug)
    unit = get_object_or_404(CourseUnit, pk=unit_id, module__course=course, kind=CourseUnit.Kind.ASSIGNMENT)
    assignment, _ = Assignment.objects.get_or_create(unit=unit, defaults={'instructions': unit.body or 'Complete this assignment.'})
    form = AssignmentForm(request.POST or None, instance=assignment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Assignment settings saved.')
        return redirect('course_builder', slug=course.slug)
    return render(request, 'lms/assignment_form.html', {
        'form': form,
        'course': course,
        'unit': unit,
    })


@instructor_required
def course_gradebook(request, slug):
    course = _managed_course(request, slug)
    enrollments = course.enrollments.select_related('user', 'user__progress').exclude(
        status=Enrollment.Status.WITHDRAWN
    )
    rows = []
    for enrollment in enrollments:
        attempts = QuizAttempt.objects.filter(user=enrollment.user, unit__module__course=course)
        submissions = Submission.objects.filter(student=enrollment.user, assignment__unit__module__course=course)
        rows.append({
            'enrollment': enrollment,
            'quiz_average': attempts.aggregate(value=Avg('percentage'))['value'],
            'quiz_attempts': attempts.count(),
            'assignments_graded': submissions.filter(status=Submission.Status.GRADED).count(),
            'assignments_total': submissions.count(),
        })
    return render(request, 'lms/gradebook.html', {
        'course': course,
        'rows': rows,
        'pending_submissions': Submission.objects.filter(
            assignment__unit__module__course=course,
            status=Submission.Status.SUBMITTED,
        ).select_related('student', 'assignment__unit'),
        'pending_quizzes': QuizAttempt.objects.filter(
            unit__module__course=course,
            requires_review=True,
        ).select_related('user', 'unit'),
    })


@instructor_required
@require_http_methods(['GET', 'POST'])
def grade_submission(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related('assignment__unit__module__course', 'student'),
        pk=submission_id,
    )
    course = submission.assignment.unit.module.course
    if not can_manage_course(request.user, course):
        raise PermissionDenied('You cannot grade this submission.')
    form = SubmissionGradeForm(request.POST or None, instance=submission)
    if request.method == 'POST' and form.is_valid():
        submission = form.save(commit=False)
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        if submission.grade is not None:
            submission.status = Submission.Status.GRADED
        submission.save()
        if submission.status == Submission.Status.GRADED:
            update_unit_progress(submission.student, submission.assignment.unit, complete=True)
        Notification.objects.create(
            user=submission.student,
            title='Assignment reviewed',
            message=f'{submission.assignment.unit.title} has been reviewed.',
            link=submission.assignment.unit.get_absolute_url(),
        )
        messages.success(request, 'Grade and feedback saved.')
        return redirect('course_gradebook', slug=course.slug)
    return render(request, 'lms/submission_grade.html', {
        'submission': submission,
        'course': course,
        'form': form,
    })


@instructor_required
@require_http_methods(['GET', 'POST'])
def grade_quiz_review(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related('unit__module__course', 'user'),
        pk=attempt_id,
        requires_review=True,
    )
    course = attempt.unit.module.course
    if not can_manage_course(request.user, course):
        raise PermissionDenied('You cannot grade this attempt.')
    error = None
    if request.method == 'POST':
        try:
            score = Decimal(request.POST.get('score', ''))
            if score < 0 or score > attempt.max_score:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            error = f'Enter a score from 0 to {attempt.max_score}.'
        else:
            grade_quiz_attempt(
                attempt,
                score=score,
                feedback=request.POST.get('feedback', '').strip(),
                grader=request.user,
            )
            messages.success(request, 'Quiz grade saved.')
            return redirect('course_gradebook', slug=course.slug)
    return render(request, 'lms/quiz_grade.html', {
        'attempt': attempt,
        'course': course,
        'questions': attempt.unit.questions.all(),
        'error': error,
    })


@user_passes_test(lambda user: user.is_staff)
def admin_dashboard(request):
    return render(request, 'lms/admin_dashboard.html', {
        'user_count': User.objects.count(),
        'student_count': UserProgress.objects.filter(role=UserProgress.Role.STUDENT).count(),
        'instructor_count': UserProgress.objects.filter(role=UserProgress.Role.INSTRUCTOR).count(),
        'course_count': Course.objects.count(),
        'enrollment_count': Enrollment.objects.count(),
        'completion_count': Enrollment.objects.filter(status=Enrollment.Status.COMPLETED).count(),
        'recent_users': User.objects.select_related('progress').order_by('-date_joined')[:8],
        'recent_courses': Course.objects.select_related('instructor').order_by('-created_at')[:8],
    })


@user_passes_test(lambda user: user.is_staff)
@require_http_methods(['GET', 'POST'])
def admin_users(request):
    if request.method == 'POST':
        target = get_object_or_404(User, pk=request.POST.get('user_id'))
        action = request.POST.get('action')
        if action == 'toggle-active' and target != request.user:
            target.is_active = not target.is_active
            target.save(update_fields=['is_active'])
            messages.success(request, 'Account status updated.')
        elif action == 'set-role':
            role = request.POST.get('role')
            if role in UserProgress.Role.values:
                progress = ensure_user_progress(target)
                progress.role = role
                progress.instructor_requested = False
                progress.save(update_fields=['role', 'instructor_requested'])
                messages.success(request, 'User role updated.')
        return redirect('admin_users')
    users = User.objects.select_related('progress').order_by('username')
    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query)
        )
    return render(request, 'lms/admin_users.html', {
        'users': users,
        'query': query,
        'roles': UserProgress.Role.choices,
    })


@user_passes_test(lambda user: user.is_staff)
@require_http_methods(['GET', 'POST'])
def admin_categories(request):
    form = CourseCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.slug = _unique_slug(CourseCategory, category.name)
        category.save()
        messages.success(request, 'Category created.')
        return redirect('admin_categories')
    return render(request, 'lms/admin_categories.html', {
        'categories': CourseCategory.objects.annotate(course_count=Count('courses')),
        'form': form,
    })


@user_passes_test(lambda user: user.is_staff)
@require_http_methods(['GET', 'POST'])
def admin_category_edit(request, category_id):
    category = get_object_or_404(CourseCategory, pk=category_id)
    form = CourseCategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.slug = _unique_slug(CourseCategory, category.name, category)
        category.save()
        messages.success(request, 'Category saved.')
        return redirect('admin_categories')
    return render(request, 'lms/category_form.html', {'form': form, 'category': category})


@user_passes_test(lambda user: user.is_staff)
@require_POST
def admin_category_delete(request, category_id):
    category = get_object_or_404(CourseCategory, pk=category_id)
    name = category.name
    category.delete()
    messages.success(request, f'{name} was deleted. Existing courses were kept uncategorized.')
    return redirect('admin_categories')


@login_required
def department_progress(request):
    if not request.user.is_staff:
        raise PermissionDenied('Admin access is required.')

    dept_filter = request.GET.get('dept', '')
    search = request.GET.get('q', '').strip()
    departments = Department.objects.all()
    progress_records = UserProgress.objects.select_related('user', 'department').filter(
        user__is_staff=False
    ).order_by('-total_score')
    if dept_filter.isdecimal():
        progress_records = progress_records.filter(department_id=int(dept_filter))
    elif dept_filter:
        dept_filter = ''
    if search:
        progress_records = progress_records.filter(
            Q(full_name__icontains=search) | Q(user__username__icontains=search)
        )

    student_list = []
    for progress in progress_records:
        results = QuizResult.objects.filter(user=progress.user)
        total_points = results.aggregate(value=Sum('score'))['value'] or 0
        total_possible = results.aggregate(value=Sum('total'))['value'] or 0
        student_list.append({
            'full_name': progress.full_name or progress.user.get_full_name() or progress.user.username,
            'username': progress.user.username,
            'rank': progress.rank,
            'department': progress.department.name if progress.department else '-',
            'total_score': progress.total_score,
            'missions_completed': progress.missions_completed,
            'avg_pct': round(total_points / total_possible * 100) if total_possible else 0,
            'last': progress.last_accessed,
            'joined': progress.user.date_joined,
            'study_days': (timezone.now() - progress.user.date_joined).days,
            'study_hours': round(progress.study_minutes / 60, 1),
            'profile_complete': progress.profile_complete,
        })

    all_learners = UserProgress.objects.filter(user__is_staff=False)
    total_students = all_learners.count()
    total_missions = QuizResult.objects.count()
    aggregate_points = QuizResult.objects.aggregate(score=Sum('score'), total=Sum('total'))
    overall_avg_pct = round(
        (aggregate_points['score'] or 0) / (aggregate_points['total'] or 1) * 100
    )
    total_study_hours = round((all_learners.aggregate(value=Sum('study_minutes'))['value'] or 0) / 60, 1)
    dept_data = []
    for department in departments:
        members = department.members.filter(user__is_staff=False)
        dept_data.append({
            'id': department.id,
            'name': department.name,
            'count': members.count(),
            'avg_score': round(members.aggregate(value=Avg('total_score'))['value'] or 0),
        })
    return render(request, 'lms/department.html', {
        'student_list': student_list,
        'departments': departments,
        'dept_data': dept_data,
        'dept_filter': dept_filter,
        'search': search,
        'total_students': total_students,
        'total_missions': total_missions,
        'overall_avg_pct': overall_avg_pct,
        'total_study_hours': total_study_hours,
    })


@require_http_methods(['GET', 'POST'])
def pathway_progress_api(request, pathway):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Sign in to sync progress.'}, status=401)
    allowed = {'intermediate', 'beginner', 'course-library'}
    if pathway not in allowed:
        raise Http404('Pathway not found.')

    record, _ = PathwayProgress.objects.get_or_create(user=request.user, pathway=pathway)
    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'completed': record.completed,
            'drafts': record.drafts,
            'scores': record.scores,
            'updated_at': record.updated_at.isoformat(),
        })

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)
    completed = data.get('completed', [])
    drafts = data.get('drafts', {})
    scores = data.get('scores', {})
    if not isinstance(completed, list) or not isinstance(drafts, dict) or not isinstance(scores, dict):
        return JsonResponse({'ok': False, 'error': 'Invalid progress format.'}, status=400)
    if len(completed) > 500 or len(drafts) > 500 or len(scores) > 500:
        return JsonResponse({'ok': False, 'error': 'Progress payload is too large.'}, status=400)

    record.completed = list(dict.fromkeys(str(item)[:120] for item in completed))
    record.drafts = {str(key)[:120]: str(value)[:10000] for key, value in drafts.items()}
    record.scores = {str(key)[:120]: value for key, value in scores.items()}
    record.save()
    return JsonResponse({'ok': True, 'updated_at': record.updated_at.isoformat()})
