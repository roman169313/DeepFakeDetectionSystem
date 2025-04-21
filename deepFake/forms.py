from django import forms
from .models import MediaFile
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

# Custom Login Form
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Password'
    }))

# Custom Register Form
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Email'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Username'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Confirm Password'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'placeholder': 'Email'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
                'placeholder': 'Password'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

from django import forms
from django.core.exceptions import ValidationError
from .models import MediaFile

class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['file']

    file = forms.FileField(
    label='Upload Media File',
    widget=forms.ClearableFileInput(attrs={
        'name': 'image_file',
        'accept': 'image/*,video/*,audio/*'
    })
)


    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError("No file selected.")

        allowed_types = [
            'image/jpeg',
            'image/png',
            'image/jpg',
            'video/mp4',
            'video/webm',
            'audio/mpeg',
            'audio/mp3',
            'audio/wav'
        ]

        if file.content_type not in allowed_types:
            raise ValidationError("Unsupported file format. Only images (JPEG/PNG), videos (MP4/Webm), and audio (MP3/WAV) are allowed.")

        return file

class MediaImageForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['file']

    # Override the 'file' field to change the input name to 'image_file'
    file = forms.FileField(
    label='Upload Media File',
    widget=forms.ClearableFileInput(attrs={
        'name': 'image_file',
        'accept': 'image/*'
    })
)
class MediaVideoForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['file']

    # Override the 'file' field to change the input name to 'image_file'
    file = forms.FileField(
    label='Upload Media File',
    widget=forms.ClearableFileInput(attrs={
        'name': 'image_file',
        'accept': 'video/*'
    })
)
class MediaAudioForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['file']

    # Override the 'file' field to change the input name to 'image_file'
    file = forms.FileField(
    label='Upload Media File',
    widget=forms.ClearableFileInput(attrs={
        'name': 'image_file',
        'accept': 'audio/*'
    })
)