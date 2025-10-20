import pandas as pd
import numpy as np
from typing import List, Dict
from django.db import transaction
from .models import RulePerformance, RuleRankingSession

class SmartRuleRanker:
    """
    FR05-01: Implements the "Smart Order" feature
    LEARNING: This is the brain that decides which rules should go first
    """
    
    def calculate_rule_priority_score(self, rule_performance: Dict) -> float:
        """
        FR05-01: Calculate priority score for each rule
        """
        hit_count_weight = 0.6
        effectiveness_weight = 0.3 
        recency_weight = 0.1
        
        # Normalize hit count (0 to 1 scale)
        max_hits = max(rule_performance['hit_count'], 1)
        normalized_hits = rule_performance['hit_count'] / max_hits
        
        # Effectiveness ratio (already 0-1)
        effectiveness = rule_performance['effectiveness_ratio']
        
        # Recency bonus (rules triggered recently get slight boost)
        recency_bonus = 0.1 if rule_performance.get('last_triggered') else 0.0
        
        priority_score = (
            normalized_hits * hit_count_weight +
            effectiveness * effectiveness_weight + 
            recency_bonus * recency_weight
        )
        
        return float(priority_score)  # ✅ Ensure it's Python float
    
    def convert_to_python_types(self, data):
        """
        Convert pandas/numpy types to Python native types for JSON serialization
        """
        if isinstance(data, (np.integer, pd.Int64Dtype)):
            return int(data)
        elif isinstance(data, (np.floating, pd.Float64Dtype)):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, pd.Series):
            return data.tolist()
        elif isinstance(data, dict):
            return {key: self.convert_to_python_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.convert_to_python_types(item) for item in data]
        else:
            return data
    
    def generate_optimized_ranking(self, rules_data: pd.DataFrame, performance_data: pd.DataFrame) -> List[Dict]:
        """
        FR05-01: Generate new rule order based on performance
        """
        optimized_rules = []
        
        for _, rule in rules_data.iterrows():
            rule_id = rule['rule_id']
            
            # Get performance data for this rule
            rule_perf = performance_data[performance_data['rule_id'] == rule_id]
            
            if not rule_perf.empty:
                # SAFELY get fields with default values
                perf_row = rule_perf.iloc[0]
                perf_dict = {
                    'hit_count': perf_row.get('hit_count', 0),
                    'effectiveness_ratio': perf_row.get('effectiveness_ratio', 0.0),
                    'last_triggered': perf_row.get('last_triggered', None)
                }
                
                priority_score = self.calculate_rule_priority_score(perf_dict)
                
                optimized_rules.append({
                    'rule_id': rule_id,
                    'rule_data': self.convert_to_python_types(rule.to_dict()),  # ✅ Convert to Python types
                    'priority_score': float(priority_score),  # ✅ Ensure Python float
                    'hit_count': int(perf_dict['hit_count']),  # ✅ Convert to Python int
                    'current_position': int(rule.get('position', 0))  # ✅ Convert to Python int
                })
        
        # FR05-01: Sort by priority score (highest first)
        optimized_rules.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Assign new positions
        for new_position, rule in enumerate(optimized_rules, 1):
            rule['new_position'] = int(new_position)  # ✅ Convert to Python int
            rule['position_change'] = int(rule['current_position'] - new_position)  # ✅ Convert to Python int
        
        return optimized_rules
    
    def calculate_performance_improvement(self, current_order: List, optimized_order: List) -> float:
        """
        FR05-04: Estimate performance improvement
        """
        total_rules = len(current_order)
        
        # Calculate average position in current order (lower = better)
        current_avg_position = sum(range(1, total_rules + 1)) / total_rules
        
        # Calculate weighted average position in optimized order
        optimized_weighted_sum = 0
        total_hits = 0
        
        for rule in optimized_order:
            position = rule['new_position']
            hit_count = rule['hit_count']
            optimized_weighted_sum += position * hit_count
            total_hits += hit_count
        
        optimized_avg_position = optimized_weighted_sum / total_hits if total_hits > 0 else current_avg_position
        
        # Improvement percentage
        improvement = ((current_avg_position - optimized_avg_position) / current_avg_position) * 100
        
        return float(max(improvement, 0))  # ✅ Ensure Python float

    @transaction.atomic
    def create_ranking_session(self, rules_data: pd.DataFrame, performance_data: pd.DataFrame, session_name: str) -> RuleRankingSession:
        """
        FR05-02: Create and save a ranking proposal
        """
        # Get current order
        current_order = []
        for position, (_, rule) in enumerate(rules_data.iterrows(), 1):
            current_order.append({
                'rule_id': rule['rule_id'],
                'position': int(position),  # ✅ Convert to Python int
                'rule_data': self.convert_to_python_types(rule.to_dict())  # ✅ Convert to Python types
            })
        
        # Generate optimized order
        optimized_order = self.generate_optimized_ranking(rules_data, performance_data)
        
        # Calculate improvement
        improvement = self.calculate_performance_improvement(current_order, optimized_order)
        
        # Create ranking session
        ranking_session = RuleRankingSession.objects.create(
            name=session_name,
            original_rules_order=self.convert_to_python_types(current_order),  # ✅ Convert to Python types
            optimized_rules_order=self.convert_to_python_types(optimized_order),  # ✅ Convert to Python types
            performance_improvement=float(improvement),  # ✅ Ensure Python float
            status='proposed'
        )
        
        return ranking_session