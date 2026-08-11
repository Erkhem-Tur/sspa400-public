from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import (
    Assignment,
    Course,
    CourseCategory,
    CourseModule,
    CourseUnit,
    Department,
    DiscussionPost,
    QuizQuestion,
    Submission,
    UserProgress,
    RANK_CHOICES,
    PROMPT_CHOICES,
)


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(label='Email')
    full_name = forms.CharField(max_length=200, label='Full name')
    role = forms.ChoiceField(choices=UserProgress.Role.choices, label='Account type')
    password = forms.CharField(widget=forms.PasswordInput, label="Нууц үг")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Нууц үг давтах")

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {'username': 'Хэрэглэгчийн нэр'}

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Энэ нэр бүртгэлтэй байна.")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError("Нууц үг таарахгүй байна.")
        password = cleaned.get('password')
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error('password', error)
        return cleaned

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account already uses this email address.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['full_name'].strip()
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label="Хэлтэс / Тасаг",
        empty_label="-- Хэлтэсээ сонгоно уу --"
    )
    rank = forms.ChoiceField(choices=RANK_CHOICES, label="Цол")
    full_name = forms.CharField(max_length=200, label="Бүтэн нэр")

    class Meta:
        model = UserProgress
        fields = ['full_name', 'rank', 'department']


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Хэрэглэгчийн нэр")
    password = forms.CharField(widget=forms.PasswordInput, label="Нууц үг")


class LogbookEntryForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        strip=True,
        error_messages={
            'required': 'Нэрээ оруулна уу.',
            'max_length': 'Нэр 200 тэмдэгтээс урт байж болохгүй.',
        },
    )
    rank = forms.ChoiceField(
        choices=RANK_CHOICES,
        required=False,
        error_messages={'invalid_choice': 'Цолоо жагсаалтаас сонгоно уу.'},
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        error_messages={'invalid_choice': 'Хэлтсээ жагсаалтаас сонгоно уу.'},
    )
    tasag = forms.CharField(
        max_length=200,
        required=False,
        strip=True,
        error_messages={'max_length': 'Тасаг 200 тэмдэгтээс урт байж болохгүй.'},
    )
    tl_english = forms.CharField(
        max_length=200,
        required=False,
        strip=True,
        error_messages={'max_length': 'Англи тэмдэглэл 200 тэмдэгтээс урт байж болохгүй.'},
    )
    tl_mongolian = forms.CharField(
        max_length=200,
        required=False,
        strip=True,
        error_messages={'max_length': 'Монгол тэмдэглэл 200 тэмдэгтээс урт байж болохгүй.'},
    )
    note = forms.CharField(
        max_length=1000,
        required=False,
        strip=True,
        error_messages={'max_length': 'Нийт тэмдэглэл 1000 тэмдэгтээс урт байж болохгүй.'},
    )

    def combined_note(self):
        parts = []
        tl_english = self.cleaned_data.get('tl_english')
        tl_mongolian = self.cleaned_data.get('tl_mongolian')
        note = self.cleaned_data.get('note')
        if tl_english:
            parts.append(f'[EN] {tl_english}')
        if tl_mongolian:
            parts.append(f'[MN] {tl_mongolian}')
        if note:
            parts.append(note)
        return ' | '.join(parts)


class WallPostForm(forms.Form):
    author_name = forms.CharField(
        max_length=100,
        strip=True,
        error_messages={
            'required': 'Нэрээ оруулна уу.',
            'max_length': 'Нэр 100 тэмдэгтээс урт байж болохгүй.',
        },
    )
    prompt = forms.ChoiceField(
        choices=PROMPT_CHOICES,
        error_messages={
            'required': 'Асуулт сонгоно уу.',
            'invalid_choice': 'Асуулт сонгоно уу.',
        },
    )
    content = forms.CharField(
        max_length=300,
        strip=True,
        error_messages={
            'required': 'Хариултаа бичнэ үү.',
            'max_length': 'Хариулт 300 тэмдэгтээс урт байж болохгүй.',
        },
    )


class StyledModelForm(forms.ModelForm):
    """Apply the existing Bootstrap form treatment consistently."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class CourseForm(StyledModelForm):
    class Meta:
        model = Course
        fields = [
            'title',
            'short_description',
            'description',
            'learning_outcomes',
            'category',
            'level',
            'estimated_minutes',
            'status',
            'is_featured',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'learning_outcomes': forms.Textarea(attrs={'rows': 5, 'placeholder': 'One outcome per line'}),
        }


class CourseCategoryForm(StyledModelForm):
    class Meta:
        model = CourseCategory
        fields = ['name', 'description', 'order', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class CourseModuleForm(StyledModelForm):
    class Meta:
        model = CourseModule
        fields = ['title', 'summary', 'order']
        widgets = {'summary': forms.Textarea(attrs={'rows': 3})}


class CourseUnitForm(StyledModelForm):
    class Meta:
        model = CourseUnit
        fields = [
            'title',
            'summary',
            'kind',
            'body',
            'duration_minutes',
            'video_url',
            'audio_script',
            'resource_url',
            'meeting_url',
            'pass_percent',
            'is_required',
            'is_published',
            'order',
        ]
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
            'audio_script': forms.Textarea(attrs={'rows': 6}),
        }


class QuizQuestionForm(StyledModelForm):
    options_text = forms.CharField(
        required=False,
        label='Answer choices',
        help_text='Enter one choice per line. Essay questions do not need choices.',
        widget=forms.Textarea(attrs={'rows': 5}),
    )

    class Meta:
        model = QuizQuestion
        fields = ['prompt', 'kind', 'options_text', 'correct_answer', 'explanation', 'points', 'order']
        widgets = {
            'prompt': forms.Textarea(attrs={'rows': 4}),
            'explanation': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['options_text'].initial = '\n'.join(self.instance.options or [])

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get('kind')
        options = [line.strip() for line in cleaned.get('options_text', '').splitlines() if line.strip()]
        correct = cleaned.get('correct_answer', '').strip()
        if kind == QuizQuestion.Kind.MULTIPLE_CHOICE:
            if len(options) < 2:
                self.add_error('options_text', 'Multiple-choice questions need at least two choices.')
            if correct and correct.casefold() not in {item.casefold() for item in options}:
                self.add_error('correct_answer', 'The correct answer must match one of the choices.')
            if not correct:
                self.add_error('correct_answer', 'Enter the correct answer.')
        elif kind == QuizQuestion.Kind.TRUE_FALSE:
            options = ['True', 'False']
            if correct.casefold() not in {'true', 'false'}:
                self.add_error('correct_answer', 'Enter True or False.')
        else:
            options = []
        cleaned['parsed_options'] = options
        return cleaned

    def save(self, commit=True):
        question = super().save(commit=False)
        question.options = self.cleaned_data.get('parsed_options', [])
        if commit:
            question.save()
        return question


class AssignmentForm(StyledModelForm):
    class Meta:
        model = Assignment
        fields = ['instructions', 'due_at', 'max_points', 'rubric', 'allow_resubmission']
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 8}),
            'due_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'rubric': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '[{"criterion": "Clarity", "points": 20}]',
            }),
        }


class DiscussionPostForm(StyledModelForm):
    class Meta:
        model = DiscussionPost
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ask a question or share an answer...'})}


class SubmissionForm(StyledModelForm):
    class Meta:
        model = Submission
        fields = ['response_text', 'attachment_url']
        widgets = {'response_text': forms.Textarea(attrs={'rows': 8})}

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('response_text', '').strip() and not cleaned.get('attachment_url'):
            raise forms.ValidationError('Write a response or provide a file link.')
        return cleaned


class SubmissionGradeForm(StyledModelForm):
    class Meta:
        model = Submission
        fields = ['grade', 'status', 'feedback']
        widgets = {'feedback': forms.Textarea(attrs={'rows': 5})}

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade is not None and grade < 0:
            raise forms.ValidationError('Grade cannot be negative.')
        if grade is not None and grade > self.instance.assignment.max_points:
            raise forms.ValidationError(
                f'Grade cannot exceed {self.instance.assignment.max_points} points.'
            )
        return grade
