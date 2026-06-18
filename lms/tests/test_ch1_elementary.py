"""
Chapter 1 – Elementary: Model unit tests
========================================
These tests exercise model methods and computed properties directly,
without making any HTTP requests. They are the fastest tests to run
and the first line of defence when a model changes behaviour.

Topics covered
--------------
- __str__ representations
- Computed properties: percentage(), embed_url(), thumbnail_url(), study_hours()
- Default field values
- Model ordering (Meta.ordering)
- extract_youtube_id() utility from admin.py
- Database-level unique_together constraint
"""

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from lms.admin import extract_youtube_id
from lms.models import (
    Department, Lesson, LogEntry, QuizResult,
    TlOverride, UserProgress, Video, WallPost,
)


# ── Department ────────────────────────────────────────────────────────────────

class DepartmentModelTest(TestCase):
    def test_str(self):
        dept = Department.objects.create(name="Alpha", order=1)
        self.assertEqual(str(dept), "Alpha")

    def test_ordering_by_order_field(self):
        # Use order values well above the seeded data (0-9) to ensure isolation
        Department.objects.create(name="TestBeta", order=200)
        Department.objects.create(name="TestAlpha", order=100)
        names = list(
            Department.objects.filter(name__in=["TestBeta", "TestAlpha"])
            .values_list("name", flat=True)
        )
        self.assertEqual(names, ["TestAlpha", "TestBeta"])


# ── Lesson ────────────────────────────────────────────────────────────────────

class LessonModelTest(TestCase):
    def test_str(self):
        lesson = Lesson.objects.create(title="Lesson One", order=1)
        self.assertEqual(str(lesson), "Lesson One")

    def test_ordering_by_order_field(self):
        Lesson.objects.create(title="B", order=2)
        Lesson.objects.create(title="A", order=1)
        titles = list(
            Lesson.objects.filter(title__in=["A", "B"])
            .values_list("title", flat=True)
        )
        self.assertEqual(titles, ["A", "B"])


# ── QuizResult ────────────────────────────────────────────────────────────────

class QuizResultModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.lesson = Lesson.objects.create(title="Test Lesson", order=1)

    def _make(self, score, total):
        return QuizResult.objects.create(
            user=self.user, lesson=self.lesson,
            batch_index=0, score=score, total=total,
        )

    def test_percentage_normal(self):
        self.assertEqual(self._make(8, 10).percentage(), 80)

    def test_percentage_rounds_down(self):
        # 1/3 * 100 = 33.33 → rounds to 33
        self.assertEqual(self._make(1, 3).percentage(), 33)

    def test_percentage_rounds_up(self):
        # 2/3 * 100 = 66.67 → rounds to 67
        self.assertEqual(self._make(2, 3).percentage(), 67)

    def test_percentage_zero_total_returns_zero(self):
        self.assertEqual(self._make(0, 0).percentage(), 0)

    def test_percentage_perfect_score(self):
        self.assertEqual(self._make(10, 10).percentage(), 100)

    def test_str_contains_username_and_fraction(self):
        result = self._make(7, 10)
        text = str(result)
        self.assertIn("tester", text)
        self.assertIn("7/10", text)

    def test_str_contains_mission_number(self):
        # batch_index=0 → "Mission 1"
        result = self._make(5, 10)
        self.assertIn("Mission 1", str(result))


# ── UserProgress ──────────────────────────────────────────────────────────────

class UserProgressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="pass")
        self.dept = Department.objects.create(name="Dept A", order=1)
        self.progress = UserProgress.objects.create(
            user=self.user,
            department=self.dept,
            study_minutes=90,
        )

    def test_study_hours_exact(self):
        self.assertEqual(self.progress.study_hours(), 1.5)

    def test_study_hours_rounds_to_one_decimal(self):
        self.progress.study_minutes = 100
        # 100 / 60 = 1.6666... → 1.7
        self.assertEqual(self.progress.study_hours(), 1.7)

    def test_study_hours_zero(self):
        self.progress.study_minutes = 0
        self.assertEqual(self.progress.study_hours(), 0.0)

    def test_study_days_is_non_negative(self):
        # User was just created, so delta is effectively 0 days
        self.assertGreaterEqual(self.progress.study_days(), 0)

    def test_str_includes_username_and_score(self):
        self.progress.total_score = 42
        self.progress.save()
        self.assertIn("student", str(self.progress))
        self.assertIn("42", str(self.progress))

    def test_str_without_department_shows_fallback(self):
        user2 = User.objects.create_user(username="nodept", password="pass")
        progress = UserProgress.objects.create(user=user2, department=None)
        self.assertIn("Хэлтэсгүй", str(progress))


# ── Video ─────────────────────────────────────────────────────────────────────

class VideoModelTest(TestCase):
    def setUp(self):
        self.video = Video.objects.create(
            title="Rick Roll",
            youtube_id="dQw4w9WgXcQ",
            order=1,
        )

    def test_embed_url(self):
        self.assertEqual(
            self.video.embed_url(),
            "https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0&modestbranding=1",
        )

    def test_thumbnail_url(self):
        self.assertEqual(
            self.video.thumbnail_url(),
            "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        )

    def test_str(self):
        self.assertEqual(str(self.video), "Rick Roll")

    def test_is_published_by_default(self):
        self.assertTrue(self.video.is_published)


# ── LogEntry ──────────────────────────────────────────────────────────────────

class LogEntryModelTest(TestCase):
    def test_str_contains_full_name(self):
        dept = Department.objects.create(name="D1", order=1)
        entry = LogEntry.objects.create(full_name="Bold-Erdene", department=dept)
        self.assertIn("Bold-Erdene", str(entry))

    def test_str_contains_timestamp(self):
        entry = LogEntry.objects.create(full_name="Naran")
        # __str__ formats as YYYY-MM-DD HH:MM
        import re
        self.assertRegex(str(entry), r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")


# ── WallPost ──────────────────────────────────────────────────────────────────

class WallPostModelTest(TestCase):
    def test_str_contains_author_and_prompt_label(self):
        post = WallPost.objects.create(
            author_name="Naran",
            prompt="learned",
            content="Тест контент",
        )
        text = str(post)
        self.assertIn("Naran", text)
        self.assertIn("Өнөөдөр би сурсан зүйл", text)

    def test_get_prompt_display_difficult(self):
        post = WallPost.objects.create(
            author_name="A", prompt="difficult", content="hard"
        )
        self.assertIn("хэцүү", post.get_prompt_display())

    def test_get_prompt_display_next(self):
        post = WallPost.objects.create(
            author_name="B", prompt="next", content="plan"
        )
        self.assertIn("Дараагийн удаа", post.get_prompt_display())


# ── TlOverride ────────────────────────────────────────────────────────────────

class TlOverrideModelTest(TestCase):
    def test_str(self):
        override = TlOverride.objects.create(
            path="/lesson/1/", key="title", text="Гарчиг"
        )
        self.assertEqual(str(override), "/lesson/1/ | title")

    def test_unique_together_raises_integrity_error(self):
        TlOverride.objects.create(path="/lesson/1/", key="title", text="First")
        with self.assertRaises(IntegrityError):
            TlOverride.objects.create(path="/lesson/1/", key="title", text="Duplicate")

    def test_same_key_different_path_is_allowed(self):
        TlOverride.objects.create(path="/lesson/1/", key="title", text="One")
        # Should not raise
        TlOverride.objects.create(path="/lesson/2/", key="title", text="Two")
        self.assertEqual(TlOverride.objects.count(), 2)


# ── extract_youtube_id utility ────────────────────────────────────────────────

class ExtractYoutubeIdTest(TestCase):
    def test_bare_11_char_id(self):
        self.assertEqual(extract_youtube_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_youtu_be_url(self):
        self.assertEqual(
            extract_youtube_id("https://youtu.be/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_youtube_watch_url(self):
        self.assertEqual(
            extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_youtube_embed_url(self):
        self.assertEqual(
            extract_youtube_id("https://www.youtube.com/embed/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_youtube_shorts_url(self):
        self.assertEqual(
            extract_youtube_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(extract_youtube_id("  dQw4w9WgXcQ  "), "dQw4w9WgXcQ")

    def test_invalid_input_returned_as_is(self):
        # Invalid values pass through so VideoAdminForm.clean() can catch them
        result = extract_youtube_id("not-a-real-url")
        self.assertEqual(result, "not-a-real-url")

    def test_id_with_underscore_and_hyphen(self):
        self.assertEqual(extract_youtube_id("Ab1-Cd2_Ef3"), "Ab1-Cd2_Ef3")


# ── Model ordering ────────────────────────────────────────────────────────────

class QuizResultOrderingTest(TestCase):
    """QuizResult.Meta.ordering = ['-taken_at'] — newest first."""

    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.lesson = Lesson.objects.create(title="L", order=1)

    def test_newest_result_first(self):
        r1 = QuizResult.objects.create(
            user=self.user, lesson=self.lesson, batch_index=0, score=5, total=10
        )
        r2 = QuizResult.objects.create(
            user=self.user, lesson=self.lesson, batch_index=1, score=8, total=10
        )
        results = list(QuizResult.objects.all())
        # r2 was created after r1 so it should appear first
        self.assertEqual(results[0].pk, r2.pk)
        self.assertEqual(results[1].pk, r1.pk)


class VideoOrderingTest(TestCase):
    """Video.Meta.ordering = ['order', 'created_at'] — lower order first."""

    def test_lower_order_comes_first(self):
        v2 = Video.objects.create(title="B", youtube_id="bbbbbbbbbbb", order=2)
        v1 = Video.objects.create(title="A", youtube_id="aaaaaaaaaaa", order=1)
        pks = list(Video.objects.filter(pk__in=[v1.pk, v2.pk]).values_list("pk", flat=True))
        self.assertEqual(pks, [v1.pk, v2.pk])


class WallPostOrderingTest(TestCase):
    """WallPost.Meta.ordering = ['-created_at'] — newest first."""

    def test_newest_post_first(self):
        p1 = WallPost.objects.create(author_name="A", prompt="learned", content="first")
        p2 = WallPost.objects.create(author_name="B", prompt="learned", content="second")
        posts = list(WallPost.objects.filter(pk__in=[p1.pk, p2.pk]))
        self.assertEqual(posts[0].pk, p2.pk)


# ── Department DB-level unique name ──────────────────────────────────────────

class DepartmentUniqueNameTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        Department.objects.create(name="Alpha", order=1)
        with self.assertRaises(Exception):  # IntegrityError at DB level
            Department.objects.create(name="Alpha", order=2)


# ── UserProgress default values ───────────────────────────────────────────────

class UserProgressDefaultValuesTest(TestCase):
    def test_defaults_are_zero_on_creation(self):
        user = User.objects.create_user(username="fresh", password="pass")
        progress = UserProgress.objects.create(user=user)
        self.assertEqual(progress.total_score, 0)
        self.assertEqual(progress.missions_completed, 0)
        self.assertEqual(progress.study_minutes, 0)
        self.assertFalse(progress.profile_complete)
        self.assertIsNone(progress.department)
        self.assertEqual(progress.full_name, "")
