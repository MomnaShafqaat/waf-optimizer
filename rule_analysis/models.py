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

        


        #momo

class RulePerformance(models.Model):
    """
    FR05-01: Tracks how often each rule is triggered
    LEARNING: This is like a "hit counter" for each rule
    """
    rule_id = models.CharField(max_length=50, unique=True)
    hit_count = models.IntegerField(default=0)  # FR03-01
    last_triggered = models.DateTimeField(null=True, blank=True)
    average_evaluation_time = models.FloatField(default=0.0)  # FR03-02
    false_positive_count = models.IntegerField(default=0)  # FR04-01
    
    # FR03-03: Effectiveness metrics
    effectiveness_ratio = models.FloatField(default=0.0)  # hits vs false positives
    
    class Meta:
        db_table = 'rule_performance'

class RuleRankingSession(models.Model):
    """
    FR05-02: Stores different ranking proposals for comparison
    LEARNING: Like saving different versions of rule order
    """
    name = models.CharField(max_length=255)
    original_rules_order = models.JSONField()  # Current order
    optimized_rules_order = models.JSONField()  # Proposed order
    performance_improvement = models.FloatField(default=0.0)  # Expected gain
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FR05-03: Approval workflow
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('applied', 'Applied'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    approved_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        db_table = 'rule_ranking_sessions'

from django.db import models

class ThresholdSuggestion(models.Model):
    value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Threshold: {self.value} (Approved: {self.approved})"
