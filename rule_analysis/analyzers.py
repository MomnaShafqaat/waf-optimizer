import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import re

class RuleRelationshipAnalyzer:
    def __init__(self, rules_df: pd.DataFrame, traffic_df: pd.DataFrame):
        self.rules_df = rules_df
        self.traffic_df = traffic_df
        self.relationships = []
    
    def analyze_all_relationships(self, analysis_types: List[str]) -> Dict:
        """FR02-01: Analyze all rules pairwise for relationships"""
        
        # Get unique rules that actually triggered
        triggered_rules = self.traffic_df[self.traffic_df['rule_id'] != '-']['rule_id'].unique()
        
        # FR02-01: Pairwise analysis
        for i, rule_a in enumerate(triggered_rules):
            for rule_b in triggered_rules[i+1:]:
                relationships = self.analyze_rule_pair(rule_a, rule_b, analysis_types)
                self.relationships.extend(relationships)
        
        return self.compile_results()
    
    def analyze_rule_pair(self, rule_a: str, rule_b: str, analysis_types: List[str]) -> List[Dict]:
        """Analyze relationship between two rules"""
        
        relationships = []
        
        # Get data for both rules
        rule_a_data = self.traffic_df[self.traffic_df['rule_id'] == rule_a]
        rule_b_data = self.traffic_df[self.traffic_df['rule_id'] == rule_b]
        
        # FR02-02: Classify relationships with clear labels
        if 'SHD' in analysis_types:
            shadow_rel = self.check_shadowing(rule_a, rule_b, rule_a_data, rule_b_data)
            if shadow_rel:
                relationships.append(shadow_rel)
        
        if 'GEN' in analysis_types:
            gen_rel = self.check_generalization(rule_a, rule_b, rule_a_data, rule_b_data)
            if gen_rel:
                relationships.append(gen_rel)
        
        if 'RXD' in analysis_types or 'RYD' in analysis_types:
            red_rel = self.check_redundancy(rule_a, rule_b, rule_a_data, rule_b_data)
            if red_rel:
                relationships.append(red_rel)
        
        if 'COR' in analysis_types:
            cor_rel = self.check_correlation(rule_a, rule_b, rule_a_data, rule_b_data)
            if cor_rel:
                relationships.append(cor_rel)
        
        return relationships
    
    def check_shadowing(self, rule_a: str, rule_b: str, rule_a_data: pd.DataFrame, rule_b_data: pd.DataFrame) -> Dict:
        """Check if rule_a shadows rule_b (SHD)"""
        
        # Rules that trigger on the same requests but rule_a always triggers first/alone
        common_requests = self.find_common_requests(rule_a, rule_b)
        
        if len(common_requests) > 0:
            # Check if rule_a blocks requests that rule_b would also catch
            rule_a_blocks = len(rule_a_data[rule_a_data['action'] == 'blocked'])
            rule_b_blocks = len(rule_b_data[rule_b_data['action'] == 'blocked'])
            
            shadow_confidence = len(common_requests) / max(len(rule_a_data), len(rule_b_data))
            
            if shadow_confidence > 0.7:  # High overlap threshold
                return {
                    'relationship_type': 'SHD',
                    'rule_a': rule_a,
                    'rule_b': rule_b,
                    'confidence': shadow_confidence,
                    'evidence_count': len(common_requests),
                    'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                    'description': f"Rule {rule_a} shadows Rule {rule_b} - they trigger on similar patterns"
                }
        
        return None
    
    def check_generalization(self, rule_a: str, rule_b: str, rule_a_data: pd.DataFrame, rule_b_data: pd.DataFrame) -> Dict:
        """Check if rule_a is more general than rule_b (GEN)"""
        
        # Rule A catches everything Rule B catches plus more
        rule_b_requests = set(rule_b_data['transaction_id'])
        rule_a_requests = set(rule_a_data['transaction_id'])
        
        if rule_b_requests.issubset(rule_a_requests) and len(rule_a_requests) > len(rule_b_requests):
            generalization_confidence = len(rule_b_requests) / len(rule_a_requests)
            
            return {
                'relationship_type': 'GEN',
                'rule_a': rule_a,
                'rule_b': rule_b,
                'confidence': generalization_confidence,
                'evidence_count': len(rule_b_requests),
                'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                'description': f"Rule {rule_a} is more general than Rule {rule_b}"
            }
        
        return None
    
    def check_redundancy(self, rule_a: str, rule_b: str, rule_a_data: pd.DataFrame, rule_b_data: pd.DataFrame) -> Dict:
        """Check for redundant rules (RXD/RYD)"""
        
        # Rules that always trigger together
        common_requests = self.find_common_requests(rule_a, rule_b)
        total_rule_a = len(rule_a_data)
        total_rule_b = len(rule_b_data)
        
        if total_rule_a > 0 and total_rule_b > 0:
            co_occurrence_rate = len(common_requests) / min(total_rule_a, total_rule_b)
            
            if co_occurrence_rate > 0.9:  # Almost always trigger together
                return {
                    'relationship_type': 'RXD',
                    'rule_a': rule_a,
                    'rule_b': rule_b,
                    'confidence': co_occurrence_rate,
                    'evidence_count': len(common_requests),
                    'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                    'description': f"Rules {rule_a} and {rule_b} are redundant - they trigger on identical patterns"
                }
        
        return None
    
    def check_correlation(self, rule_a: str, rule_b: str, rule_a_data: pd.DataFrame, rule_b_data: pd.DataFrame) -> Dict:
        """Check for correlated rules (COR)"""
        
        common_requests = self.find_common_requests(rule_a, rule_b)
        total_requests = len(self.traffic_df)
        
        if total_requests > 0:
            expected_co_occurrence = (len(rule_a_data) / total_requests) * (len(rule_b_data) / total_requests)
            actual_co_occurrence = len(common_requests) / total_requests
            
            if actual_co_occurrence > expected_co_occurrence * 2:  # Significant correlation
                correlation_strength = actual_co_occurrence / expected_co_occurrence
                
                return {
                    'relationship_type': 'COR',
                    'rule_a': rule_a,
                    'rule_b': rule_b,
                    'confidence': min(correlation_strength / 10, 1.0),  # Normalize to 0-1
                    'evidence_count': len(common_requests),
                    'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                    'description': f"Rules {rule_a} and {rule_b} are correlated - they frequently trigger together"
                }
        
        return None
    
    def find_common_requests(self, rule_a: str, rule_b: str) -> List:
        """Find requests where both rules triggered"""
        rule_a_requests = set(self.traffic_df[self.traffic_df['rule_id'] == rule_a]['transaction_id'])
        rule_b_requests = set(self.traffic_df[self.traffic_df['rule_id'] == rule_b]['transaction_id'])
        return list(rule_a_requests.intersection(rule_b_requests))
    
    def get_conflicting_fields(self, rule_a: str, rule_b: str) -> Dict:
        """FR02-03: Identify specific fields causing the relationship"""
        # Compare rule patterns, conditions, or triggered parameters
        rule_a_patterns = self.extract_rule_patterns(rule_a)
        rule_b_patterns = self.extract_rule_patterns(rule_b)
        
        conflicting = {}
        for field in ['attack_type', 'severity', 'matched_data']:
            if rule_a_patterns.get(field) and rule_b_patterns.get(field):
                if rule_a_patterns[field] == rule_b_patterns[field]:
                    conflicting[field] = f"Both rules use: {rule_a_patterns[field]}"
        
        return conflicting
    
    def extract_rule_patterns(self, rule_id: str) -> Dict:
        """Extract patterns from rule data"""
        rule_data = self.traffic_df[self.traffic_df['rule_id'] == rule_id].iloc[0] if not self.traffic_df[self.traffic_df['rule_id'] == rule_id].empty else {}
        
        patterns = {}
        if not rule_data.empty:
            patterns['attack_type'] = rule_data.get('attack_type', '')
            patterns['severity'] = rule_data.get('severity', '')
            patterns['matched_data'] = rule_data.get('matched_data', '')
        
        return patterns
    
    def compile_results(self) -> Dict:
        """Compile all analysis results"""
        relationships_by_type = {}
        for rel in self.relationships:
            rel_type = rel['relationship_type']
            if rel_type not in relationships_by_type:
                relationships_by_type[rel_type] = []
            relationships_by_type[rel_type].append(rel)
        
        return {
            'total_rules': len(self.traffic_df[self.traffic_df['rule_id'] != '-']['rule_id'].unique()),
            'total_relationships': len(self.relationships),
            'relationships': relationships_by_type,
            'shd_count': len([r for r in self.relationships if r['relationship_type'] == 'SHD']),
            'rxd_count': len([r for r in self.relationships if r['relationship_type'] == 'RXD']),
            'recommendations': self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Example recommendations based on analysis
        shadowed_rules = [r for r in self.relationships if r['relationship_type'] == 'SHD']
        if shadowed_rules:
            recommendations.append({
                'type': 'Remove Shadowed Rules',
                'description': f"Remove {len(shadowed_rules)} rules that are shadowed by more general rules",
                'impact': 'Improve performance without reducing security'
            })
        
        redundant_rules = [r for r in self.relationships if r['relationship_type'] == 'RXD']
        if redundant_rules:
            recommendations.append({
                'type': 'Merge Redundant Rules', 
                'description': f"Merge {len(redundant_rules)} pairs of redundant rules",
                'impact': 'Reduce rule complexity and maintenance overhead'
            })
        
        return recommendations