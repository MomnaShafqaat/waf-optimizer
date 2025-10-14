from rest_framework import viewsets
from .models import RuleRelationship
from .serializers import RuleRelationshipSerializer

class RuleRelationshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RuleRelationship.objects.all()
    serializer_class = RuleRelationshipSerializer
