from django.db import models
from data_management.models import UploadedFile

class RuleAnalysisSession(models.Model):
    ANALYSIS_TYPES = [
        ('SHD', 'Shadowing'),
        ('GEN', 'Generalization'),
        ('RXD', 'Redundancy X'),
        ('RYD', 'Redundancy Y'),
        ('COR', 'Correlation'),
    ]
    
    name = models.CharField(max_length=255)
    rules_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='rules_analyses')
    traffic_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='traffic_analyses')
    analysis_types = models.JSONField()  # List of analysis types to perform
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RuleRelationship(models.Model):
    RELATIONSHIP_TYPES = [
        ('SHD', 'Shadowing - Rule A shadows Rule B'),
        ('GEN', 'Generalization - Rule A is more general than Rule B'),
        ('RXD', 'Redundancy X - Rules trigger on identical patterns'),
        ('RYD', 'Redundancy Y - Rules are functionally equivalent'),
        ('COR', 'Correlation - Rules frequently trigger together'),
    ]
    
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='relationships')
    relationship_type = models.CharField(max_length=3, choices=RELATIONSHIP_TYPES)
    rule_a = models.CharField(max_length=50)  # Rule ID from rules file
    rule_b = models.CharField(max_length=50)  # Rule ID from rules file
    confidence = models.FloatField()  # 0.0 to 1.0
    evidence_count = models.IntegerField(default=0)
    conflicting_fields = models.JSONField()  # Fields causing the issue
    description = models.TextField()
    
    class Meta:
        unique_together = ['session', 'relationship_type', 'rule_a', 'rule_b']