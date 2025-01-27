from django.db import models

class MediaFile(models.Model):
    MEDIA_TYPES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('image', 'Image'),
    ]
    file = models.FileField(upload_to='uploads/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} - {self.file.name}"
