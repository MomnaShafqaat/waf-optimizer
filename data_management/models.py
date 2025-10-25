from django.db import models
import base64

class UploadedFile(models.Model):
    FILE_TYPES = [
        ('rules', 'WAF Rules File'),
        ('traffic', 'Traffic Data File'),
    ]

    # Keep the file field for compatibility with DRF file uploads
    file = models.FileField()
    
    # New fields to store file content in database
    file_name = models.CharField(max_length=255, blank=True)
    file_content = models.TextField(blank=True)  # Store file content as base64
    file_size = models.PositiveIntegerField(default=0)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Extract and store file content in database when saving
        if self.file and not self.file_content:
            # Read file content
            self.file.seek(0)
            file_data = self.file.read()
            self.file_size = len(file_data)
            self.file_name = self.file.name
            
            # Store content as base64 encoded string in database
            if isinstance(file_data, bytes):
                self.file_content = base64.b64encode(file_data).decode('utf-8')
            else:
                self.file_content = base64.b64encode(file_data.encode('utf-8')).decode('utf-8')
        
        super().save(*args, **kwargs)

    def get_file_content(self):
        """Get decoded file content from database"""
        if self.file_content:
            return base64.b64decode(self.file_content).decode('utf-8')
        return None

    def __str__(self):
        return f"{self.file_type} - {self.file_name}"