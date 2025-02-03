from django import forms
from .models import MediaFile
from django.contrib.auth.models import User

class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
        'placeholder': 'Password'
    }))

class UserRegistrationForm(forms.ModelForm):
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
        'placeholder': 'Confirm Password'
    }), label="Confirm Password")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
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

class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['file', 'media_type']

    # Override the 'file' field to change the input name to 'image_file'
    file = forms.FileField(
        label='Upload Image',
        widget=forms.ClearableFileInput(attrs={'name': 'image_file'})
    )
