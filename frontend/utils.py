# frontend/utils.py
import requests
import streamlit as st

# API URLs
API_URL = "http://127.0.0.1:8000/api/files/"
FILES_SUMMARY_URL = "http://127.0.0.1:8000/api/files/summary/"
HEALTH_URL = "http://127.0.0.1:8000/api/health/"
RULE_ANALYSIS_API_URL = "http://127.0.0.1:8000/api/analyze/"
# Sessions endpoint (RuleAnalysisSession ViewSet registered as 'sessions')
SESSIONS_API_URL = "http://127.0.0.1:8000/api/sessions/"
RANKING_API_URL = "http://127.0.0.1:8000/api/ranking/generate/"
RANKING_COMPARISON_URL = "http://127.0.0.1:8000/api/ranking/comparison/"
HIT_COUNTS_UPDATE_URL = "http://127.0.0.1:8000/api/hit-counts/update/"
HIT_COUNTS_DASHBOARD_URL = "http://127.0.0.1:8000/api/hit-counts/dashboard/"

# FR04: False Positive Reduction API URLs
FALSE_POSITIVE_DETECT_URL = "http://127.0.0.1:8000/api/false-positives/detect/"
FALSE_POSITIVE_DASHBOARD_URL = "http://127.0.0.1:8000/api/false-positives/dashboard/"
WHITELIST_SUGGESTIONS_URL = "http://127.0.0.1:8000/api/false-positives/suggestions/"
LEARNING_MODE_START_URL = "http://127.0.0.1:8000/api/learning-mode/start/"
LEARNING_MODE_STATUS_URL = "http://127.0.0.1:8000/api/learning-mode/status/"
WHITELIST_EXPORT_URL = "http://127.0.0.1:8000/api/whitelist/export/"
SUGGESTION_DEPLOYMENT_URL = "http://127.0.0.1:8000/api/suggestions/deploy/"

def check_backend_status():
    """Check if backend is online"""
    try:
        response = requests.get(HEALTH_URL, timeout=3)
        return response.status_code == 200
    except:
        return False

def get_files_data():
    """Get uploaded files data"""
    try:
        response = requests.get(FILES_SUMMARY_URL)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and ('rules' in data or 'traffic' in data):
                rules = data.get('rules', []) or []
                traffic = data.get('traffic', []) or []
                return rules + traffic
            return data
        return []
    except:
        return []

def create_analysis_session(name, rules_file_id, traffic_file_id, analysis_types=None):
    """Create a RuleAnalysisSession via the backend API and return the session object"""
    try:
        if analysis_types is None:
            analysis_types = ['SHD', 'RXD', 'GEN', 'COR']
        data = {
            'name': name,
            'rules_file': rules_file_id,
            'traffic_file': traffic_file_id,
            'analysis_types': analysis_types
        }
        response = requests.post(SESSIONS_API_URL, json=data)
        return response
    except Exception as e:
        st.error(f"Create session error: {str(e)}")
        return None

def analyze_rules_by_session(session_id, analysis_types=None):
    """Request rule analysis for an existing backend session (session_id)."""
    try:
        data = {'session_id': session_id}
        if analysis_types:
            data['analysis_types'] = analysis_types
        response = requests.post(RULE_ANALYSIS_API_URL, json=data, timeout=60)
        return response
    except Exception as e:
        st.error(f"Analyze by session error: {str(e)}")
        return None

def analyze_rules(rules_content, logs_content, analysis_types):
    """Run rule analysis with file content as strings"""
    try:
        # Convert bytes to string if needed
        if isinstance(rules_content, bytes):
            rules_content = rules_content.decode('utf-8')
        if isinstance(logs_content, bytes):
            logs_content = logs_content.decode('utf-8')
        
        analysis_data = {
            'rules_content': rules_content,
            'logs_content': logs_content,
            'analysis_types': [atype[:3].upper() for atype in analysis_types]
        }
        
        response = requests.post(RULE_ANALYSIS_API_URL, json=analysis_data, timeout=30)
        return response
        
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def generate_rule_ranking(rules_file_id, session_name):
    """Generate optimized rule ranking"""
    # Prefer sending file content rather than ids
    try:
        import streamlit as st
        rules_content = None
        try:
            rules_content = st.session_state.get('rules_file_content')
        except Exception:
            pass

        # Decode bytes to string if necessary
        if isinstance(rules_content, (bytes, bytearray)):
            rules_content = rules_content.decode('utf-8')

        payload = {"session_name": session_name}
        if rules_content:
            payload['rules_content'] = rules_content
        else:
            # fallback to identifier if content missing
            payload['rules_file_id'] = rules_file_id

        response = requests.post(RANKING_API_URL, json=payload)
        return response
    except Exception as e:
        st.error(f"Ranking generation error: {str(e)}")
        return None

def get_ranking_comparison(session_id):
    """Get ranking comparison data"""
    try:
        response = requests.get(f"{RANKING_COMPARISON_URL}{session_id}/")
        return response
    except Exception as e:
        st.error(f"Ranking comparison error: {str(e)}")
        return None

def update_performance_data():
    """Update performance data (FR03)"""
    try:
        import streamlit as st
        # Send file contents instead of IDs
        rules_content = st.session_state.get('rules_file_content')
        logs_content = st.session_state.get('logs_file_content')

        # Decode bytes to string if necessary
        if isinstance(rules_content, (bytes, bytearray)):
            rules_content = rules_content.decode('utf-8')
        if isinstance(logs_content, (bytes, bytearray)):
            logs_content = logs_content.decode('utf-8')

        payload = {}
        if logs_content:
            payload['traffic_content'] = logs_content
        if rules_content:
            payload['rules_content'] = rules_content

        response = requests.post(HIT_COUNTS_UPDATE_URL, json=payload)
        return response
    except Exception as e:
        st.error(f"Performance update error: {str(e)}")
        return None

def get_performance_dashboard():
    """Get performance dashboard data"""
    try:
        response = requests.get(HIT_COUNTS_DASHBOARD_URL)
        return response
    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        return None

def upload_file(file, file_type):
    """Upload a file to the Django backend (which uploads to Supabase)"""
    try:
        files = {'file': (file.name, file, "text/csv")}
        data = {'file_type': file_type}
        response = requests.post(API_URL, files=files, data=data)
        
        if response.status_code in [200, 201]:
            return response.json()  # returns dict with 'filename', 'supabase_path', etc.
        else:
            # Return the error information so the calling function can handle it
            error_info = {
                'error': response.text,
                'status_code': response.status_code
            }
            return error_info
    except Exception as e:
        # Return the exception information so the calling function can handle it
        error_info = {
            'error': str(e),
            'status_code': 500
        }
        return error_info

def validate_csv_structure(file, file_type):
    """Validate CSV file structure based on file type"""
    try:
        import pandas as pd
        import io
        
        # Read the CSV file
        file.seek(0)  # Reset file pointer
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        file.seek(0)  # Reset file pointer again
        
        if file_type == 'rules':
            # Updated required fields for rules
            required_fields = [
                'rule_id', 'rule_name', 'rule_category', 'severity', 
                'pattern', 'action', 'description'
            ]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        elif file_type == 'traffic':
            # Updated required fields for traffic
            required_fields = [
                'timestamp', 'transaction_id', 'client_ip', 'http_status', 
                'request_method', 'request_uri', 'user_agent', 'rule_id', 
                'rule_message', 'matched_data', 'severity', 'attack_type', 
                'action', 'anomaly_score', 'phase'
            ]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, "File structure is valid"
        
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
    
def delete_file(filename, file_type):
    """Delete a file by filename and type"""
    try:
        data = {
            'filename': filename,
            'file_type': file_type
        }
        response = requests.delete(f"{API_URL}delete_by_name", json=data)
        return response
    except Exception as e:
        st.error(f"Deletion error: {str(e)}")
        return None

# FR04: False Positive Reduction API Functions
def detect_false_positives_api(session_id, detection_method, threshold):
    """Detect false positives in WAF rules"""
    data = {
        'session_id': session_id,
        'detection_method': detection_method,
        'false_positive_threshold': threshold
    }
    
    try:
        response = requests.post(FALSE_POSITIVE_DETECT_URL, json=data, timeout=30)
        return response
    except Exception as e:
        st.error(f"False positive detection error: {str(e)}")
        return None

def generate_whitelist_suggestions_api(false_positive_id, suggestion_types):
    """Generate whitelist suggestions for false positives"""
    data = {
        'false_positive_id': false_positive_id,
        'suggestion_types': suggestion_types
    }
    
    try:
        response = requests.post(WHITELIST_SUGGESTIONS_URL, json=data, timeout=30)
        return response
    except Exception as e:
        st.error(f"Whitelist suggestion error: {str(e)}")
        return None

def start_learning_mode_api(session_id, learning_duration, sample_size):
    """Start learning mode for traffic pattern analysis"""
    data = {
        'session_id': session_id,
        'learning_duration_hours': learning_duration,
        'traffic_sample_size': sample_size
    }
    
    try:
        response = requests.post(LEARNING_MODE_START_URL, json=data, timeout=30)
        return response
    except Exception as e:
        st.error(f"Learning mode start error: {str(e)}")
        return None

def get_learning_mode_status_api(learning_session_id):
    """Get learning mode status"""
    try:
        response = requests.get(f"{LEARNING_MODE_STATUS_URL}{learning_session_id}/")
        return response
    except Exception as e:
        st.error(f"Learning mode status error: {str(e)}")
        return None

def export_whitelist_csv_api(session_id, export_name, include_patterns):
    """Export whitelist suggestions as CSV"""
    data = {
        'session_id': session_id,
        'export_name': export_name,
        'include_patterns': include_patterns
    }
    
    try:
        response = requests.post(WHITELIST_EXPORT_URL, json=data, timeout=30)
        return response
    except Exception as e:
        st.error(f"Whitelist export error: {str(e)}")
        return None

def get_false_positive_dashboard_api(session_id=None):
    """Get false positive dashboard data"""
    params = {}
    if session_id:
        params['session_id'] = session_id
    
    try:
        response = requests.get(FALSE_POSITIVE_DASHBOARD_URL, params=params)
        return response
    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        return None
    
def deploy_optimization_api(session_id: int, rule_a_id: str, rule_b_id: str, suggestion_action: str, optimized_rule_syntax: str):
    """
    Sends the specific AI-generated optimization to the backend for approval or deployment.
    
    Args:
        session_id: The ID of the RuleAnalysisSession.
        rule_a_id, rule_b_id: The rule pair identifiers.
        suggestion_action: The recommended action (e.g., MERGE, REORDER).
        optimized_rule_syntax: The actual rule code to be applied.
    """
    data = {
        'session_id': session_id,
        'rule_a_id': rule_a_id,
        'rule_b_id': rule_b_id,
        'action': suggestion_action,
        'optimized_rule': optimized_rule_syntax,
    }
    
    try:
        # Use a longer timeout as this might trigger a complex configuration change on the backend
        response = requests.post(SUGGESTION_DEPLOYMENT_URL, json=data, timeout=90)
        return response
    except Exception as e:
        st.error(f"Deployment API error: {str(e)}")
        # Return a mock failed response structure
        return type('Response', (object,), {'status_code': 500, 'json': lambda: {'error': str(e)}})


def apply_suggestion_callback(session_id: int, rule_a_id: str, rule_b_id: str, suggestion: dict):
    """
    Streamlit callback function that executes the deployment API utility.
    """
    st.session_state['deployment_pending'] = True
    st.session_state['last_applied_id'] = f"SUG-{rule_a_id}-{rule_b_id}"
    st.session_state['apply_message'] = f"Attempting deployment for {rule_a_id} vs {rule_b_id}..."
    
    # Extract necessary fields from the full suggestion dictionary
    action = suggestion.get('action', 'REVIEW')
    optimized_syntax = suggestion.get('optimized_rule', '')
    
    # Call the deployment API
    response = deploy_optimization_api(
        session_id=session_id,
        rule_a_id=rule_a_id,
        rule_b_id=rule_b_id,
        suggestion_action=action,
        optimized_rule_syntax=optimized_syntax
    )
    
    if response and response.status_code == 200:
        st.session_state['deployment_pending'] = False
        st.session_state['apply_message'] = f"✅ Deployment success! Action: {action}"
    else:
        try:
            error_details = response.json().get('error', response.text)
        except:
            error_details = response.status_code
            
        st.session_state['deployment_pending'] = False
        st.session_state['apply_message'] = f"❌ Deployment failed (Status: {error_details}). Review logs."