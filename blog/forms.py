from django import forms
from django.forms.models import BaseInlineFormSet

from .models import PostImage


class PostImageForm(forms.ModelForm):
    is_main = forms.BooleanField(required=False, label='Головне')

    class Meta:
        model = PostImage
        fields = ('image', 'is_main')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['is_main'] = (
                self.instance.image.name == self.instance.post.image.name
            )


class PostImageFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        selected = [
            form for form in self.forms
            if form.cleaned_data.get('is_main') and not form.cleaned_data.get('DELETE')
        ]
        if len(selected) > 1:
            raise forms.ValidationError('Виберіть лише одне головне зображення.')

    def save(self, commit=True):
        images = super().save(commit=commit)
        if commit:
            selected = next((
                form.instance.image for form in self.forms
                if form.cleaned_data.get('is_main') and not form.cleaned_data.get('DELETE')
            ), '')
            self.instance.image = selected
            self.instance.save(update_fields=['image'])
        return images
