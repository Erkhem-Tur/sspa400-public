import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from lms.models import (
    Assignment,
    Course,
    CourseCategory,
    CourseModule,
    CourseUnit,
    Department,
    Lesson,
    QuizQuestion,
)


class Command(BaseCommand):
    help = 'Seed required departments and a free starter LMS course.'

    def handle(self, *args, **kwargs):
        self._seed_departments_and_legacy_lesson()
        self._seed_admin_from_environment()
        self._seed_starter_course()
        self.stdout.write(self.style.SUCCESS('Seed completed successfully'))

    def _seed_departments_and_legacy_lesson(self):
        departments = [
            (1, 'Хамгаалалтын 6-р хэлтэс'),
            (2, 'Төрийн Ордны хамгаалалтын хэлтэс'),
        ]
        for order, name in departments:
            Department.objects.get_or_create(name=name, defaults={'order': order})

        Lesson.objects.get_or_create(id=1, defaults={
            'title': 'SSPA Operation English - 400 questions',
            'description': 'Vocabulary, Grammar, Flashcards, Listening',
            'order': 1,
        })

    def _seed_admin_from_environment(self):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
        if not username or not password:
            return
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        changed = created
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            changed = True
        if email and user.email != email:
            user.email = email
            changed = True
        if created or not user.check_password(password):
            user.set_password(password)
            changed = True
        if changed:
            user.save()

    def _seed_starter_course(self):
        conversation, _ = CourseCategory.objects.get_or_create(
            slug='conversation-english',
            defaults={
                'name': 'Conversation English',
                'description': 'Speaking and listening for daily communication.',
                'order': 0,
            },
        )
        CourseCategory.objects.get_or_create(
            slug='operational-english',
            defaults={
                'name': 'Operational English',
                'description': 'Clear English for protective and workplace duties.',
                'order': 1,
            },
        )
        CourseCategory.objects.get_or_create(
            slug='grammar-vocabulary',
            defaults={
                'name': 'Grammar and Vocabulary',
                'description': 'Short, practical language review.',
                'order': 2,
            },
        )

        course, created = Course.objects.get_or_create(
            slug='daily-conversation-restart',
            defaults={
                'title': 'Daily Conversation Restart',
                'short_description': 'A low-pressure speaking and listening restart for learners returning after a break.',
                'description': (
                    'Rebuild useful English through short conversations. Each lesson follows a simple cycle: '
                    'understand the situation, listen for key details, repeat useful phrases, and speak with a partner. '
                    'You do not need to remember everything before you begin.'
                ),
                'learning_outcomes': (
                    'Greet someone and restart a conversation naturally\n'
                    'Ask for repetition or clarification without stopping the conversation\n'
                    'Confirm names, numbers, times, and locations\n'
                    'Give a short, clear workplace situation report'
                ),
                'category': conversation,
                'level': Course.Level.MIXED,
                'status': Course.Status.PUBLISHED,
                'estimated_minutes': 95,
                'is_featured': True,
            },
        )
        if not created or course.modules.exists():
            return

        restart = CourseModule.objects.create(
            course=course,
            title='Restart and remember',
            summary='Recover familiar English before adding anything difficult.',
            order=0,
        )
        CourseUnit.objects.create(
            module=restart,
            title='A calm restart',
            summary='Use what you remember and rebuild confidence one short response at a time.',
            kind=CourseUnit.Kind.TEXT,
            order=0,
            duration_minutes=8,
            body=(
                'Your English is not gone. It may only be slow to return.\n\n'
                'Use this four-step speaking routine:\n'
                '1. Listen to the whole message.\n'
                '2. Catch one useful word or detail.\n'
                '3. Give a short answer first.\n'
                '4. Add one more detail.\n\n'
                'Example:\n'
                'Question: How was your weekend?\n'
                'Short answer: It was good.\n'
                'Add one detail: I visited my family.'
            ),
        )
        CourseUnit.objects.create(
            module=restart,
            title='Meeting again after a break',
            summary='Listen for the greeting, reason, and next question.',
            kind=CourseUnit.Kind.LISTENING,
            order=1,
            duration_minutes=10,
            audio_script=(
                'A: Good morning, Bat. It is good to see you again. How have you been? '
                'B: I have been well, thank you. I was away for training. How about you? '
                'A: I am doing well. Are you working at the main office today? '
                'B: Yes. I start at nine o clock. What time is the briefing? '
                'A: The briefing is at ten thirty in Meeting Room Two. '
                'B: Ten thirty, Meeting Room Two. Understood. See you there.'
            ),
            body='After listening, say the conversation again with a partner. Change the time and location.',
        )
        diagnostic = CourseUnit.objects.create(
            module=restart,
            title='Quick restart check',
            summary='Check the details you heard and the phrases you can use.',
            kind=CourseUnit.Kind.QUIZ,
            order=2,
            duration_minutes=7,
            pass_percent=70,
        )
        self._question(diagnostic, 0, 'Why was Bat away?', ['For training', 'For vacation', 'For a meeting'], 'For training', 'Listen for the reason after "I was away".')
        self._question(diagnostic, 1, 'What time is the briefing?', ['9:00', '10:30', '12:30'], '10:30', 'The speaker confirms ten thirty.')
        self._question(diagnostic, 2, '“Could you say that again?” is a polite clarification phrase.', ['True', 'False'], 'True', kind=QuizQuestion.Kind.TRUE_FALSE)

        daily = CourseModule.objects.create(
            course=course,
            title='Keep a daily conversation moving',
            summary='Use short follow-up questions and clear confirmation.',
            order=1,
        )
        CourseUnit.objects.create(
            module=daily,
            title='The three-part conversation pattern',
            kind=CourseUnit.Kind.TEXT,
            order=0,
            duration_minutes=10,
            body=(
                'Most daily conversations become easier with three moves:\n\n'
                '1. Answer: “I am working at the north gate today.”\n'
                '2. Add a detail: “My shift finishes at six.”\n'
                '3. Ask back: “What about you?”\n\n'
                'Useful follow-up questions:\n'
                '- What happened next?\n'
                '- What time does it start?\n'
                '- Where should we meet?\n'
                '- Who is responsible?\n'
                '- Could you explain that again?'
            ),
        )
        CourseUnit.objects.create(
            module=daily,
            title='Lunch and shift plans',
            summary='Listen for preferences, time, and place.',
            kind=CourseUnit.Kind.LISTENING,
            order=1,
            duration_minutes=10,
            audio_script=(
                'A: Are you free for lunch today? '
                'B: Yes, but I only have thirty minutes. '
                'A: No problem. Would you like soup or dumplings? '
                'B: Soup, please. Where should we meet? '
                'A: Let us meet near the front entrance at twelve fifteen. '
                'B: The front entrance at twelve fifteen. I will be there.'
            ),
            body='Repeat the conversation. Then change the food, meeting place, and time.',
        )

        clear = CourseModule.objects.create(
            course=course,
            title='Clear workplace English',
            summary='Confirm important details and give a concise update.',
            order=2,
        )
        CourseUnit.objects.create(
            module=clear,
            title='Clarify and confirm',
            kind=CourseUnit.Kind.TEXT,
            order=0,
            duration_minutes=10,
            body=(
                'Use these phrases when a detail is not clear:\n\n'
                '- Could you repeat the time, please?\n'
                '- Did you say Gate Three?\n'
                '- Could you speak a little more slowly?\n'
                '- Let me confirm: two visitors at fourteen hundred.\n'
                '- I understand the location, but I need the name again.\n\n'
                'Confirmation is professional. It prevents mistakes.'
            ),
        )
        CourseUnit.objects.create(
            module=clear,
            title='Visitor at the gate',
            summary='Listen for identity, purpose, destination, and time.',
            kind=CourseUnit.Kind.LISTENING,
            order=1,
            duration_minutes=12,
            audio_script=(
                'Officer: Good afternoon. May I see your identification, please? '
                'Visitor: Of course. My name is Daniel Park. I have a meeting with Ms. Bold. '
                'Officer: What time is your meeting? '
                'Visitor: It is at fourteen thirty. '
                'Officer: Let me confirm: Daniel Park, meeting with Ms. Bold at fourteen thirty. '
                'Visitor: That is correct. '
                'Officer: Please wait here while I confirm your appointment.'
            ),
            body='Practice the officer role. Change the visitor name, meeting person, and time.',
        )
        assignment_unit = CourseUnit.objects.create(
            module=clear,
            title='One-minute situation report',
            summary='Prepare a short spoken report using four essential details.',
            kind=CourseUnit.Kind.ASSIGNMENT,
            order=2,
            duration_minutes=15,
            is_required=False,
            body='Write the report first, then say it aloud without reading every word.',
        )
        Assignment.objects.create(
            unit=assignment_unit,
            instructions=(
                'Write a short situation report with: who, what happened, where, and what action you took. '
                'Keep it between 40 and 80 words. Then practice saying it in under one minute.'
            ),
            max_points=20,
            rubric=[
                {'criterion': 'All four details are clear', 'points': 8},
                {'criterion': 'Message is concise and organized', 'points': 6},
                {'criterion': 'Useful operational vocabulary', 'points': 6},
            ],
        )

        finish = CourseModule.objects.create(
            course=course,
            title='Final speaking readiness check',
            summary='Confirm the phrases and listening habits you can now use.',
            order=3,
        )
        final = CourseUnit.objects.create(
            module=finish,
            title='Final check',
            kind=CourseUnit.Kind.QUIZ,
            order=0,
            duration_minutes=10,
            pass_percent=70,
        )
        self._question(final, 0, 'Which response best confirms a time and place?', ['Okay.', 'Ten thirty, Meeting Room Two. Understood.', 'Maybe later.'], 'Ten thirty, Meeting Room Two. Understood.')
        self._question(final, 1, 'Which question asks for a location?', ['Where should we meet?', 'Who is responsible?', 'What happened next?'], 'Where should we meet?')
        self._question(final, 2, 'Asking a speaker to repeat an important detail is unprofessional.', ['True', 'False'], 'False', 'Clarification prevents mistakes and is professional.', QuizQuestion.Kind.TRUE_FALSE)
        self._question(final, 3, 'A clear situation report should include who, what, where, and action taken.', ['True', 'False'], 'True', kind=QuizQuestion.Kind.TRUE_FALSE)

    @staticmethod
    def _question(unit, order, prompt, options, correct, explanation='', kind=QuizQuestion.Kind.MULTIPLE_CHOICE):
        QuizQuestion.objects.create(
            unit=unit,
            order=order,
            prompt=prompt,
            kind=kind,
            options=options,
            correct_answer=correct,
            explanation=explanation,
            points=1,
        )
