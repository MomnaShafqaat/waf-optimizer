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
    
    # NEW: Store complete analysis results including AI suggestions
    results = models.JSONField(null=True, blank=True, help_text="Complete analysis results with AI suggestions")
    
    # NEW: AI-specific fields
    ai_available = models.BooleanField(default=False, help_text="Whether AI suggestions were available")
    ai_processed = models.BooleanField(default=False, help_text="Whether AI processing was attempted")
    ai_error = models.TextField(blank=True, null=True, help_text="Any AI processing errors")
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

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
    
    # NEW: AI suggestion fields
    ai_suggestion = models.JSONField(null=True, blank=True, help_text="AI optimization suggestion")
    ai_action = models.CharField(max_length=50, blank=True, null=True, help_text="AI recommended action")
    ai_optimized_rule = models.TextField(blank=True, null=True, help_text="AI suggested optimized rule")
    ai_explanation = models.TextField(blank=True, null=True, help_text="AI explanation for the suggestion")
    
    class Meta:
        unique_together = ['session', 'relationship_type', 'rule_a', 'rule_b']
    
    def __str__(self):
        return f"{self.rule_a} {self.relationship_type} {self.rule_b} ({self.confidence:.2f})"

# NEW: Model to store AI suggestions separately for better organization
class AISuggestion(models.Model):
    """
    Stores AI-generated optimization suggestions for rule relationships
    """
    ACTION_CHOICES = [
        ('MERGE', 'Merge rules'),
        ('REMOVE_RULE_A', 'Remove Rule A'),
        ('REMOVE_RULE_B', 'Remove Rule B'), 
        ('KEEP_BOTH', 'Keep both rules'),
        ('REVIEW', 'Manual review needed'),
        ('REORDER', 'Reorder rules'),
    ]
    
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='ai_suggestions')
    relationship = models.ForeignKey(RuleRelationship, on_delete=models.CASCADE, null=True, blank=True)
    
    # Rule information
    rule_a = models.CharField(max_length=50)
    rule_b = models.CharField(max_length=50)
    relationship_type = models.CharField(max_length=3, choices=RuleRelationship.RELATIONSHIP_TYPES)
    
    # AI suggestion details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    optimized_rule = models.TextField(help_text="AI-generated optimized rule code")
    explanation = models.TextField(help_text="AI explanation for the suggestion")
    security_impact = models.TextField(help_text="Impact on security")
    performance_improvement = models.CharField(max_length=100, help_text="Expected performance gain")
    implementation_steps = models.JSONField(help_text="Step-by-step implementation guide")
    
    # Confidence and metadata
    confidence_score = models.FloatField(default=0.0)
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_suggestions'
        indexes = [
            models.Index(fields=['session', 'relationship_type']),
            models.Index(fields=['action']),
            models.Index(fields=['is_applied']),
        ]
    
    def __str__(self):
        return f"AI: {self.rule_a} & {self.rule_b} -> {self.action}"

# NEW: Model for overall AI optimization strategy
class AIOptimizationStrategy(models.Model):
    """
    Stores overall AI optimization strategy for a session
    """
    session = models.OneToOneField(RuleAnalysisSession, on_delete=models.CASCADE, related_name='ai_strategy')
    
    # Strategy components
    priority_actions = models.JSONField(help_text="High-priority actions sorted by impact")
    rule_merging_plan = models.JSONField(help_text="Specific rules to merge and approach")
    removal_candidates = models.JSONField(help_text="Rules that can be safely removed")
    performance_improvements = models.JSONField(help_text="Expected performance gains")
    security_considerations = models.JSONField(help_text="Security risks to watch for")
    implementation_priority = models.JSONField(help_text="Priority levels for each action")
    
    # Metadata
    total_optimizations_suggested = models.IntegerField(default=0)
    estimated_performance_gain = models.FloatField(default=0.0)
    estimated_security_impact = models.CharField(max_length=20, default='NEUTRAL', 
                                               choices=[('IMPROVED', 'Improved'), 
                                                       ('NEUTRAL', 'Neutral'), 
                                                       ('REDUCED', 'Reduced')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_optimization_strategies'
        verbose_name_plural = "AI Optimization Strategies"
    
    def __str__(self):
        return f"AI Strategy for {self.session.name}"

# FR03: Rule Performance Profiling Models
class RulePerformance(models.Model):
    """
    FR03-01: Tracks real performance data for each rule
    FR03-02: Calculates performance metrics  
    FR03-03: Flags inefficient rules
    """
    rule_id = models.CharField(max_length=50, unique=True)
    
    # FR03-01: Hit counting
    hit_count = models.IntegerField(default=0)
    total_requests_processed = models.IntegerField(default=0)
    
    # FR03-02: Performance metrics
    match_frequency = models.FloatField(default=0.0)  # hits / total_requests
    average_evaluation_time = models.FloatField(default=0.0)
    effectiveness_ratio = models.FloatField(default=0.0)  # true positives / total hits
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    # FR03-03: Rule efficiency flags
    is_rarely_used = models.BooleanField(default=False)
    is_redundant = models.BooleanField(default=False)
    is_high_performance = models.BooleanField(default=False)
    
    # NEW: AI optimization flags
    ai_optimization_suggested = models.BooleanField(default=False)
    ai_optimization_type = models.CharField(max_length=50, blank=True, null=True)
    last_ai_analysis = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rule_performance'
        indexes = [
            models.Index(fields=['hit_count']),
            models.Index(fields=['is_rarely_used']),
            models.Index(fields=['is_redundant']),
            models.Index(fields=['ai_optimization_suggested']),
        ]
    
    def __str__(self):
        return f"Performance: {self.rule_id} ({self.hit_count} hits)"

class PerformanceSnapshot(models.Model):
    """
    Tracks performance over time for analytics
    """
    snapshot_name = models.CharField(max_length=255)
    total_rules = models.IntegerField(default=0)
    rarely_used_count = models.IntegerField(default=0)
    redundant_count = models.IntegerField(default=0)
    high_performance_count = models.IntegerField(default=0)
    snapshot_data = models.JSONField()  # Detailed metrics
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW: AI optimization metrics
    ai_optimization_opportunities = models.IntegerField(default=0)
    estimated_ai_improvement = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'performance_snapshots'
    
    def __str__(self):
        return f"Snapshot: {self.snapshot_name}"

# FR05: Rule Ranking Models
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
    
    # NEW: AI-generated ranking fields
    ai_generated = models.BooleanField(default=False, help_text="Whether ranking was AI-generated")
    ai_confidence = models.FloatField(default=0.0, help_text="AI confidence in the ranking")
    ai_optimization_rationale = models.JSONField(null=True, blank=True, help_text="AI explanation for the ranking")
    
    class Meta:
        db_table = 'rule_ranking_sessions'

from django.db import models

class ThresholdSuggestion(models.Model):
    value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Threshold: {self.value} (Approved: {self.approved})"
    
    def __str__(self):
        ai_flag = " 🤖" if self.ai_generated else ""
        return f"Ranking: {self.name}{ai_flag} ({self.status})"

# NEW: Model to track AI usage and performance
class AIUsageLog(models.Model):
    """
    Tracks AI API usage for monitoring and billing
    """
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    response_time = models.FloatField(default=0.0)  # in seconds
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    cost_estimate = models.FloatField(default=0.0)  # estimated cost in USD
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_usage_logs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"AI Usage {status}: {self.endpoint} ({self.total_tokens} tokens)"
