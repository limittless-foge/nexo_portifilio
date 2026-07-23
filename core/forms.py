from django import forms
from .models import SiteSetting, Project

class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ['our_story_video', 'our_story_image', 'phone_number']
        widgets = {
            'our_story_video': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'video-upload',
                'accept': 'video/*'
            }),
            'our_story_image': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'image-upload',
                'accept': 'image/*'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
                'placeholder': '+251 968 929 373'
            }),
        }
