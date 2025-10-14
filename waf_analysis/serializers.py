from rest_framework import serializers
from .models import RuleRelationship

class RuleRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleRelationship
        fields = ['id', 'rule_1', 'rule_2', 'relationship_type', 'details', 'created_at']
