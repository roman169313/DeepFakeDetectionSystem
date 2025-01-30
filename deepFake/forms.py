from django import forms
from .models import MediaFile

class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['file', 'media_type']

    # Override the 'file' field to change the input name to 'image_file'
    file = forms.FileField(
        label='Upload Image',
        widget=forms.ClearableFileInput(attrs={'name': 'image_file'})
    )
