from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from lms.models import Course, QuizQuestion


class LawQuizSeedTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed')

    def test_law_course_is_published_and_sectioned(self):
        course = Course.objects.get(slug='law-quiz-448')
        self.assertTrue(course.is_published)
        self.assertEqual(course.modules.count(), 11)
        self.assertGreater(course.modules.first().units.count(), 1)

    def test_only_highlighted_source_answers_are_scored(self):
        questions = QuizQuestion.objects.filter(unit__module__course__slug='law-quiz-448')
        self.assertEqual(questions.count(), 448)
        self.assertFalse(questions.filter(correct_answer='').exists())
        self.assertTrue(all(question.correct_answer in question.options for question in questions))
        self.assertTrue(all('Legalinfo.mn:' in question.explanation for question in questions))

    def test_public_quiz_requires_no_login(self):
        response = self.client.get(reverse('public_law_quiz'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Нэвтрэх шаардлагагүй')

    def test_public_course_detail_links_directly_to_quiz(self):
        response = self.client.get(reverse('course_detail', args=['law-quiz-448']))
        self.assertContains(response, reverse('public_law_quiz'))
        self.assertContains(response, 'Нэвтрэхгүйгээр шууд эхлэх')
