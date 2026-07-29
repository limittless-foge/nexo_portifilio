from django import forms
from .models import SiteSetting, Project

class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ['our_story_video', 'our_story_image', 'education_external_url']
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
            'education_external_url': forms.TextInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
                'placeholder': 'https://example.com'
            }),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title',
            'category_fk',
            'image_url',
            'image',
            'video',
            'description',
            'technology_stack',
            'case_study_url',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
                'placeholder': 'e.g. Brand Campaign Launch Reel'
            }),
            'category_fk': forms.Select(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
                'placeholder': 'Optional poster image URL'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full text-slate-200',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'w-full text-slate-200',
                'accept': 'video/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
                'rows': 4,
                'placeholder': 'Short project summary and results'
            }),
            'technology_stack': forms.TextInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
                'placeholder': 'e.g. Django, React, Redis'
            }),
            'case_study_url': forms.URLInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-white text-sm focus:border-accent/50 transition outline-none',
                'placeholder': 'Optional case study or deployment link'
            }),
        }
