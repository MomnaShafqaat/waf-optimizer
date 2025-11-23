# ai_processor.py

import json
import logging
import pandas as pd
from typing import Dict, List
from .groq_client import GroqAIClient # Import the client


logger = logging.getLogger(__name__)

class RuleAnalysisAIProcessor:
    """Processes rule relationship analysis results through Groq AI"""
    
    def __init__(self, rules_df: pd.DataFrame = None, ai_client=None):
        try:
            self.rules_df = rules_df
            self.ai_client = ai_client or GroqAIClient()
            self.ai_available = True
            print("✅ Groq AI client initialized successfully")
        except Exception as e:
            logger.warning(f"AI client initialization failed: {e}")
            self.ai_available = False
            self.ai_client = None
            print(f"❌ AI client initialization failed: {e}")

    def _get_rule_data(self, rule_id: str) -> Dict:
        """Extract data for a given rule_id from rules_df safely."""
        if self.rules_df is None or self.rules_df.empty:
            raise ValueError("rules_df is not available in RuleAnalysisAIProcessor")

        id_column = 'id' if 'id' in self.rules_df.columns else 'rule_id'
        rule_row = self.rules_df[self.rules_df[id_column].astype(str) == str(rule_id)]

        if rule_row.empty:
            logger.warning(f"No data found for rule {rule_id}")
            return {
                "rule_id": rule_id,
                "description": "N/A",
                "severity": "N/A",
                "action": "N/A",
                "phase": "N/A",
                "pattern": "N/A",
            }

        row = rule_row.iloc[0]
        return {
            "rule_id": str(rule_id),
            "description": row.get("msg", ""),
            "severity": row.get("severity", ""),
            "action": row.get("action", ""),
            "phase": row.get("phase", ""),
            "pattern": row.get("pattern", ""),
        }
    
    def enhance_analysis_with_ai(self, analysis_results: Dict, traffic_df: pd.DataFrame) -> Dict:
        """
        Use Groq AI to enhance rule relationship analysis results.
        - Sends redundant, shadowed, and correlated rule pairs to Groq for optimization insights.
        """

        if not self.ai_available or not self.ai_client:
            logger.warning("AI not available — returning base analysis only.")
            analysis_results["ai_available"] = False
            analysis_results["ai_error"] = "AI client not available"
            return analysis_results

        try:
            ai_suggestions = {
                "redundant": [],
                "shadowed": [],
                "correlated": []
            }

            # Loop over each relationship type
            for rel_type, rel_list in analysis_results.get("relationships", {}).items():
                for rel in rel_list:
                    rule_a_id = rel.get("rule_a")
                    rule_b_id = rel.get("rule_b")

                    if not rule_a_id or not rule_b_id:
                        continue

                    # Extract contextual rule data
                    rule_a_data = self._get_rule_data(rule_a_id)
                    rule_b_data = self._get_rule_data(rule_b_id)

                    # Prepare shared context
                    context = {
                        "relationship_type": rel_type,
                        "confidence": rel.get("confidence"),
                        "evidence_count": rel.get("evidence_count"),
                        "conflicting_fields": rel.get("conflicting_fields", {}),
                        "description": rel.get("description", "")
                    }

                    try:
                        # 🔹 Redundant Rules (merge/delete suggestions)
                        if rel_type == "RXD":
                            ai_response = self.ai_client.optimize_redundant_rules(
                                rule_a_id, rule_b_id, rel_type, rule_a_data, rule_b_data, context
                            )
                            ai_suggestions["redundant"].append(ai_response)

                        # 🔹 Shadowed Rules (identify dominant rule)
                        elif rel_type == "SHD":
                            user_prompt = (
                                f"Rule {rule_a_id} shadows {rule_b_id}. "
                                f"Suggest how to merge or remove one without reducing security.\n\n"
                                f"Rule A Data: {json.dumps(rule_a_data, indent=2, default=str)}\n"
                                f"Rule B Data: {json.dumps(rule_b_data, indent=2, default=str)}\n"
                            )
                            ai_response = self.ai_client.make_request(
                                "You are a WAF optimization expert. Suggest minimal-impact actions.",
                                user_prompt,
                                temperature=0.3,
                                max_tokens=800
                            )
                            ai_suggestions["shadowed"].append(ai_response)

                        # 🔹 Correlated Rules (suggest grouping or simplification)
                        elif rel_type == "COR":
                            user_prompt = (
                                f"Rules {rule_a_id} and {rule_b_id} often trigger together (correlated). "
                                f"Suggest optimization or grouping ideas.\n\n"
                                f"Rule A: {json.dumps(rule_a_data, indent=2, default=str)}\n"
                                f"Rule B: {json.dumps(rule_b_data, indent=2, default=str)}\n"
                                f"Traffic Context: {json.dumps(context, indent=2, default=str)}"
                            )
                            ai_response = self.ai_client.make_request(
                                "You are a ModSecurity correlation analyzer.",
                                user_prompt,
                                temperature=0.4,
                                max_tokens=800
                            )
                            ai_suggestions["correlated"].append(ai_response)
                            
                    except Exception as e:
                        logger.error(f"AI request failed for {rule_a_id} vs {rule_b_id}: {e}")
                        # Continue with other pairs instead of failing completely

            # Merge AI results into output
            analysis_results["ai_available"] = True
            analysis_results["ai_suggestions"] = ai_suggestions

            print(f"✅ AI enhancement completed successfully")
            return analysis_results

        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            analysis_results["ai_available"] = False
            analysis_results["ai_error"] = str(e)
            return analysis_results