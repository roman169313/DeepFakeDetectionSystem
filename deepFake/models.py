# from django.db import models
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class MediaFile(models.Model):
#     MEDIA_TYPE_CHOICES = [
#         ('audio', 'Audio'),
#         ('video', 'Video'),
#         ('image', 'Image'),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_files')
#     file = models.FileField(upload_to='uploads/')
#     media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
#     uploaded_at = models.DateTimeField(auto_now_add=True)
    
#     # Analysis Results
#     prediction = models.CharField(max_length=100, blank=True, null=True)
#     confidence = models.FloatField(blank=True, null=True)
#     metadata = models.JSONField(default=dict, blank=True)
    
#     # Visualization paths
#     ela_image = models.CharField(max_length=255, blank=True)
#     jpeg_image = models.CharField(max_length=255, blank=True)
#     noise_image = models.CharField(max_length=255, blank=True)
#     waveform_image = models.CharField(max_length=255, blank=True)
#     spectrogram_image = models.CharField(max_length=255, blank=True)
#     frame_analysis_image = models.CharField(max_length=255, blank=True)

#     class Meta:
#         ordering = ['-uploaded_at']
#         verbose_name = 'Media File'
#         verbose_name_plural = 'Media Files'

#     def __str__(self):
#         return f"{self.get_media_type_display()} - {self.file.name}"

# models.py
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

def user_upload_path(instance, filename):
    """Generate a unique upload path for user files."""
    ext = filename.split('.')[-1]
    unique_id = uuid.uuid4()
    return f"uploads/user_{instance.user.id}/{instance.media_type}s/{unique_id}.{ext}"

def processed_image_path(instance, filename, folder):
    """Generate a unique path for processed images (e.g., ELA, spectrogram)."""
    unique_id = uuid.uuid4()
    return f"processed/{folder}/user_{instance.user.id}/{unique_id}_{filename}"

class MediaFile(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('image', 'Image'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to=user_upload_path)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Analysis Results
    prediction = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Visualization files
    ela_image = models.ImageField(upload_to=lambda instance, filename: processed_image_path(instance, filename, 'ela'), blank=True, null=True)
    jpeg_image = models.ImageField(upload_to=lambda instance, filename: processed_image_path(instance, filename, 'jpeg'), blank=True, null=True)
    noise_image = models.ImageField(upload_to=lambda instance, filename: processed_image_path(instance, filename, 'noise'), blank=True, null=True)
    waveform_image = models.ImageField(upload_to=lambda instance, filename: processed_image_path(instance, filename, 'waveforms'), blank=True, null=True)
    spectrogram_image = models.ImageField(upload_to=lambda instance, filename: processed_image_path(instance, filename, 'spectrograms'), blank=True, null=True)
    frame_analysis_image = models.ImageField(upload_to=lambda instance, filename: processed_image_path(instance, filename, 'frame_analysis'), blank=True, null=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'

    def __str__(self):
        return f"{self.get_media_type_display()} - {self.file.name}"