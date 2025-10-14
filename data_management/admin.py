from django.contrib import admin
from .models import UploadedFile

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'file_type', 'uploaded_at')
    list_filter = ('file_type',)
    search_fields = ('file',)
