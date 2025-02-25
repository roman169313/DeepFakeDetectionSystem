from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MediaFile(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('image', 'Image'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='uploads/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Analysis Results
    prediction = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Visualization paths
    ela_image = models.CharField(max_length=255, blank=True)
    jpeg_image = models.CharField(max_length=255, blank=True)
    noise_image = models.CharField(max_length=255, blank=True)
    waveform_image = models.CharField(max_length=255, blank=True)
    spectrogram_image = models.CharField(max_length=255, blank=True)
    frame_analysis_image = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'

    def __str__(self):
        return f"{self.get_media_type_display()} - {self.file.name}"