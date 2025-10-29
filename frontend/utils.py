# frontend/utils.py
import requests
import streamlit as st

# API URLs
API_URL = "http://127.0.0.1:8000/api/files/"
RULE_ANALYSIS_API_URL = "http://127.0.0.1:8000/api/analyze/"
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

def check_backend_status():
    """Check if backend is online"""
    try:
        response = requests.get(API_URL, timeout=3)
        return response.status_code == 200
    except:
        return False

def get_files_data():
    """Get uploaded files data"""
    try:
        response = requests.get(API_URL)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def analyze_rules(rules_file_id, traffic_file_id, analysis_types):
    """Run rule analysis"""
    analysis_data = {
        'rules_file_id': rules_file_id,
        'traffic_file_id': traffic_file_id,
        'analysis_types': [atype[:3].upper() for atype in analysis_types]
    }
    
    try:
        response = requests.post(RULE_ANALYSIS_API_URL, json=analysis_data, timeout=30)
        return response
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def generate_rule_ranking(rules_file_id, session_name):
    """Generate optimized rule ranking"""
    data = {"rules_file_id": rules_file_id, "session_name": session_name}
    
    try:
        response = requests.post(RANKING_API_URL, json=data)
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
        response = requests.post(HIT_COUNTS_UPDATE_URL, json={})
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
    """Upload a file to the backend"""
    try:
        files = {'file': file}
        data = {'file_type': file_type}
        response = requests.post(API_URL, files=files, data=data)
        return response
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

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
    
def delete_file(file_id):
    """Delete a file by ID"""
    delete_url = f"{API_URL}delete/{file_id}/"
    try:
        response = requests.delete(delete_url)
        return response
    except Exception as e:
        st.error(f"Deletion error: {str(e)}")

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