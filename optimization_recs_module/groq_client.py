# groq_client.py

import requests
import os
import json
import logging
import re
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GroqAIClient:
    """Centralized AI client for all WAF optimization tasks using Groq API"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1"
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            raise ValueError("Groq API key not configured")
        
        # Use only the model that we know works
        self.model = "llama-3.1-8b-instant"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test API connection on initialization
        self._test_api_connection()
    
    def _test_api_connection(self):
        """Test Groq API connection with a simple request"""
        try:
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Respond with just 'OK'"}],
                "max_tokens": 5,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                test_response = result['choices'][0]['message']['content'].strip()
                print(f"✅ Groq API connection test successful: '{test_response}'")
                return True
            else:
                print(f"❌ Groq API connection failed: {response.status_code} - {response.text}")
                raise Exception(f"Groq API connection failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Groq API connection error: {e}")
            raise Exception(f"Groq API connection error: {e}")
    
    def make_request(self, system_prompt, user_prompt, temperature=0.5, max_tokens=600):
        """Generic method for all AI requests using requests library (NO FUNCTION CALLING)"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # ... (rest of the API request logic remains the same) ...
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # ... (rest of the error handling remains the same) ...
            
            result = response.json()
            
            # 💡 NOTE: The model's response structure changes. We now grab 'content'.
            return self._parse_text_response(result['choices'][0]['message']['content']) 
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = f" - {error_response}"
            except:
                error_detail = f" - Response: {response.text}"
            
            logger.error(f"Groq API HTTP error {response.status_code}: {e}{error_detail}")
            raise Exception(f"Groq API HTTP error {response.status_code}: {e}")
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Groq API error: {e}")
    
    def optimize_redundant_rules(self, rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context):
        """Specific method for rule optimization with labeled text output"""
        
        system_prompt = """
        You are a WAF rule optimization expert. Your task is to analyze two rules and provide a single, prioritized suggestion to merge or remove one.
        
        **RESPOND WITH ONLY THE LABELED SECTIONS BELOW.** DO NOT add any extra explanation or introductory text.

        - **OPTIMIZED RULE SYNTAX:** [Provide the complete, single ModSecurity rule syntax here]
        - **ACTION:** [MERGE|REMOVE_RULE_A|REMOVE_RULE_B|KEEP_BOTH]
        - **EXPLANATION:** [Brief explanation of the decision.]
        - **SECURITY IMPACT:** [How security is maintained or improved.]
        - **PERFORMANCE IMPROVEMENT:** [Expected performance gain.]
        - **IMPLEMENTATION STEPS:** [Step 1; Step 2; Step 3; ...]
        """
        
        user_prompt = self._build_rule_optimization_prompt(
            rule_a_id, rule_b_id, relationship_type, rule_a_data, rule_b_data, analysis_context
        )
        
        # Use slightly higher temperature for better compliance
        return self.make_request(system_prompt, user_prompt, temperature=0.5, max_tokens=600)
    
    def _build_rule_optimization_prompt(self,
                                        rule_a_id, rule_b_id, relationship_type,
                                        rule_a_data, rule_b_data, analysis_context):

        # rule_a_data & rule_b_data are now dicts
        rule_a_details = {
            'attack_type': rule_a_data.get('attack_type', 'Unknown'),
            'severity': rule_a_data.get('severity', 'Unknown'),
            'matched_data': rule_a_data.get('matched_data', 'None'),
            'trigger_count': rule_a_data.get('trigger_count', 0)
        }
        rule_b_details = {
            'attack_type': rule_b_data.get('attack_type', 'Unknown'),
            'severity': rule_b_data.get('severity', 'Unknown'),
            'matched_data': rule_b_data.get('matched_data', 'None'),
            'trigger_count': rule_b_data.get('trigger_count', 0)
        }

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
    
    def _parse_text_response(self, ai_response):
        """
        Aggressively extracts the primary suggestion by identifying the main action 
        and the first complete pattern/JSON structure found in the raw text, 
        since the AI refuses to use markers.
        """
        raw_text = ai_response.strip()
        
        # 1. Initialize fallback result structure
        result = {
            "optimized_rule": "N/A (Pattern not found)",
            "action": "REVIEW_MANUALLY",
            "explanation": "AI output could not be parsed into structure. Requires manual review.",
            "security_impact": "Requires manual review.",
            "performance_improvement": "N/A",
            "implementation_steps": ["Check raw response for suggested actions."]
        }

        # 2. Extract potential JSON structures or SQL code blocks (Optionally provided by AI)
        # This targets the common JSON blocks the AI outputs.
        json_candidates = re.findall(r'\{.*?\}', raw_text, re.DOTALL)
        
        # 3. Analyze the overall text for the primary recommended action
        if re.search(r'Merge|combine', raw_text, re.IGNORECASE):
            result['action'] = "MERGE"
            result['explanation'] = "AI suggests merging the two rules."
        elif re.search(r'Remove Rule B|Remove Rule 1021|Remove Rule 1026|Remove Rule 1019|Remove Rule 1023', raw_text, re.IGNORECASE):
            result['action'] = "REMOVE_RULE_B"
            result['explanation'] = "AI suggests removing Rule B as redundant or lower priority."
        elif re.search(r'Downgrade|Modify Rule A|Update Rule 1001', raw_text, re.IGNORECASE):
            result['action'] = "MODIFY_RULE_A"
            result['explanation'] = "AI suggests modifying Rule A (often to merge pattern or change severity/action)."

        # 4. Extract the BEST PATTERN/RULE SYNTAX
        
        # A. Try to extract the pattern from the first JSON block, if present
        if json_candidates:
            # We try to clean and load the first candidate
            json_str = json_candidates[0]
            json_str = re.sub(r'//.*', '', json_str) # Remove comments
            try:
                parsed_json = json.loads(json_str)
                if 'pattern' in parsed_json:
                    pattern = parsed_json['pattern'].strip('"').strip()
                    result['optimized_rule'] = f"Suggested Pattern: {pattern}"
                    # If we get a rule ID, we can update the action if the JSON suggests it
                    if 'action' in parsed_json and 'severity' in parsed_json:
                        result['explanation'] += f" The AI provided a target JSON structure with action: {parsed_json['action']} and severity: {parsed_json['severity']}."
                elif 'rule_id' in parsed_json:
                    # If it's a valid JSON but no pattern, log what we got
                    result['optimized_rule'] = f"AI provided structural Rule Data, not final syntax."

            except json.JSONDecodeError:
                # Failed to parse the JSON block, so we move to text extraction
                pass 

        # B. If no pattern was extracted from JSON, try to extract from SQL code blocks
        if result['optimized_rule'] == "N/A (Pattern not found)":
            sql_match = re.search(r'```(?:sql)?\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
            if sql_match:
                pattern = sql_match.group(1).strip()
                result['optimized_rule'] = f"Suggested Pattern: {pattern}"
                result['explanation'] = "Rule pattern extracted from SQL code block."

        # 5. Final check for removal case
        if result['action'] == "REMOVE_RULE_B" and result['optimized_rule'] == "N/A (Pattern not found)":
            result['optimized_rule'] = "Keep Rule A as is, remove Rule B."


        # 6. We manually map the essential fields to fulfill the expected contract,
        # prioritizing the extracted 'action' and 'optimized_rule'.
        
        return {
            "optimized_rule": result['optimized_rule'],
            "action": result['action'],
            "explanation": result['explanation'],
            "security_impact": result['security_impact'],
            "performance_improvement": result['performance_improvement'],
            "implementation_steps": result['implementation_steps']
        }
