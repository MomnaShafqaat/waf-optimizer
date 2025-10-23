from django.db import models

class UploadedFile(models.Model):
    FILE_TYPES = [
        ('rules', 'WAF Rules File'),
        ('traffic', 'Traffic Data File'),
    ]

    file = models.FileField()  # Removed upload_to='uploads/'
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} - {self.file.name}"