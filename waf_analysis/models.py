
# Create your models here.
from django.db import models
from data_management.models import UploadedFile

class RuleRelationship(models.Model):
    rule_1 = models.CharField(max_length=255)
    rule_2 = models.CharField(max_length=255)
    relationship_type = models.CharField(
        max_length=10,
        choices=[
            ('SHD', 'Shadowing'),
            ('GEN', 'Generalization'),
            ('RXD', 'Redundancy'),
            ('COR', 'Correlation')
        ]
    )
    details = models.TextField(blank=True, null=True)
    detected_at = models.DateTimeField(auto_now_add=True)
