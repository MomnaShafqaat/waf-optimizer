from django.contrib import admin
from .models import ThresholdSuggestion

@admin.register(ThresholdSuggestion)
class ThresholdSuggestionAdmin(admin.ModelAdmin):
    list_display = ('value', 'approved', 'created_at')
    list_filter = ('approved',)
