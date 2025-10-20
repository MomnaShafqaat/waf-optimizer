from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RuleAnalysisSessionViewSet, analyze_rules
from .ranking_views import generate_rule_ranking, get_ranking_session, get_ranking_comparison, approve_ranking_session

# Create router and register viewsets
router = DefaultRouter()
router.register(r'sessions', RuleAnalysisSessionViewSet, basename='session')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Direct analysis endpoint
    path('analyze/', analyze_rules, name='analyze-rules'),
    
    # Rule ranking endpoints
    path('ranking/generate/', generate_rule_ranking, name='generate-ranking'),
    path('ranking/session/<int:session_id>/', get_ranking_session, name='get-ranking-session'),
    path('ranking/comparison/<int:session_id>/', get_ranking_comparison, name='get-ranking-comparison'),
    path('ranking/approve/<int:session_id>/', approve_ranking_session, name='approve-ranking'),
]