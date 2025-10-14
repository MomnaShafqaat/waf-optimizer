from waf_analysis.models import RuleRelationship
from data_management.models import UploadedFile
import pandas as pd

def analyze_rule_conflicts():
    # Load the latest WAF rules CSV from UploadedFile
    rules_file = UploadedFile.objects.filter(file_type='rules').last()
    if not rules_file:
        return "No rules uploaded"

    df = pd.read_csv(rules_file.file.path)  # Assumes a CSV with columns like 'id', 'pattern', 'action'
    
    # Clear old relationships
    RuleRelationship.objects.all().delete()

    # Pairwise comparison
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            rule1 = df.iloc[i]
            rule2 = df.iloc[j]

            # Simple placeholder logic (you will replace with real conflict detection)
            if rule1['pattern'] == rule2['pattern']:
                rel_type = 'RXD'
            elif rule1['pattern'] in rule2['pattern']:
                rel_type = 'SHD'
            else:
                rel_type = 'COR'

            RuleRelationship.objects.create(
                rule_1=rule1['id'],
                rule_2=rule2['id'],
                relationship_type=rel_type,
                details=f"{rule1['pattern']} vs {rule2['pattern']}"
            )
