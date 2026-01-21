from django import forms
from pages.models import Challenge, Category
from .models import LessonSettings, LessonTemplate
from django_summernote.widgets import SummernoteWidget

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ['title', 'category', 'description', 'points', 'difficulty', 'flag', 'max_attempts', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none'}),
            'category': forms.Select(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none'}),
            'description': SummernoteWidget(attrs={'summernote': {'width': '100%', 'height': '400px'}}),
            'points': forms.NumberInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none'}),
            'difficulty': forms.Select(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none'}),
            'flag': forms.TextInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none font-mono'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 bg-[#13141b] border border-[#2c2f3b] rounded focus:ring-[#9fef00]'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none', 'placeholder': 'e.g. Web Security'}),
        }

class TimerSettingsForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(
        required=False,
        min_value=1,
        label="Duration (minutes)",
        widget=forms.NumberInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none', 'placeholder': '45'})
    )
    delay_minutes = forms.IntegerField(
        required=False,
        min_value=0,
        label="Overtime Delay (minutes)",
        widget=forms.NumberInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none', 'placeholder': '10'})
    )

    class Meta:
        model = LessonSettings
        fields = []

class LessonTemplateForm(forms.ModelForm):
    challenges = forms.ModelMultipleChoiceField(
        queryset=Challenge.objects.all().order_by('category__name', 'points'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'accent-[#9fef00]'}),
        required=False,
        label="Select Challenges"
    )

    class Meta:
        model = LessonTemplate
        fields = ['title', 'description', 'challenges']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full bg-[#1a1c23] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] focus:outline-none'}),
            'description': forms.Textarea(attrs={'class': 'w-full bg-[#1a1c23] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] focus:outline-none', 'rows': 3}),
        }