# false_positive_reduction/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    FalsePositiveDetectionViewSet,
    detect_false_positives,
    render_whitelist_suggestions,
    render_learning_mode,
    get_learning_mode_status,
    export_whitelist_csv,
    render_whitelist_export,
    get_false_positive_dashboard,
)

router = DefaultRouter()
router.register(r'false-positives', FalsePositiveDetectionViewSet, basename='false-positive')
urlpatterns = [
    # FR04-01: False Positive Detection
    path('false-positives/detect/', detect_false_positives, name='detect-false-positives'),

    # Router must come *after* all custom paths
    path('', include(router.urls)),

    # FR04-02: Whitelist Suggestions
    path('false-positives/suggestions/generate/', render_whitelist_suggestions, name='generate-whitelist-suggestions'),

    # FR04-03: Learning Mode
    path('learning-mode/start/', render_learning_mode, name='start-learning-mode'),
    path('learning-mode/<int:learning_session_id>/status/', get_learning_mode_status, name='learning-mode-status'),

    # FR04-04: Whitelist Export
    path('whitelist/export/', export_whitelist_csv, name='export-whitelist-csv'),
    path('whitelist/download/<int:export_id>/', render_whitelist_export, name='download-whitelist-export'),

    # Dashboard
    path('dashboard/', get_false_positive_dashboard, name='false-positive-dashboard'),
]
