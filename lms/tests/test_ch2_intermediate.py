"""
Chapter 2 – Intermediate: View and form tests
=============================================
These tests make HTTP requests through Django's test client and validate
form logic. They verify status codes, template selection, context data,
and form-level validation errors.

Topics covered
--------------
- Public view status codes and correct template usage
- Context data (lessons in dashboard, only published videos, etc.)
- Stub views that redirect to dashboard
- tl_fetch JSON API
- submit_quiz and track_study_time JSON endpoints
- logbook_view GET + POST (valid / missing name)
- padlet_view GET + POST (valid / bad prompt / missing fields)
- RegisterForm validation (duplicate username, password mismatch, save)
- VideoAdminForm.clean_youtube_id() accepting multiple URL formats
"""

import json
import zipfile

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from lms.forms import RegisterForm
from lms.admin import VideoAdminForm
from lms.models import Department, Lesson, LogEntry, TlOverride, Video, WallPost


# ── Public views ──────────────────────────────────────────────────────────────

class PublicViewsTest(TestCase):
    def setUp(self):
        self.lesson = Lesson.objects.create(id=1, title="Test Lesson", order=1)

    def test_dashboard_returns_200(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/dashboard.html")

    def test_dashboard_context_contains_lesson(self):
        response = self.client.get(reverse("dashboard"))
        self.assertIn(self.lesson, response.context["lessons"])

    def test_dashboard_only_includes_published_videos(self):
        # 4 videos are seeded by migrations; add one published and one hidden
        initial_count = Video.objects.filter(is_published=True).count()
        Video.objects.create(title="TestPub", youtube_id="aaaaaaaaaaa", order=99, is_published=True)
        Video.objects.create(title="TestHidden", youtube_id="bbbbbbbbbbb", order=100, is_published=False)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(len(response.context["videos"]), initial_count + 1)
        titles = [v.title for v in response.context["videos"]]
        self.assertIn("TestPub", titles)
        self.assertNotIn("TestHidden", titles)

    def test_lesson_view_returns_200(self):
        response = self.client.get(reverse("lesson", args=[self.lesson.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/index.html")

    def test_lesson_view_context_has_lesson(self):
        response = self.client.get(reverse("lesson", args=[self.lesson.pk]))
        self.assertEqual(response.context["lesson"], self.lesson)

    def test_additional_lesson_shows_database_content(self):
        lesson = Lesson.objects.create(
            title="COP17 Registration & Access Control English - A1 Resource Pack",
            description="Teacher guide\nLearner handouts\nHomework",
            order=2,
        )
        response = self.client.get(reverse("lesson", args=[lesson.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/lesson_detail.html")
        self.assertContains(response, "COP17 Registration")
        self.assertContains(response, "Teacher guide")
        self.assertContains(response, "Learner handouts")
        self.assertNotContains(response, "400 Questions")

    def test_alc_support_lesson_links_docx_and_pdf(self):
        lesson = Lesson.objects.create(
            title="ALC Book 4 Lesson 2 Support English - SSPA Protection Officers",
            description="SSPA_ALC_Book4_Lesson2_A1_Support_Pack.docx",
            order=3,
        )
        response = self.client.get(reverse("lesson", args=[lesson.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/alc_lesson2.html")
        self.assertContains(response, "ALC Book 4 Lesson 2")
        self.assertContains(response, 'id="vocabGrid"')
        self.assertContains(response, 'id="finalQuiz"')
        self.assertContains(response, "lms/alc_lesson2.js")
        self.assertEqual(
            [resource["path"] for resource in response.context["resource_files"]],
            [
                "lms/resources/SSPA_ALC_Book4_Lesson2_A1_Support_Pack.docx",
                "lms/resources/ALC_Book4_Lesson2.pdf",
            ],
        )
        self.assertContains(response, "Open PDF")

    def test_non_alc_resource_lesson_keeps_generic_template(self):
        lesson = Lesson.objects.create(
            title="Another classroom resource",
            description="Teacher notes",
            order=4,
        )
        response = self.client.get(reverse("lesson", args=[lesson.pk]))
        self.assertTemplateUsed(response, "lms/lesson_detail.html")
        self.assertNotContains(response, 'id="finalQuiz"')

    def test_lesson_view_returns_404_for_missing_id(self):
        response = self.client.get(reverse("lesson", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_worksheets_returns_200(self):
        self.assertEqual(self.client.get(reverse("worksheets")).status_code, 200)

    def test_terminology_hub_returns_enhanced_vocabulary_and_listening(self):
        response = self.client.get(reverse("terminology"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/terminology.html")
        self.assertContains(response, 'id="vocabularyView"')
        self.assertContains(response, 'id="listeningView"')
        self.assertContains(response, "310 verified terms")

    def test_terminology_json_contains_complete_import(self):
        data_path = settings.BASE_DIR / "lms" / "static" / "lms" / "terminology.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        items = data["items"]
        self.assertEqual(len(items), 310)
        self.assertEqual(len(data["meta"]["modules"]), 13)
        self.assertEqual(len({item["item_id"] for item in items}), 310)
        self.assertTrue(all(item["audio_script"] for item in items))
        self.assertEqual(items[0]["front"], "Protectee")
        self.assertEqual(items[0]["back_mn"], "хамгаалалтад байгаа хүн")

    def test_course_library_is_structured_and_complete(self):
        response = self.client.get(reverse("course_library"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/course_library.html")
        self.assertEqual(len(response.context["course_lessons"]), 32)
        self.assertEqual(response.context["course_counts"], {"A1": 8, "A2": 12, "B1": 12})
        self.assertContains(response, 'id="courseRows"')
        self.assertContains(response, 'data-number="32"')
        self.assertContains(response, "500 Worksheets")

    def test_intermediate_pathway_combines_foundation_and_operational_lessons(self):
        response = self.client.get(reverse("intermediate_course"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/intermediate_course.html")
        self.assertEqual(len(response.context["operational_lessons"]), 12)
        self.assertEqual(response.context["operational_lessons"][0]["pathway_number"], 9)
        self.assertEqual(response.context["operational_lessons"][-1]["pathway_number"], 20)
        self.assertContains(response, "Intermediate English Pathway")
        self.assertContains(response, 'id="diagnosticOpen"')
        self.assertContains(response, 'id="finalOpen"')

    def test_intermediate_course_json_contains_complete_docx_import(self):
        data_path = settings.BASE_DIR / "lms" / "static" / "lms" / "intermediate_course.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        lessons = data["lessons"]
        self.assertEqual(len(lessons), 8)
        self.assertEqual(sum(len(lesson["vocabulary"]) for lesson in lessons), 48)
        self.assertEqual(len(data["diagnostic"]["questions"]), 15)
        self.assertTrue(all(len(lesson["reading_questions"]) == len(lesson["reading_answers"]) for lesson in lessons))
        self.assertTrue(all(len(lesson["language_practice"]) == len(lesson["language_answers"]) for lesson in lessons))
        self.assertTrue(data["final_assessment"]["reading"])
        self.assertTrue(data["final_assessment"]["writing"])
        self.assertTrue(data["final_assessment"]["speaking"])

    def test_intermediate_source_docx_is_available(self):
        resource = settings.BASE_DIR / "lms" / "static" / "lms" / "resources" / "Integrated_English_Course_Pack_A2-B1.docx"
        self.assertTrue(resource.exists())
        self.assertGreater(resource.stat().st_size, 50_000)

    def test_course_library_links_to_intermediate_pathway(self):
        response = self.client.get(reverse("course_library"))
        self.assertContains(response, reverse("intermediate_course"))
        self.assertContains(response, "8 foundation lessons + 12 operational applications")

    def test_beginner_alc_pack_contains_four_integrated_lessons(self):
        response = self.client.get(reverse("beginner_course"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/beginner_course.html")
        self.assertEqual(len(response.context["beginner_lessons"]), 4)
        self.assertContains(response, "ALC + SSPA Beginner Lesson Pack")
        self.assertContains(response, 'id="bpFrame"')
        self.assertContains(response, "Sports Event Protection + Simple Past")
        self.assertContains(response, "Body, Doctor Visit, and Food Safety")

    def test_beginner_pack_static_html_and_zip_are_available(self):
        static_root = settings.BASE_DIR / "lms" / "static" / "lms"
        lesson_root = static_root / "alc_beginner"
        expected = {"index.html", "bk4_l1.html", "bk4_l2.html", "bk4_l3.html", "bk5_l1.html"}
        example_counts = {
            "bk4_l1.html": 26,
            "bk4_l2.html": 30,
            "bk4_l3.html": 30,
            "bk5_l1.html": 40,
        }
        self.assertEqual({path.name for path in lesson_root.glob("*.html")}, expected)
        self.assertTrue(all((lesson_root / name).stat().st_size > 4_000 for name in expected))
        source_zip = static_root / "resources" / "alc_sspa_integrated_lesson_pack.zip"
        self.assertTrue(source_zip.exists())
        self.assertGreater(source_zip.stat().st_size, 20_000)

        with zipfile.ZipFile(source_zip) as lesson_pack:
            for name, expected_count in example_counts.items():
                lesson_text = (lesson_root / name).read_text(encoding="utf-8")
                zipped_text = lesson_pack.read(
                    f"alc_sspa_integrated_lessons/{name}"
                ).decode("utf-8-sig")

                for content in (lesson_text, zipped_text):
                    vocabulary = content.split(
                        '<section class="card" id="vocabulary">', 1
                    )[1].split("</table></section>", 1)[0]
                    self.assertNotIn("<input", vocabulary)
                    self.assertEqual(vocabulary.count('class="example"'), expected_count)
                    self.assertIn('<a class="btn light" href="#grammar">Grammar</a>', content)
                    self.assertIn('<section class="card" id="grammar"><h2>Grammar:', content)
                    self.assertIn("<input", content.split(vocabulary, 1)[1])

            lesson_text = (lesson_root / "bk4_l2.html").read_text(encoding="utf-8")
            zipped_text = lesson_pack.read(
                "alc_sspa_integrated_lessons/bk4_l2.html"
            ).decode("utf-8-sig")

        for content in (lesson_text, zipped_text):
            self.assertIn("<b>second lieutenant</b></td><td><div class=\"mn\">дэслэгч</div>", content)
            self.assertIn("<b>first lieutenant</b></td><td><div class=\"mn\">ахлах дэслэгч</div>", content)

    def test_course_library_links_to_beginner_alc_pack(self):
        response = self.client.get(reverse("course_library"))
        self.assertContains(response, reverse("beginner_course"))
        self.assertContains(response, "4 integrated ALC lessons")

    def test_dashboard_links_to_course_and_practice_centers(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, reverse("course_library"))
        self.assertContains(response, "Course Library")
        self.assertContains(response, "Practice Center")

    def test_videos_view_returns_200(self):
        self.assertEqual(self.client.get(reverse("videos")).status_code, 200)

    def test_videos_view_only_shows_published(self):
        initial_published = Video.objects.filter(is_published=True).count()
        Video.objects.create(title="TestV1", youtube_id="aaaaaaaaaaa", order=99, is_published=True)
        Video.objects.create(title="TestV2", youtube_id="bbbbbbbbbbb", order=100, is_published=False)
        response = self.client.get(reverse("videos"))
        self.assertEqual(response.context["videos"].count(), initial_published + 1)

    def test_past_tense_view(self):
        self.assertEqual(self.client.get(reverse("past_tense")).status_code, 200)

    def test_present_simple_view(self):
        self.assertEqual(self.client.get(reverse("present_simple")).status_code, 200)

    def test_past_continuous_view(self):
        self.assertEqual(self.client.get(reverse("past_continuous")).status_code, 200)

    def test_usss_report_view(self):
        self.assertEqual(self.client.get(reverse("usss_report")).status_code, 200)

    def test_gspr_article_view(self):
        self.assertEqual(self.client.get(reverse("gspr_article")).status_code, 200)


# ── Stub views ────────────────────────────────────────────────────────────────

class LoginViewTest(TestCase):
    """login_view now renders a real page with Google + password options."""

    def test_get_returns_login_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/login.html")

    def test_get_when_already_authenticated_redirects_to_dashboard(self):
        user = User.objects.create_user(username="u", password="p")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("login")), reverse("dashboard"))

    def test_post_valid_credentials_redirects_to_dashboard(self):
        User.objects.create_user(username="validuser", password="validpass")
        response = self.client.post(reverse("login"), {
            "username": "validuser", "password": "validpass",
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_post_invalid_credentials_shows_error(self):
        response = self.client.post(reverse("login"), {
            "username": "nobody", "password": "wrong",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lms/login.html")

    def test_firebase_config_in_context(self):
        response = self.client.get(reverse("login"))
        self.assertIn("firebase_config", response.context)


class StubViewsTest(TestCase):
    """Remaining stub views should redirect to dashboard."""

    def test_register_redirects_to_dashboard(self):
        self.assertRedirects(self.client.get(reverse("register")), reverse("dashboard"))

    def test_profile_redirects_to_dashboard(self):
        self.assertRedirects(self.client.get(reverse("profile")), reverse("dashboard"))

    def test_departments_redirects_to_dashboard(self):
        self.assertRedirects(self.client.get(reverse("departments")), reverse("dashboard"))

    def test_logout_redirects_to_dashboard(self):
        user = User.objects.create_user(username="u", password="p")
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("logout")), reverse("dashboard"))


# ── tl_fetch API ──────────────────────────────────────────────────────────────

class TlFetchViewTest(TestCase):
    def test_returns_empty_dict_when_no_overrides(self):
        response = self.client.get(reverse("tl_fetch"), {"path": "/lesson/1/"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_returns_keyed_overrides_for_matching_path(self):
        TlOverride.objects.create(path="/lesson/1/", key="title", text="Гарчиг")
        TlOverride.objects.create(path="/lesson/1/", key="body", text="Биет")
        data = self.client.get(reverse("tl_fetch"), {"path": "/lesson/1/"}).json()
        self.assertEqual(data["title"], "Гарчиг")
        self.assertEqual(data["body"], "Биет")

    def test_does_not_return_overrides_for_other_paths(self):
        TlOverride.objects.create(path="/other/", key="title", text="Other")
        data = self.client.get(reverse("tl_fetch"), {"path": "/lesson/1/"}).json()
        self.assertEqual(data, {})

    def test_empty_path_param_returns_empty_dict(self):
        TlOverride.objects.create(path="/lesson/1/", key="title", text="G")
        data = self.client.get(reverse("tl_fetch")).json()
        self.assertEqual(data, {})


# ── submit_quiz API ───────────────────────────────────────────────────────────

class SubmitQuizViewTest(TestCase):
    def test_post_valid_json_returns_score(self):
        response = self.client.post(
            reverse("submit_quiz"),
            data=json.dumps({"score": 8, "total": 10}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["score"], 8)
        self.assertEqual(data["total"], 10)

    def test_post_with_defaults(self):
        response = self.client.post(
            reverse("submit_quiz"),
            data=json.dumps({}),
            content_type="application/json",
        )
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["score"], 0)

    def test_get_returns_405(self):
        self.assertEqual(self.client.get(reverse("submit_quiz")).status_code, 405)


# ── track_study_time API ──────────────────────────────────────────────────────

class TrackStudyTimeViewTest(TestCase):
    def test_post_returns_ok(self):
        response = self.client.post(reverse("track_study_time"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_get_returns_405(self):
        self.assertEqual(self.client.get(reverse("track_study_time")).status_code, 405)


# ── logbook_view ──────────────────────────────────────────────────────────────

class LogbookViewTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Alpha", order=1)

    def test_get_returns_200(self):
        self.assertEqual(self.client.get(reverse("logbook")).status_code, 200)

    def test_get_context_contains_departments(self):
        response = self.client.get(reverse("logbook"))
        self.assertIn(self.dept, response.context["departments"])

    def test_post_valid_creates_entry(self):
        self.client.post(reverse("logbook"), {
            "full_name": "Bat-Erdene",
            "rank": "Ахмад | Captain",
            "department": str(self.dept.pk),
            "tasag": "G2",
            "note": "Оролцсон",
        })
        self.assertEqual(LogEntry.objects.count(), 1)
        self.assertEqual(LogEntry.objects.first().full_name, "Bat-Erdene")

    def test_post_combines_note_parts(self):
        self.client.post(reverse("logbook"), {
            "full_name": "Naran",
            "tl_english": "Hello",
            "tl_mongolian": "Сайн байна уу",
            "note": "Extra",
        })
        entry = LogEntry.objects.first()
        self.assertIn("[EN] Hello", entry.note)
        self.assertIn("[MN] Сайн байна уу", entry.note)
        self.assertIn("Extra", entry.note)

    def test_post_missing_name_shows_error_and_no_entry_created(self):
        response = self.client.post(reverse("logbook"), {"full_name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Нэрээ оруулна уу")
        self.assertEqual(LogEntry.objects.count(), 0)

    def test_post_success_flag_is_true_in_context(self):
        response = self.client.post(reverse("logbook"), {
            "full_name": "Naran",
            "rank": "",
            "department": "",
        })
        self.assertTrue(response.context["success"])

    def test_post_error_flag_is_set_on_missing_name(self):
        response = self.client.post(reverse("logbook"), {"full_name": ""})
        self.assertIsNotNone(response.context["error"])


# ── padlet_view ───────────────────────────────────────────────────────────────

class PadletViewTest(TestCase):
    def test_get_returns_200(self):
        self.assertEqual(self.client.get(reverse("padlet")).status_code, 200)

    def test_get_shows_existing_posts(self):
        WallPost.objects.create(author_name="A", prompt="learned", content="X")
        response = self.client.get(reverse("padlet"))
        self.assertEqual(response.context["posts"].count(), 1)

    def test_post_valid_creates_wall_post(self):
        self.client.post(reverse("padlet"), {
            "author_name": "Naran",
            "prompt": "learned",
            "content": "Today I learned about Django tests.",
        })
        self.assertEqual(WallPost.objects.count(), 1)
        self.assertEqual(WallPost.objects.first().author_name, "Naran")

    def test_post_missing_author_name_shows_error(self):
        response = self.client.post(reverse("padlet"), {
            "author_name": "",
            "prompt": "learned",
            "content": "content",
        })
        self.assertContains(response, "Нэрээ оруулна уу")
        self.assertEqual(WallPost.objects.count(), 0)

    def test_post_invalid_prompt_key_shows_error(self):
        response = self.client.post(reverse("padlet"), {
            "author_name": "Naran",
            "prompt": "totally_wrong_key",
            "content": "content",
        })
        self.assertContains(response, "Асуулт сонгоно уу")
        self.assertEqual(WallPost.objects.count(), 0)

    def test_post_missing_content_shows_error(self):
        response = self.client.post(reverse("padlet"), {
            "author_name": "Naran",
            "prompt": "learned",
            "content": "",
        })
        self.assertContains(response, "Хариултаа бичнэ үү")
        self.assertEqual(WallPost.objects.count(), 0)

    def test_post_success_flag_is_true_in_context(self):
        response = self.client.post(reverse("padlet"), {
            "author_name": "Naran",
            "prompt": "learned",
            "content": "Some content",
        })
        self.assertTrue(response.context["success"])


# ── RegisterForm ──────────────────────────────────────────────────────────────

class RegisterFormTest(TestCase):
    def test_valid_form_is_valid(self):
        form = RegisterForm(data={
            "username": "newuser",
            "password": "secret123",
            "password2": "secret123",
        })
        self.assertTrue(form.is_valid())

    def test_password_mismatch_is_invalid(self):
        form = RegisterForm(data={
            "username": "newuser",
            "password": "secret123",
            "password2": "different",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Нууц үг таарахгүй байна", str(form.errors))

    def test_duplicate_username_is_invalid(self):
        User.objects.create_user(username="existing", password="pass")
        form = RegisterForm(data={
            "username": "existing",
            "password": "secret123",
            "password2": "secret123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Энэ нэр бүртгэлтэй байна", str(form.errors))

    def test_save_stores_hashed_password(self):
        form = RegisterForm(data={
            "username": "hashtest",
            "password": "mypassword",
            "password2": "mypassword",
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("mypassword"))
        self.assertFalse(user.check_password("wrongpassword"))

    def test_save_creates_user_in_database(self):
        form = RegisterForm(data={
            "username": "dbtest",
            "password": "mypassword",
            "password2": "mypassword",
        })
        form.is_valid()
        form.save()
        self.assertTrue(User.objects.filter(username="dbtest").exists())


# ── VideoAdminForm ────────────────────────────────────────────────────────────

class VideoAdminFormTest(TestCase):
    def _form(self, youtube_id_value):
        return VideoAdminForm(data={
            "title": "Test Video",
            "youtube_id": youtube_id_value,
            "order": 1,
            "is_published": True,
        })

    def test_bare_11_char_id_is_valid(self):
        form = self._form("dQw4w9WgXcQ")
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["youtube_id"], "dQw4w9WgXcQ")

    def test_youtu_be_url_is_valid_and_extracts_id(self):
        form = self._form("https://youtu.be/dQw4w9WgXcQ")
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["youtube_id"], "dQw4w9WgXcQ")

    def test_watch_url_is_valid_and_extracts_id(self):
        form = self._form("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["youtube_id"], "dQw4w9WgXcQ")

    def test_embed_url_is_valid_and_extracts_id(self):
        form = self._form("https://www.youtube.com/embed/dQw4w9WgXcQ")
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["youtube_id"], "dQw4w9WgXcQ")

    def test_shorts_url_is_valid_and_extracts_id(self):
        form = self._form("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["youtube_id"], "dQw4w9WgXcQ")

    def test_invalid_url_raises_validation_error(self):
        form = self._form("not-a-youtube-url-at-all")
        self.assertFalse(form.is_valid())
        self.assertIn("youtube_id", form.errors)

    def test_empty_string_is_invalid(self):
        form = self._form("")
        self.assertFalse(form.is_valid())


# ── worksheets ?tab= query params ────────────────────────────────────────────

class WorksheetsTabParamTest(TestCase):
    """Legacy worksheet tab URLs continue to reach the right resources."""

    def test_tab_vocabulary_redirects_to_enhanced_library(self):
        response = self.client.get(reverse("worksheets"), {"tab": "vocabulary"})
        self.assertRedirects(response, reverse("terminology"))

    def test_tab_listening_redirects_to_listening_lab(self):
        response = self.client.get(reverse("worksheets"), {"tab": "listening"})
        self.assertRedirects(response, f'{reverse("terminology")}?mode=listening')

    def test_tab_reading_returns_200(self):
        response = self.client.get(reverse("worksheets"), {"tab": "reading"})
        self.assertEqual(response.status_code, 200)

    def test_unknown_tab_still_returns_200(self):
        response = self.client.get(reverse("worksheets"), {"tab": "nonexistent"})
        self.assertEqual(response.status_code, 200)


# ── Dashboard hero counts ─────────────────────────────────────────────────────

class DashboardHeroCountsTest(TestCase):
    def setUp(self):
        Video.objects.create(title="V1", youtube_id="aaaaaaaaaaa", order=99, is_published=True)
        Video.objects.create(title="V2", youtube_id="bbbbbbbbbbb", order=100, is_published=True)
        self.lesson = Lesson.objects.create(title="L1", order=99)

    def test_context_has_lessons_key(self):
        response = self.client.get(reverse("dashboard"))
        self.assertIn("lessons", response.context)

    def test_context_has_videos_key(self):
        response = self.client.get(reverse("dashboard"))
        self.assertIn("videos", response.context)

    def test_new_lesson_appears_in_context(self):
        response = self.client.get(reverse("dashboard"))
        lesson_pks = [l.pk for l in response.context["lessons"]]
        self.assertIn(self.lesson.pk, lesson_pks)

    def test_new_published_videos_appear_in_context(self):
        response = self.client.get(reverse("dashboard"))
        video_pks = [v.pk for v in response.context["videos"]]
        self.assertIn(
            Video.objects.get(youtube_id="aaaaaaaaaaa").pk, video_pks
        )


# ── submit_quiz malformed JSON ────────────────────────────────────────────────

class SubmitQuizEdgeCasesTest(TestCase):
    def test_malformed_json_returns_400(self):
        response = self.client.post(
            reverse("submit_quiz"),
            data="{ not valid json ::::",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    def test_score_defaults_to_zero_when_absent(self):
        response = self.client.post(
            reverse("submit_quiz"),
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(response.json()["score"], 0)
        self.assertEqual(response.json()["total"], 10)


# ── padlet all 4 prompt keys ──────────────────────────────────────────────────

class PadletAllPromptsTest(TestCase):
    def _post(self, prompt):
        return self.client.post(reverse("padlet"), {
            "author_name": "Naran",
            "prompt": prompt,
            "content": "Some content here",
        })

    def test_prompt_learned_is_valid(self):
        self._post("learned")
        self.assertEqual(WallPost.objects.filter(prompt="learned").count(), 1)

    def test_prompt_difficult_is_valid(self):
        self._post("difficult")
        self.assertEqual(WallPost.objects.filter(prompt="difficult").count(), 1)

    def test_prompt_question_is_valid(self):
        self._post("question")
        self.assertEqual(WallPost.objects.filter(prompt="question").count(), 1)

    def test_prompt_next_is_valid(self):
        self._post("next")
        self.assertEqual(WallPost.objects.filter(prompt="next").count(), 1)


# ── logbook dept FK saved ─────────────────────────────────────────────────────

class LogbookDeptFkTest(TestCase):
    def test_department_fk_set_when_valid_dept_id_submitted(self):
        dept = Department.objects.create(name="TestDept", order=999)
        self.client.post(reverse("logbook"), {
            "full_name": "Bat",
            "department": str(dept.pk),
        })
        entry = LogEntry.objects.get(full_name="Bat")
        self.assertEqual(entry.department_id, dept.pk)

    def test_department_fk_is_none_when_no_dept_submitted(self):
        self.client.post(reverse("logbook"), {
            "full_name": "Saran",
            "department": "",
        })
        entry = LogEntry.objects.get(full_name="Saran")
        self.assertIsNone(entry.department)
