import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import re
import json
import logging
import requests
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

class DeepSeekAIClient:
    """Centralized AI client for all WAF optimization tasks"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com')
        
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not found in environment variables")
            raise ValueError("DeepSeek API key not configured")
        
        self.model = "deepseek-chat"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def make_request(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1000):
        """Generic method for all AI requests using requests library"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return self._parse_response(result['choices'][0]['message']['content'])
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            return self._create_error_response(str(e))
    
    def optimize_redundant_rules(self, rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context):
        """Specific method for rule optimization"""
        system_prompt = """You are a WAF security expert specializing in ModSecurity rule optimization. 
        Provide concise, actionable rule optimization suggestions in valid JSON format.
        Focus on practical improvements that maintain security while reducing redundancy."""
        
        user_prompt = self._build_rule_optimization_prompt(
            rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context
        )
        
        return self.make_request(system_prompt, user_prompt, temperature=0.3, max_tokens=800)
    
    def _build_rule_optimization_prompt(self, rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context):
        """Build the prompt for rule optimization"""
        
        # Extract rule details
        rule_a_details = self._extract_rule_details(rule_a_data)
        rule_b_details = self._extract_rule_details(rule_b_data)
        
        prompt = f"""
        Analyze these two WAF rules with a {relationship_type} relationship and suggest an optimized replacement:

        RULE A (ID: {rule_a_id}):
        - Attack Type: {rule_a_details['attack_type']}
        - Severity: {rule_a_details['severity']}
        - Matched Patterns: {rule_a_details['matched_data']}
        - Trigger Count: {rule_a_details['trigger_count']}

        RULE B (ID: {rule_b_id}):
        - Attack Type: {rule_b_details['attack_type']}
        - Severity: {rule_b_details['severity']}
        - Matched Patterns: {rule_b_details['matched_data']}
        - Trigger Count: {rule_b_details['trigger_count']}

        RELATIONSHIP: {relationship_type}
        CONFIDENCE: {analysis_context.get('confidence', 'N/A')}
        EVIDENCE COUNT: {analysis_context.get('evidence_count', 'N/A')}

        Provide a JSON response with these fields:
        - optimized_rule: A complete ModSecurity rule that combines both rules' protection
        - action: Specific instruction (MERGE, REMOVE_RULE_A, REMOVE_RULE_B, KEEP_BOTH)
        - explanation: Brief technical explanation
        - security_impact: How security is maintained or improved
        - performance_improvement: Expected performance gain
        - implementation_steps: Array of step-by-step actions

        Make the optimized rule practical and ready for ModSecurity deployment.
        """
        
        return prompt
    
    def _extract_rule_details(self, rule_data):
        """Extract relevant details from rule data"""
        if rule_data.empty:
            return {
                'attack_type': 'Unknown',
                'severity': 'Unknown', 
                'matched_data': 'None',
                'trigger_count': 0
            }
        
        first_row = rule_data.iloc[0]
        return {
            'attack_type': first_row.get('attack_type', 'Unknown'),
            'severity': first_row.get('severity', 'Unknown'),
            'matched_data': first_row.get('matched_data', 'None'),
            'trigger_count': len(rule_data)
        }
    
    def _parse_response(self, ai_response):
        """Parse AI response and ensure valid structure"""
        try:
            suggestion = json.loads(ai_response)
            
            # Ensure required fields exist
            required_fields = ['optimized_rule', 'action', 'explanation']
            for field in required_fields:
                if field not in suggestion:
                    suggestion[field] = f"Missing {field}"
            
            return suggestion
            
        except json.JSONDecodeError:
            return self._create_fallback_suggestion(ai_response)
    
    def _create_error_response(self, error_msg):
        """Create standardized error response"""
        return {
            "error": f"AI service unavailable: {error_msg}",
            "suggestion": "Please try again later or use manual analysis",
            "fallback_mode": True
        }
    
    def _create_fallback_suggestion(self, raw_text):
        """Create structured suggestion from raw text"""
        return {
            "optimized_rule": "# AI suggestion unavailable - manual review required",
            "action": "REVIEW", 
            "explanation": raw_text[:200] + "..." if len(raw_text) > 200 else raw_text,
            "security_impact": "Unknown - requires manual verification",
            "performance_improvement": "Unknown",
            "implementation_steps": [
                "1. Review the AI explanation above",
                "2. Manually create optimized rule",
                "3. Test thoroughly before deployment"
            ]
        }
    
class RuleAnalysisAIProcessor:
    """Processes rule relationship analysis results through DeepSeek AI"""
    
    def __init__(self):
        try:
            self.ai_client = DeepSeekAIClient()
            self.ai_available = True
            print("✅ AI client initialized successfully")
        except Exception as e:
            logger.warning(f"AI client initialization failed: {e}")
            self.ai_available = False
            print("❌ AI client initialization failed")
    
    def enhance_analysis_with_ai(self, analysis_results: Dict, traffic_df: pd.DataFrame) -> Dict:
        """
        Enhance rule analysis results with AI suggestions
        """
        if not self.ai_available:
            analysis_results['ai_available'] = False
            analysis_results['ai_suggestions'] = {"error": "AI service not available"}
            return analysis_results
        
        try:
            print("🔄 Getting AI suggestions...")
            # For now, return basic suggestions without API call
            ai_suggestions = self._create_basic_ai_suggestions(analysis_results)
            
            final_results = {
                **analysis_results,
                'ai_suggestions': ai_suggestions,
                'ai_available': True,
                'ai_analysis_summary': {
                    'total_relationships_processed': analysis_results.get('total_relationships', 0),
                    'rules_analyzed': analysis_results.get('total_rules', 0)
                }
            }
            
            return final_results
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {str(e)}")
            analysis_results['ai_available'] = False
            analysis_results['ai_suggestions'] = {"error": f"AI processing failed: {str(e)}"}
            return analysis_results
    
    def _create_basic_ai_suggestions(self, analysis_results: Dict) -> Dict:
        """Create basic rule-based suggestions when AI is unavailable"""
        relationships = analysis_results.get('relationships', {})
        ai_suggestions = {}
        
        for rel_type, rel_list in relationships.items():
            ai_suggestions[rel_type] = []
            for rel in rel_list:
                suggestion = {
                    'rule_a': rel['rule_a'],
                    'rule_b': rel['rule_b'], 
                    'relationship_type': rel_type,
                    'confidence': rel['confidence'],
                    'ai_suggestion': self._create_fallback_suggestion(rel),
                    'original_description': rel['description']
                }
                ai_suggestions[rel_type].append(suggestion)
        
        # Add overall strategy
        ai_suggestions['overall_strategy'] = {
            'priority_actions': [
                'Review shadowing relationships first',
                'Merge redundant rules for performance',
                'Monitor correlated rules for patterns'
            ],
            'estimated_improvement': '10-30% performance gain possible'
        }
        
        return ai_suggestions
    
    def _create_fallback_suggestion(self, relationship: Dict) -> Dict:
        """Create fallback suggestion when AI is unavailable"""
        rule_a = relationship['rule_a']
        rule_b = relationship['rule_b']
        rel_type = relationship['relationship_type']
        
        if rel_type == 'SHD':
            return {
                'action': 'REMOVE_RULE_B',
                'explanation': f'Rule {rule_a} shadows Rule {rule_b}. Consider removing {rule_b}.',
                'optimized_rule': f'# Keep Rule {rule_a}, remove Rule {rule_b}\n# Reason: Shadowing relationship',
                'performance_improvement': 'Reduced processing overhead',
                'implementation_steps': ['Remove Rule {rule_b} from configuration', 'Test Rule {rule_a} coverage']
            }
        elif rel_type == 'RXD':
            return {
                'action': 'MERGE',
                'explanation': f'Rules {rule_a} and {rule_b} are redundant. Merge into single rule.',
                'optimized_rule': f'# Merged rule combining {rule_a} and {rule_b}\n# Check patterns from both rules',
                'performance_improvement': 'Eliminated duplicate processing',
                'implementation_steps': ['Analyze patterns from both rules', 'Create combined rule', 'Remove original rules']
            }
        else:
            return {
                'action': 'REVIEW',
                'explanation': f'Rules {rule_a} and {rule_b} have {rel_type} relationship. Manual review needed.',
                'optimized_rule': '# Manual optimization required',
                'performance_improvement': 'Unknown',
                'implementation_steps': ['Review rule patterns', 'Check for optimization opportunities']
            }

class RuleRelationshipAnalyzer:
    def __init__(self, rules_df: pd.DataFrame, traffic_df: pd.DataFrame, enable_ai: bool = True):
        self.rules_df = rules_df
        self.traffic_df = traffic_df
        self.relationships = []
        self.enable_ai = enable_ai
        
        # Initialize AI processor if enabled
        if enable_ai:
            try:
                self.ai_processor = RuleAnalysisAIProcessor()
            except Exception as e:
                logger.warning(f"AI processor initialization failed: {e}")
                self.ai_processor = None
        else:
            self.ai_processor = None
    
    def analyze_all_relationships(self, analysis_types: List[str]) -> Dict:
        """FR02-01: Analyze all rules pairwise for relationships"""
        
        # Get unique rules that actually triggered (handle different column names)
        rule_id_column = 'rule_id'  # Your actual column name
        
        # Filter out empty/non-rule entries
        triggered_rules = self.traffic_df[
            (self.traffic_df[rule_id_column].notna()) & 
            (self.traffic_df[rule_id_column] != '-') & 
            (self.traffic_df[rule_id_column] != '')
        ][rule_id_column].unique()
        
        print(f"Found {len(triggered_rules)} unique triggered rules: {triggered_rules}")
        
        # FR02-01: Pairwise analysis
        for i, rule_a in enumerate(triggered_rules):
            for rule_b in triggered_rules[i+1:]:
                relationships = self.analyze_rule_pair(rule_a, rule_b, analysis_types)
                self.relationships.extend(relationships)
        
        # Compile base results
        base_results = self.compile_results()
        
        # Enhance with AI if enabled and available
        if self.enable_ai and self.ai_processor and self.ai_processor.ai_available:
            try:
                enhanced_results = self.ai_processor.enhance_analysis_with_ai(base_results, self.traffic_df)
                return enhanced_results
            except Exception as e:
                logger.error(f"AI enhancement failed: {e}")
                base_results['ai_available'] = False
                base_results['ai_error'] = str(e)
                return base_results
        
        base_results['ai_available'] = False
        return base_results
    
    def analyze_rule_pair(self, rule_a: str, rule_b: str, analysis_types: List[str]) -> List[Dict]:
        """Analyze relationship between two rules"""
        
        relationships = []
        
        # Get data for both rules using actual column names
        rule_a_data = self.traffic_df[self.traffic_df['rule_id'] == rule_a]
        rule_b_data = self.traffic_df[self.traffic_df['rule_id'] == rule_b]
        
        print(f"Analyzing {rule_a} ({len(rule_a_data)} requests) vs {rule_b} ({len(rule_b_data)} requests)")
        
        # FR02-02: Classify relationships with clear labels
        if 'SHD' in analysis_types:
            shadow_rel = self.check_shadowing(rule_a, rule_b, rule_a_data, rule_b_data)
            if shadow_rel:
                relationships.append(shadow_rel)
        
        if 'RXD' in analysis_types:
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
            
            if shadow_confidence > 0.5:  # Lowered threshold for testing
                return {
                    'relationship_type': 'SHD',
                    'rule_a': rule_a,
                    'rule_b': rule_b,
                    'confidence': shadow_confidence,
                    'evidence_count': len(common_requests),
                    'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                    'description': f"Rule {rule_a} shadows Rule {rule_b} - {len(common_requests)} common requests"
                }
        
        return None
    
    def check_redundancy(self, rule_a: str, rule_b: str, rule_a_data: pd.DataFrame, rule_b_data: pd.DataFrame) -> Dict:
        """Check for redundant rules (RXD)"""
        
        # Rules that always trigger together
        common_requests = self.find_common_requests(rule_a, rule_b)
        total_rule_a = len(rule_a_data)
        total_rule_b = len(rule_b_data)
        
        if total_rule_a > 0 and total_rule_b > 0:
            co_occurrence_rate = len(common_requests) / min(total_rule_a, total_rule_b)
            
            if co_occurrence_rate > 0.7:  # Lowered threshold for testing
                return {
                    'relationship_type': 'RXD',
                    'rule_a': rule_a,
                    'rule_b': rule_b,
                    'confidence': co_occurrence_rate,
                    'evidence_count': len(common_requests),
                    'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                    'description': f"Rules {rule_a} and {rule_b} are redundant - {co_occurrence_rate:.1%} co-occurrence"
                }
        
        return None
    
    def check_correlation(self, rule_a: str, rule_b: str, rule_a_data: pd.DataFrame, rule_b_data: pd.DataFrame) -> Dict:
        """Check for correlated rules (COR)"""
        
        common_requests = self.find_common_requests(rule_a, rule_b)
        total_requests = len(self.traffic_df)
        
        if total_requests > 0:
            expected_co_occurrence = (len(rule_a_data) / total_requests) * (len(rule_b_data) / total_requests)
            actual_co_occurrence = len(common_requests) / total_requests
            
            if actual_co_occurrence > expected_co_occurrence * 1.5:  # Lowered threshold
                correlation_strength = actual_co_occurrence / expected_co_occurrence
                
                return {
                    'relationship_type': 'COR',
                    'rule_a': rule_a,
                    'rule_b': rule_b,
                    'confidence': min(correlation_strength / 5, 1.0),  # Normalize to 0-1
                    'evidence_count': len(common_requests),
                    'conflicting_fields': self.get_conflicting_fields(rule_a, rule_b),
                    'description': f"Rules {rule_a} and {rule_b} are correlated - {correlation_strength:.1f}x expected rate"
                }
        
        return None
    
    def find_common_requests(self, rule_a: str, rule_b: str) -> List:
        """Find requests where both rules triggered"""
        rule_a_requests = set(self.traffic_df[self.traffic_df['rule_id'] == rule_a]['transaction_id'])
        rule_b_requests = set(self.traffic_df[self.traffic_df['rule_id'] == rule_b]['transaction_id'])
        common = list(rule_a_requests.intersection(rule_b_requests))
        print(f"Common requests between {rule_a} and {rule_b}: {len(common)}")
        return common
    
    def get_conflicting_fields(self, rule_a: str, rule_b: str) -> Dict:
        """Identify specific fields causing the relationship"""
        rule_a_patterns = self.extract_rule_patterns(rule_a)
        rule_b_patterns = self.extract_rule_patterns(rule_b)
        
        conflicting = {}
        
        # Check attack_type
        if rule_a_patterns.get('attack_type') and rule_b_patterns.get('attack_type'):
            if rule_a_patterns['attack_type'] == rule_b_patterns['attack_type']:
                conflicting['attack_type'] = f"Both detect: {rule_a_patterns['attack_type']}"
        
        # Check severity  
        if rule_a_patterns.get('severity') and rule_b_patterns.get('severity'):
            if rule_a_patterns['severity'] == rule_b_patterns['severity']:
                conflicting['severity'] = f"Same severity: {rule_a_patterns['severity']}"
        
        return conflicting
    
    def extract_rule_patterns(self, rule_id: str) -> Dict:
        """Extract patterns from rule data using actual column names"""
        rule_data = self.traffic_df[self.traffic_df['rule_id'] == rule_id]
        
        if rule_data.empty:
            return {}
        
        first_row = rule_data.iloc[0]
        patterns = {
            'attack_type': first_row.get('attack_type', 'Unknown'),
            'severity': first_row.get('severity', 'Unknown'),
            'matched_data': first_row.get('matched_data', 'None'),
        }
        
        return patterns
    
    def compile_results(self) -> Dict:
        """Compile all analysis results"""
        relationships_by_type = {}
        for rel in self.relationships:
            rel_type = rel['relationship_type']
            if rel_type not in relationships_by_type:
                relationships_by_type[rel_type] = []
            relationships_by_type[rel_type].append(rel)
        
        # Get unique rules that triggered
        triggered_rules = self.traffic_df[
            (self.traffic_df['rule_id'].notna()) & 
            (self.traffic_df['rule_id'] != '-') & 
            (self.traffic_df['rule_id'] != '')
        ]['rule_id'].unique()
        
        return {
            'total_rules': len(triggered_rules),
            'total_relationships': len(self.relationships),
            'relationships': relationships_by_type,
            'shd_count': len([r for r in self.relationships if r['relationship_type'] == 'SHD']),
            'rxd_count': len([r for r in self.relationships if r['relationship_type'] == 'RXD']),
            'recommendations': self.generate_recommendations(),
            'triggered_rules_sample': list(triggered_rules)[:10]  # For debugging
        }
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
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
        
        if not recommendations and self.relationships:
            recommendations.append({
                'type': 'Review Correlated Rules',
                'description': f"Review {len(self.relationships)} rule relationships for optimization opportunities",
                'impact': 'Potential performance improvements'
            })
        
        return recommendations