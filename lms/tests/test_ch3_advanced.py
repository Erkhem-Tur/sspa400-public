"""
Chapter 3 – Advanced: Auth boundaries, edge cases, and integration tests
=========================================================================
These tests cover staff-only views, cascade behaviour, complex filtering,
IP detection, and cross-cutting concerns that require multiple components
to work together correctly.

Topics covered
--------------
- dept_manage_view: auth enforcement, duplicate-name detection (case-insensitive)
- dept_edit_view: rename, delete, 404 on missing pk
- logbook_admin_view: staff-only, date/month/dept filtering, invalid filter values
- tl_save: staff-only, upsert semantics, missing fields, invalid JSON, GET → 405
- padlet_delete_view: staff-only, 404 on missing post, GET → 405
- QuizResult cascade delete when User is deleted
- IP address capture from X-Forwarded-For proxy header
- UserProgress.study_days() calculation
- WallPost IP capture
"""

import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from lms.models import (
    Department, Lesson, LogEntry, QuizResult,
    TlOverride, UserProgress, WallPost,
)


# ── dept_manage_view ──────────────────────────────────────────────────────────

class DeptManageViewAuthTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="user", password="pass", is_staff=False
        )

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(reverse("dept_manage"))
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_is_redirected(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("dept_manage"))
        self.assertNotEqual(response.status_code, 200)

    def test_staff_can_access_page(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("dept_manage")).status_code, 200)

    def test_staff_can_create_department(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("dept_manage"), {"name": "New Department"})
        self.assertTrue(Department.objects.filter(name="New Department").exists())

    def test_creating_department_redirects_to_dept_manage(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dept_manage"), {"name": "New"})
        self.assertRedirects(response, reverse("dept_manage"))

    def test_duplicate_name_shows_error_and_does_not_create(self):
        # 10 departments are seeded by migrations; track the count before and after
        before = Department.objects.count()
        Department.objects.create(name="TestAlpha", order=500)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dept_manage"), {"name": "TestAlpha"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "аль хэдийн байна")
        self.assertEqual(Department.objects.count(), before + 1)  # no new one added

    def test_duplicate_name_detection_is_case_insensitive(self):
        before = Department.objects.count()
        Department.objects.create(name="TestAlpha", order=500)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dept_manage"), {"name": "TESTALPHA"})
        self.assertContains(response, "аль хэдийн байна")
        self.assertEqual(Department.objects.count(), before + 1)

    def test_empty_name_shows_error_and_does_not_create(self):
        before = Department.objects.count()
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dept_manage"), {"name": ""})
        self.assertContains(response, "хоосон")
        self.assertEqual(Department.objects.count(), before)  # nothing added


# ── dept_edit_view ────────────────────────────────────────────────────────────

class DeptEditViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.dept = Department.objects.create(name="Alpha", order=1)

    def test_staff_can_get_edit_page(self):
        self.client.force_login(self.staff)
        self.assertEqual(
            self.client.get(reverse("dept_edit", args=[self.dept.pk])).status_code, 200
        )

    def test_staff_can_rename_department(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse("dept_edit", args=[self.dept.pk]),
            {"name": "Renamed", "order": 1},
        )
        self.dept.refresh_from_db()
        self.assertEqual(self.dept.name, "Renamed")

    def test_staff_can_delete_department(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse("dept_edit", args=[self.dept.pk]),
            {"action": "delete"},
        )
        self.assertFalse(Department.objects.filter(pk=self.dept.pk).exists())

    def test_delete_redirects_to_dept_manage(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("dept_edit", args=[self.dept.pk]),
            {"action": "delete"},
        )
        self.assertRedirects(response, reverse("dept_manage"))

    def test_rename_to_existing_name_shows_error(self):
        Department.objects.create(name="Beta", order=2)
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("dept_edit", args=[self.dept.pk]),
            {"name": "Beta", "order": 1},
        )
        self.assertContains(response, "аль хэдийн байна")
        self.dept.refresh_from_db()
        self.assertEqual(self.dept.name, "Alpha")

    def test_renaming_to_own_current_name_succeeds(self):
        # The exclude(pk=dept_id) in the view means same-name save is allowed
        self.client.force_login(self.staff)
        self.client.post(
            reverse("dept_edit", args=[self.dept.pk]),
            {"name": "Alpha", "order": 2},
        )
        self.dept.refresh_from_db()
        self.assertEqual(self.dept.order, 2)

    def test_edit_nonexistent_dept_returns_404(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dept_edit", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_empty_name_on_edit_shows_error(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("dept_edit", args=[self.dept.pk]),
            {"name": "", "order": 1},
        )
        self.assertContains(response, "хоосон")
        self.dept.refresh_from_db()
        self.assertEqual(self.dept.name, "Alpha")


# ── logbook_admin_view ────────────────────────────────────────────────────────

class LogbookAdminViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="user", password="pass", is_staff=False
        )
        self.dept = Department.objects.create(name="Alpha", order=1)
        self.entry_a = LogEntry.objects.create(full_name="Bat", department=self.dept)
        self.entry_b = LogEntry.objects.create(full_name="Saran", department=None)

    def test_non_staff_is_redirected(self):
        self.client.force_login(self.regular)
        self.assertNotEqual(
            self.client.get(reverse("logbook_admin")).status_code, 200
        )

    def test_anonymous_is_redirected(self):
        self.assertNotEqual(
            self.client.get(reverse("logbook_admin")).status_code, 200
        )

    def test_staff_sees_all_entries_by_default(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("logbook_admin"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entries"].count(), 2)

    def test_filter_by_dept_returns_only_matching_entries(self):
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("logbook_admin"), {"dept": str(self.dept.pk)}
        )
        self.assertEqual(response.context["entries"].count(), 1)
        self.assertEqual(response.context["entries"].first().full_name, "Bat")

    def test_invalid_date_string_does_not_crash_and_shows_all(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("logbook_admin"), {"date": "not-a-date"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entries"].count(), 2)

    def test_invalid_month_string_does_not_crash_and_shows_all(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("logbook_admin"), {"month": "bad-month"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entries"].count(), 2)

    def test_context_contains_today_count(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("logbook_admin"))
        self.assertIn("today_count", response.context)
        self.assertGreaterEqual(response.context["today_count"], 0)

    def test_context_contains_total_count(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("logbook_admin"))
        self.assertEqual(response.context["total_count"], 2)


# ── tl_save view ──────────────────────────────────────────────────────────────

class TlSaveViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="user", password="pass", is_staff=False
        )

    def _post(self, data, user=None):
        if user:
            self.client.force_login(user)
        return self.client.post(
            reverse("tl_save"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_user_is_redirected(self):
        response = self._post({"path": "/lesson/1/", "key": "title", "text": "Hello"})
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_is_redirected(self):
        response = self._post(
            {"path": "/lesson/1/", "key": "title", "text": "Hello"},
            user=self.regular,
        )
        self.assertNotEqual(response.status_code, 200)

    def test_staff_can_create_new_override(self):
        response = self._post(
            {"path": "/lesson/1/", "key": "title", "text": "Гарчиг"},
            user=self.staff,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertTrue(TlOverride.objects.filter(path="/lesson/1/", key="title").exists())

    def test_staff_can_update_existing_override(self):
        TlOverride.objects.create(path="/lesson/1/", key="title", text="Old")
        self._post(
            {"path": "/lesson/1/", "key": "title", "text": "New"},
            user=self.staff,
        )
        override = TlOverride.objects.get(path="/lesson/1/", key="title")
        self.assertEqual(override.text, "New")
        self.assertEqual(TlOverride.objects.count(), 1)

    def test_missing_fields_returns_ok_without_saving(self):
        # path present but key and text are absent → no save, still ok
        response = self._post({"path": "/lesson/1/"}, user=self.staff)
        self.assertEqual(response.json()["ok"], True)
        self.assertEqual(TlOverride.objects.count(), 0)

    def test_invalid_json_body_returns_400(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("tl_save"),
            data="not valid json {{{",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_get_returns_405(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("tl_save")).status_code, 405)


# ── padlet_delete_view ────────────────────────────────────────────────────────

class PadletDeleteViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="user", password="pass", is_staff=False
        )
        self.post = WallPost.objects.create(
            author_name="Test", prompt="learned", content="content"
        )

    def test_non_staff_cannot_delete_post(self):
        self.client.force_login(self.regular)
        self.client.post(reverse("padlet_delete", args=[self.post.pk]))
        self.assertTrue(WallPost.objects.filter(pk=self.post.pk).exists())

    def test_anonymous_cannot_delete_post(self):
        self.client.post(reverse("padlet_delete", args=[self.post.pk]))
        self.assertTrue(WallPost.objects.filter(pk=self.post.pk).exists())

    def test_staff_can_delete_post(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("padlet_delete", args=[self.post.pk]))
        self.assertFalse(WallPost.objects.filter(pk=self.post.pk).exists())

    def test_delete_redirects_to_padlet(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("padlet_delete", args=[self.post.pk]))
        self.assertRedirects(response, reverse("padlet"))

    def test_delete_nonexistent_post_returns_404(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("padlet_delete", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_get_returns_405(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("padlet_delete", args=[self.post.pk]))
        self.assertEqual(response.status_code, 405)


# ── Cascade delete ────────────────────────────────────────────────────────────

class QuizResultCascadeTest(TestCase):
    def test_quiz_results_deleted_when_user_is_deleted(self):
        user = User.objects.create_user(username="temp", password="pass")
        lesson = Lesson.objects.create(title="L", order=1)
        QuizResult.objects.create(
            user=user, lesson=lesson, batch_index=0, score=5, total=10
        )
        self.assertEqual(QuizResult.objects.count(), 1)
        user.delete()
        self.assertEqual(QuizResult.objects.count(), 0)

    def test_user_progress_deleted_when_user_is_deleted(self):
        user = User.objects.create_user(username="temp2", password="pass")
        UserProgress.objects.create(user=user)
        self.assertEqual(UserProgress.objects.count(), 1)
        user.delete()
        self.assertEqual(UserProgress.objects.count(), 0)


# ── IP address detection ──────────────────────────────────────────────────────

class IpDetectionInLogbookTest(TestCase):
    """The logbook view captures the real IP even when behind a proxy."""

    def test_ip_uses_first_entry_from_x_forwarded_for(self):
        # Simulates a request via a load balancer that appends the real IP first
        self.client.post(
            reverse("logbook"),
            {"full_name": "Proxy User"},
            HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1",
        )
        entry = LogEntry.objects.first()
        self.assertEqual(entry.ip, "203.0.113.5")

    def test_ip_falls_back_to_remote_addr_when_no_proxy_header(self):
        self.client.post(
            reverse("logbook"),
            {"full_name": "Direct User"},
            REMOTE_ADDR="192.168.1.100",
        )
        entry = LogEntry.objects.first()
        self.assertEqual(entry.ip, "192.168.1.100")


class IpDetectionInPadletTest(TestCase):
    """The padlet view captures the IP the same way."""

    def test_ip_uses_x_forwarded_for(self):
        self.client.post(
            reverse("padlet"),
            {
                "author_name": "Naran",
                "prompt": "learned",
                "content": "Something",
            },
            HTTP_X_FORWARDED_FOR="198.51.100.7, 10.0.0.2",
        )
        post = WallPost.objects.first()
        self.assertEqual(post.ip, "198.51.100.7")


# ── UserProgress.study_days() ─────────────────────────────────────────────────

class UserProgressStudyDaysTest(TestCase):
    def test_study_days_for_brand_new_user_is_zero(self):
        user = User.objects.create_user(username="new", password="pass")
        progress = UserProgress.objects.create(user=user)
        # date_joined was set to now(), so the delta in days should be 0
        self.assertEqual(progress.study_days(), 0)

    def test_study_days_is_always_non_negative(self):
        user = User.objects.create_user(username="new2", password="pass")
        progress = UserProgress.objects.create(user=user)
        self.assertGreaterEqual(progress.study_days(), 0)


# ── logbook today_entries scope ───────────────────────────────────────────────

class LogbookTodayOnlyTest(TestCase):
    """today_entries must only include entries logged today, not yesterday."""

    def test_yesterday_entry_is_not_shown(self):
        from datetime import timedelta
        from django.utils import timezone

        # Create an entry dated yesterday
        yesterday_entry = LogEntry.objects.create(full_name="Old")
        LogEntry.objects.filter(pk=yesterday_entry.pk).update(
            logged_at=timezone.now() - timedelta(days=1)
        )
        # Create today's entry via the view
        self.client.post(reverse("logbook"), {"full_name": "Today"})

        response = self.client.get(reverse("logbook"))
        names = [e.full_name for e in response.context["today_entries"]]
        self.assertIn("Today", names)
        self.assertNotIn("Old", names)

    def test_todays_entry_is_shown(self):
        self.client.post(reverse("logbook"), {"full_name": "Present"})
        response = self.client.get(reverse("logbook"))
        names = [e.full_name for e in response.context["today_entries"]]
        self.assertIn("Present", names)


# ── logbook_admin valid date and month filters ────────────────────────────────

class LogbookAdminValidFilterTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )
        from datetime import date, timedelta
        from django.utils import timezone
        self.today = timezone.now().date()
        self.entry_today = LogEntry.objects.create(full_name="Today")
        self.entry_old = LogEntry.objects.create(full_name="Old")
        LogEntry.objects.filter(pk=self.entry_old.pk).update(
            logged_at=timezone.now() - timedelta(days=40)
        )

    def test_date_filter_today_shows_only_todays_entries(self):
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("logbook_admin"),
            {"date": self.today.isoformat()},
        )
        names = [e.full_name for e in response.context["entries"]]
        self.assertIn("Today", names)
        self.assertNotIn("Old", names)

    def test_month_filter_current_month_excludes_old_entries(self):
        from django.utils import timezone
        month_str = timezone.now().strftime("%Y-%m")
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("logbook_admin"),
            {"month": month_str},
        )
        names = [e.full_name for e in response.context["entries"]]
        self.assertIn("Today", names)
        self.assertNotIn("Old", names)


# ── dept_manage order assignment ──────────────────────────────────────────────

class DeptManageOrderAssignmentTest(TestCase):
    """New department order is set to Department.objects.count() at creation."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )

    def test_new_dept_order_equals_count_at_creation_time(self):
        self.client.force_login(self.staff)
        count_before = Department.objects.count()
        self.client.post(reverse("dept_manage"), {"name": "TestNewDept"})
        new_dept = Department.objects.get(name="TestNewDept")
        self.assertEqual(new_dept.order, count_before)


# ── Management command: seed ──────────────────────────────────────────────────

class SeedCommandTest(TestCase):
    """The seed management command creates expected departments, lesson, and admin."""

    def test_seed_creates_lesson(self):
        from django.core.management import call_command
        call_command("seed", verbosity=0)
        from lms.models import Lesson
        self.assertTrue(
            Lesson.objects.filter(title__icontains="400").exists()
        )

    def test_seed_creates_departments(self):
        from django.core.management import call_command
        call_command("seed", verbosity=0)
        self.assertTrue(
            Department.objects.filter(name__icontains="Хамгаалалтын").exists()
        )

    def test_seed_creates_admin_superuser(self):
        from django.core.management import call_command
        from django.contrib.auth.models import User
        call_command("seed", verbosity=0)
        admin = User.objects.filter(username="admin").first()
        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_superuser)

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        from lms.models import Lesson
        call_command("seed", verbosity=0)
        dept_count_1 = Department.objects.filter(
            name__icontains="Хамгаалалтын"
        ).count()
        lesson_count_1 = Lesson.objects.count()
        call_command("seed", verbosity=0)
        dept_count_2 = Department.objects.filter(
            name__icontains="Хамгаалалтын"
        ).count()
        lesson_count_2 = Lesson.objects.count()
        self.assertEqual(dept_count_1, dept_count_2)
        self.assertEqual(lesson_count_1, lesson_count_2)


# ── Management command: demo ──────────────────────────────────────────────────

class DemoCommandTest(TestCase):
    """The demo command requires seed data and creates 12 realistic student profiles."""

    def setUp(self):
        from django.core.management import call_command
        call_command("seed", verbosity=0)

    def test_demo_creates_twelve_students(self):
        from django.core.management import call_command
        call_command("demo", verbosity=0)
        # 12 students from the STUDENTS list
        self.assertEqual(
            User.objects.filter(username__regex=r"^\w+\d{3}$").count(), 12
        )

    def test_demo_creates_quiz_results_for_students(self):
        from django.core.management import call_command
        call_command("demo", verbosity=0)
        self.assertGreater(QuizResult.objects.count(), 0)

    def test_demo_creates_user_progress_records(self):
        from django.core.management import call_command
        call_command("demo", verbosity=0)
        self.assertEqual(UserProgress.objects.count(), 12)

    def test_demo_is_idempotent(self):
        from django.core.management import call_command
        call_command("demo", verbosity=0)
        user_count_1 = User.objects.exclude(is_staff=True).count()
        call_command("demo", verbosity=0)
        user_count_2 = User.objects.exclude(is_staff=True).count()
        self.assertEqual(user_count_1, user_count_2)
