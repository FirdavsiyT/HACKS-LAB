from django import forms
from pages.models import Challenge, Category
from .models import LessonSettings

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ['title', 'category', 'description', 'points', 'difficulty', 'flag', 'max_attempts', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none'}),
            'category': forms.Select(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none'}),
            'description': forms.Textarea(attrs={'class': 'w-full bg-[#13141b] border border-[#2c2f3b] rounded p-2 text-white focus:border-[#9fef00] outline-none', 'rows': 4}),
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