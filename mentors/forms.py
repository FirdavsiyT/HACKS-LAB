from django import forms
from pages.models import Challenge

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