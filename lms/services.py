from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from .models import (
    Certificate,
    Course,
    CourseUnit,
    CourseUnitProgress,
    Enrollment,
    Notification,
    QuizAttempt,
    QuizQuestion,
    UserProgress,
)


def ensure_user_progress(user, **defaults):
    progress, _ = UserProgress.objects.get_or_create(user=user, defaults=defaults)
    return progress


def is_instructor(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return ensure_user_progress(user).role == UserProgress.Role.INSTRUCTOR


def can_manage_course(user, course):
    return bool(user.is_authenticated and (user.is_staff or course.instructor_id == user.id))


def course_units(course, published_only=True):
    queryset = CourseUnit.objects.filter(module__course=course).select_related('module')
    if published_only:
        queryset = queryset.filter(is_published=True)
    return queryset.order_by('module__order', 'order', 'id')


@transaction.atomic
def recalculate_enrollment(user, course):
    enrollment, _ = Enrollment.objects.select_for_update().get_or_create(user=user, course=course)
    if enrollment.status == Enrollment.Status.COMPLETED and Certificate.objects.filter(
        user=user,
        course=course,
    ).exists():
        return enrollment
    required_ids = list(
        course_units(course).filter(is_required=True).values_list('id', flat=True)
    )
    total = len(required_ids)
    completed = CourseUnitProgress.objects.filter(
        user=user,
        unit_id__in=required_ids,
        is_complete=True,
    ).count()
    percentage = round(completed / total * 100) if total else 0
    enrollment.progress_percent = percentage

    if total and completed == total:
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.completed_at = enrollment.completed_at or timezone.now()
        certificate, created = Certificate.objects.get_or_create(user=user, course=course)
        if created:
            Notification.objects.create(
                user=user,
                title='Certificate ready',
                message=f'You completed {course.title}. Your certificate is ready to view.',
                link=certificate.get_absolute_url(),
            )
    elif enrollment.status != Enrollment.Status.WITHDRAWN:
        enrollment.status = Enrollment.Status.ACTIVE
        enrollment.completed_at = None

    enrollment.save(update_fields=['progress_percent', 'status', 'completed_at', 'last_accessed_at'])
    return enrollment


@transaction.atomic
def update_unit_progress(user, unit, *, percent=None, complete=None, seconds=0, position=None):
    progress, _ = CourseUnitProgress.objects.select_for_update().get_or_create(user=user, unit=unit)

    if percent is not None:
        progress.percent = max(progress.percent, min(100, max(0, int(percent))))
    if complete is True:
        progress.is_complete = True
        progress.percent = 100
        progress.completed_at = progress.completed_at or timezone.now()
    elif complete is False:
        progress.is_complete = False
        progress.completed_at = None
    if seconds:
        progress.seconds_spent += max(0, int(seconds))
    if position is not None:
        progress.last_position_seconds = max(0, int(position))

    progress.save()
    enrollment = recalculate_enrollment(user, unit.module.course)
    return progress, enrollment


def _same_answer(left, right):
    return str(left or '').strip().casefold() == str(right or '').strip().casefold()


@transaction.atomic
def grade_quiz(user, unit, answers):
    questions = list(unit.questions.all())
    max_score = sum(question.points for question in questions)
    score = Decimal('0')
    requires_review = False
    details = []

    for question in questions:
        answer = answers.get(str(question.pk), '')
        if question.kind == QuizQuestion.Kind.ESSAY:
            requires_review = True
            details.append({
                'question_id': question.pk,
                'correct': None,
                'explanation': 'Your instructor will review this response.',
            })
            continue

        correct = _same_answer(answer, question.correct_answer)
        if correct:
            score += Decimal(question.points)
        details.append({
            'question_id': question.pk,
            'correct': correct,
            'selected_answer': answer,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
        })

    if max_score:
        raw_percentage = score / Decimal(max_score) * Decimal('100')
        percentage = int(raw_percentage.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    else:
        percentage = 0
    passed = bool(questions and not requires_review and percentage >= unit.pass_percent)

    attempt = QuizAttempt.objects.create(
        user=user,
        unit=unit,
        answers=answers,
        score=score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        requires_review=requires_review,
    )

    if passed:
        update_unit_progress(user, unit, complete=True)
    else:
        update_unit_progress(user, unit, percent=percentage)

    return attempt, details


@transaction.atomic
def grade_quiz_attempt(attempt, *, score, feedback, grader):
    score = Decimal(str(score))
    score = min(max(score, Decimal('0')), attempt.max_score)
    percentage = 0
    if attempt.max_score:
        percentage = int(
            (score / attempt.max_score * Decimal('100')).quantize(
                Decimal('1'),
                rounding=ROUND_HALF_UP,
            )
        )
    attempt.score = score
    attempt.percentage = percentage
    attempt.passed = percentage >= attempt.unit.pass_percent
    attempt.requires_review = False
    attempt.feedback = feedback
    attempt.graded_by = grader
    attempt.graded_at = timezone.now()
    attempt.save()

    update_unit_progress(attempt.user, attempt.unit, complete=attempt.passed, percent=percentage)
    Notification.objects.create(
        user=attempt.user,
        title='Quiz graded',
        message=f'{attempt.unit.title}: {percentage}%.',
        link=attempt.unit.get_absolute_url(),
    )
    return attempt
