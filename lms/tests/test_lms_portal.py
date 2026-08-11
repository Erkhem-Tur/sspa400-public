import json

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from lms.models import (
    Assignment,
    Certificate,
    Course,
    CourseCategory,
    CourseModule,
    CourseUnit,
    CourseUnitProgress,
    DiscussionPost,
    Enrollment,
    Notification,
    PathwayProgress,
    QuizAttempt,
    QuizQuestion,
    Submission,
    UserProgress,
)


class PortalFixtureMixin:
    def setUp(self):
        self.category = CourseCategory.objects.create(name='Conversation', slug='conversation')
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@example.com',
            password='StrongPass734!',
            first_name='Instructor One',
        )
        UserProgress.objects.create(
            user=self.instructor,
            full_name='Instructor One',
            role=UserProgress.Role.INSTRUCTOR,
            profile_complete=True,
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='StrongPass734!',
            first_name='Student One',
        )
        UserProgress.objects.create(
            user=self.student,
            full_name='Student One',
            role=UserProgress.Role.STUDENT,
            profile_complete=True,
        )
        self.course = Course.objects.create(
            title='Clear Daily English',
            slug='clear-daily-english',
            short_description='Short speaking practice.',
            category=self.category,
            instructor=self.instructor,
            status=Course.Status.PUBLISHED,
        )
        self.module = CourseModule.objects.create(course=self.course, title='Start', order=0)
        self.text_unit = CourseUnit.objects.create(
            module=self.module,
            title='Useful phrases',
            body='Say hello and ask a follow-up question.',
            order=0,
        )
        self.quiz_unit = CourseUnit.objects.create(
            module=self.module,
            title='Check',
            kind=CourseUnit.Kind.QUIZ,
            order=1,
            pass_percent=70,
        )
        self.question = QuizQuestion.objects.create(
            unit=self.quiz_unit,
            prompt='Which phrase asks for repetition?',
            options=['Say again, please.', 'Goodbye.', 'No problem.'],
            correct_answer='Say again, please.',
            order=0,
        )

    def enroll_student(self):
        return Enrollment.objects.create(user=self.student, course=self.course)


class StudentLearningFlowTests(PortalFixtureMixin, TestCase):
    def test_public_catalog_and_course_detail_render(self):
        self.assertEqual(self.client.get(reverse('catalog')).status_code, 200)
        response = self.client.get(self.course.get_absolute_url())
        self.assertContains(response, self.course.title)
        self.assertContains(response, 'Free')

    def test_free_enrollment_opens_course_player(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('enroll_course', args=[self.course.slug]))
        self.assertRedirects(response, self.text_unit.get_absolute_url())
        self.assertTrue(Enrollment.objects.filter(user=self.student, course=self.course).exists())
        self.assertEqual(self.client.get(self.text_unit.get_absolute_url()).status_code, 200)

    def test_player_requires_enrollment(self):
        self.client.force_login(self.student)
        response = self.client.get(self.text_unit.get_absolute_url())
        self.assertRedirects(response, self.course.get_absolute_url())

    def test_progress_quiz_and_certificate_flow(self):
        self.enroll_student()
        self.client.force_login(self.student)
        response = self.client.post(
            reverse('update_progress', args=[self.text_unit.id]),
            data=json.dumps({'complete': True, 'seconds': 180}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['course_percent'], 50)

        response = self.client.post(
            reverse('submit_course_quiz', args=[self.quiz_unit.id]),
            {f'question_{self.question.id}': self.question.correct_answer},
        )
        self.assertEqual(response.status_code, 302)
        enrollment = Enrollment.objects.get(user=self.student, course=self.course)
        self.assertEqual(enrollment.progress_percent, 100)
        self.assertEqual(enrollment.status, Enrollment.Status.COMPLETED)
        self.assertTrue(Certificate.objects.filter(user=self.student, course=self.course).exists())

    def test_wrong_quiz_answer_does_not_complete_unit(self):
        self.enroll_student()
        self.client.force_login(self.student)
        self.client.post(
            reverse('submit_course_quiz', args=[self.quiz_unit.id]),
            {f'question_{self.question.id}': 'Goodbye.'},
        )
        attempt = QuizAttempt.objects.get(user=self.student, unit=self.quiz_unit)
        self.assertFalse(attempt.passed)
        self.assertFalse(CourseUnitProgress.objects.get(user=self.student, unit=self.quiz_unit).is_complete)

    def test_discussion_post_and_reply(self):
        self.enroll_student()
        self.client.force_login(self.student)
        self.client.post(reverse('post_discussion', args=[self.text_unit.id]), {'body': 'Could you repeat the example?'})
        post = DiscussionPost.objects.get(unit=self.text_unit)
        self.client.force_login(self.instructor)
        self.client.post(
            reverse('post_discussion', args=[self.text_unit.id]),
            {'body': 'Yes. Listen once, then repeat.', 'parent_id': post.id},
        )
        self.assertEqual(post.replies.count(), 1)
        self.assertTrue(Notification.objects.filter(user=self.student, title='New discussion reply').exists())

    def test_pathway_progress_sync_is_account_backed(self):
        self.client.force_login(self.student)
        endpoint = reverse('pathway_progress_api', args=['intermediate'])
        response = self.client.post(
            endpoint,
            data=json.dumps({'completed': ['foundation-1'], 'drafts': {'answer': 'Ready'}, 'scores': {'diagnostic': 80}}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        record = PathwayProgress.objects.get(user=self.student, pathway='intermediate')
        self.assertEqual(record.completed, ['foundation-1'])
        self.assertEqual(self.client.get(endpoint).json()['drafts']['answer'], 'Ready')


class RegistrationAndRoleTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('owner', 'owner@example.com', 'StrongPass734!')

    def registration_payload(self, **overrides):
        data = {
            'username': 'newlearner',
            'full_name': 'New Learner',
            'email': 'new@example.com',
            'role': UserProgress.Role.STUDENT,
            'password': 'VeryStrongPass734!',
            'password2': 'VeryStrongPass734!',
        }
        data.update(overrides)
        return data

    def test_student_registration_creates_profile_and_session(self):
        response = self.client.post(reverse('register'), self.registration_payload())
        self.assertRedirects(response, reverse('setup_profile'))
        user = User.objects.get(username='newlearner')
        self.assertEqual(user.progress.role, UserProgress.Role.STUDENT)
        self.assertFalse(user.progress.instructor_requested)
        self.assertIn('_auth_user_id', self.client.session)

    def test_instructor_registration_requires_admin_approval(self):
        self.client.post(
            reverse('register'),
            self.registration_payload(role=UserProgress.Role.INSTRUCTOR),
        )
        user = User.objects.get(username='newlearner')
        self.assertEqual(user.progress.role, UserProgress.Role.STUDENT)
        self.assertTrue(user.progress.instructor_requested)
        self.assertTrue(Notification.objects.filter(user=self.admin, title='Instructor access requested').exists())

    def test_admin_can_approve_instructor_role(self):
        user = User.objects.create_user('pending', 'pending@example.com', 'StrongPass734!')
        UserProgress.objects.create(user=user, instructor_requested=True)
        self.client.force_login(self.admin)
        self.client.post(reverse('admin_users'), {
            'user_id': user.id,
            'action': 'set-role',
            'role': UserProgress.Role.INSTRUCTOR,
        })
        user.progress.refresh_from_db()
        self.assertEqual(user.progress.role, UserProgress.Role.INSTRUCTOR)
        self.assertFalse(user.progress.instructor_requested)


class InstructorAuthoringTests(PortalFixtureMixin, TestCase):
    def test_student_cannot_open_instructor_workspace(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('instructor_dashboard')).status_code, 403)

    def test_instructor_can_open_own_builder_but_not_another_course(self):
        other = User.objects.create_user('other', password='StrongPass734!')
        UserProgress.objects.create(user=other, role=UserProgress.Role.INSTRUCTOR)
        foreign_course = Course.objects.create(title='Other course', slug='other-course', instructor=other)
        self.client.force_login(self.instructor)
        self.assertEqual(self.client.get(reverse('course_builder', args=[self.course.slug])).status_code, 200)
        self.assertEqual(self.client.get(reverse('course_builder', args=[foreign_course.slug])).status_code, 403)

    def test_new_course_is_always_created_as_draft(self):
        self.client.force_login(self.instructor)
        response = self.client.post(reverse('course_create'), {
            'title': 'New Speaking Course',
            'short_description': 'Practice.',
            'description': 'Clear practice.',
            'learning_outcomes': 'Speak clearly',
            'category': self.category.id,
            'level': Course.Level.BEGINNER,
            'estimated_minutes': 60,
            'status': Course.Status.PUBLISHED,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Course.objects.get(title='New Speaking Course').status, Course.Status.DRAFT)

    def test_empty_course_cannot_be_published(self):
        empty = Course.objects.create(title='Empty', slug='empty', instructor=self.instructor)
        self.client.force_login(self.instructor)
        response = self.client.post(reverse('course_edit', args=[empty.slug]), {
            'title': empty.title,
            'short_description': '',
            'description': '',
            'learning_outcomes': '',
            'category': '',
            'level': Course.Level.BEGINNER,
            'estimated_minutes': 60,
            'status': Course.Status.PUBLISHED,
        })
        self.assertEqual(response.status_code, 200)
        empty.refresh_from_db()
        self.assertEqual(empty.status, Course.Status.DRAFT)
        self.assertContains(response, 'Add at least one published lesson')


class AssignmentAndEssayGradingTests(PortalFixtureMixin, TestCase):
    def test_assignment_submission_and_grading_complete_activity(self):
        assignment_unit = CourseUnit.objects.create(
            module=self.module,
            title='Speaking report',
            kind=CourseUnit.Kind.ASSIGNMENT,
            order=2,
            is_required=False,
        )
        assignment = Assignment.objects.create(
            unit=assignment_unit,
            instructions='Write a short report.',
            max_points=20,
        )
        self.enroll_student()
        self.client.force_login(self.student)
        self.client.post(
            reverse('submit_assignment', args=[assignment_unit.id]),
            {'response_text': 'The visitor arrived at Gate Two at 14:00.'},
        )
        submission = Submission.objects.get(assignment=assignment, student=self.student)
        self.client.force_login(self.instructor)
        response = self.client.post(reverse('grade_submission', args=[submission.id]), {
            'grade': 18,
            'status': Submission.Status.GRADED,
            'feedback': 'Clear and concise.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CourseUnitProgress.objects.get(user=self.student, unit=assignment_unit).is_complete)

    def test_instructor_can_finish_manual_essay_review(self):
        self.question.kind = QuizQuestion.Kind.ESSAY
        self.question.options = []
        self.question.correct_answer = ''
        self.question.points = 5
        self.question.save()
        self.enroll_student()
        self.client.force_login(self.student)
        self.client.post(
            reverse('submit_course_quiz', args=[self.quiz_unit.id]),
            {f'question_{self.question.id}': 'I would confirm the time and location.'},
        )
        attempt = QuizAttempt.objects.get(user=self.student, unit=self.quiz_unit)
        self.assertTrue(attempt.requires_review)
        self.client.force_login(self.instructor)
        response = self.client.post(reverse('grade_quiz_review', args=[attempt.id]), {
            'score': '5',
            'feedback': 'Good answer.',
        })
        self.assertEqual(response.status_code, 302)
        attempt.refresh_from_db()
        self.assertTrue(attempt.passed)
        self.assertFalse(attempt.requires_review)


class SeedLmsTests(TestCase):
    def test_seed_adds_complete_free_starter_course(self):
        call_command('seed', verbosity=0)
        course = Course.objects.get(slug='daily-conversation-restart')
        self.assertEqual(course.status, Course.Status.PUBLISHED)
        self.assertGreaterEqual(course.modules.count(), 4)
        self.assertTrue(CourseUnit.objects.filter(module__course=course, kind=CourseUnit.Kind.LISTENING).exists())
        self.assertTrue(CourseUnit.objects.filter(module__course=course, kind=CourseUnit.Kind.QUIZ).exists())

    def test_seed_does_not_create_a_hardcoded_admin(self):
        call_command('seed', verbosity=0)
        self.assertFalse(User.objects.filter(username='admin').exists())
