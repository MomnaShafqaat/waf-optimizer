from rest_framework import serializers
from .models import FalsePositiveDetection, WhitelistSuggestion, LearningModeSession, WhitelistExport


class FalsePositiveDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FalsePositiveDetection
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WhitelistSuggestionSerializer(serializers.ModelSerializer):
    false_positive_rule_id = serializers.CharField(source='false_positive.rule_id', read_only=True)

    class Meta:
        model = WhitelistSuggestion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class LearningModeSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningModeSession
        fields = '__all__'
        read_only_fields = ['started_at', 'completed_at']


class WhitelistExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhitelistExport
        fields = '__all__'
        read_only_fields = ['created_at', 'completed_at']


