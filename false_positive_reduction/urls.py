# false_positive_reduction/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FalsePositiveDetectionViewSet,
    detect_false_positives,
    generate_whitelist_suggestions,
    start_learning_mode,
    get_learning_mode_status,
    export_whitelist_csv,
    download_whitelist_export,
    get_false_positive_dashboard,
)

router = DefaultRouter()
router.register(r'false-positives', FalsePositiveDetectionViewSet, basename='false-positive')

urlpatterns = [
    path('', include(router.urls)),
    
    # FR04-01: False Positive Detection
    path('detect/', detect_false_positives, name='detect-false-positives'),
    
    # FR04-02: Whitelist Suggestions
    path('suggestions/generate/', generate_whitelist_suggestions, name='generate-whitelist-suggestions'),
    
    # FR04-03: Learning Mode
    path('learning-mode/start/', start_learning_mode, name='start-learning-mode'),
    path('learning-mode/<int:learning_session_id>/status/', get_learning_mode_status, name='learning-mode-status'),
    
    # FR04-04: Whitelist Export
    path('whitelist/export/', export_whitelist_csv, name='export-whitelist-csv'),
    path('whitelist/download/<int:export_id>/', download_whitelist_export, name='download-whitelist-export'),
    
    # Dashboard
    path('dashboard/', get_false_positive_dashboard, name='false-positive-dashboard'),
]