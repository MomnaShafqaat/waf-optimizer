from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RuleRelationshipViewSet

router = DefaultRouter()
router.register(r'rule_relationships', RuleRelationshipViewSet, basename='rule_relationship')

urlpatterns = [
    path('', include(router.urls)),
 
]
