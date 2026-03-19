from django import forms
from .models import StudyRecord, Course, Goal

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. IT, Mathematics, Physics',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description (optional)',
            }),
        }

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'target_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Complete all lab exercises',
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class StudyRecordForm(forms.ModelForm):
    class Meta:
        model = StudyRecord
        fields = ['title', 'course', 'study_type', 'duration_mins', 'study_date', 'reflection_note']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Django ORM revision',
            }),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'study_type': forms.Select(attrs={'class': 'form-select'}),
            'duration_mins': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1440,
            }),
            'study_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'reflection_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'id': 'id_reflection_note',
                'placeholder': 'What did you learn? Any questions? (optional)',
            }),
        }
        labels = {
            'duration_mins': 'Duration (minutes)',
            'study_date': 'Study Date',
            'reflection_note': 'Reflection Note',
            'course': 'Course (optional)',
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['course'].queryset = Course.objects.filter(user=user)
        self.fields['course'].empty_label = '— No course —'

class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'username',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
    )

    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data
