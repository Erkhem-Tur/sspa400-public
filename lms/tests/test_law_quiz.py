from django.core.management import call_command
from django.test import TestCase

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
