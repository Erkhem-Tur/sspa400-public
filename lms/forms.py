from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Department, UserProgress, RANK_CHOICES


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Нууц үг")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Нууц үг давтах")

    class Meta:
        model = User
        fields = ['username']
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
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
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
