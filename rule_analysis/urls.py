from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RuleAnalysisSessionViewSet, analyze_rules

# Create router and register viewsets
router = DefaultRouter()
router.register(r'sessions', RuleAnalysisSessionViewSet, basename='session')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Direct analysis endpoint
    path('analyze/', analyze_rules, name='analyze-rules'),
]