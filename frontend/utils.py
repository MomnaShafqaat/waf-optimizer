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

def check_backend_status():
    """Check if backend is online"""
    try:
        response = requests.get(API_URL, timeout=3)
        return True
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
        return None

def generate_rule_ranking(rules_file_id, session_name):
    """Generate optimized rule ranking"""
    data = {"rules_file_id": rules_file_id, "session_name": session_name}
    
    try:
        response = requests.post(RANKING_API_URL, json=data)
        return response
    except Exception as e:
        return None

def get_ranking_comparison(session_id):
    """Get ranking comparison data"""
    try:
        response = requests.get(f"{RANKING_COMPARISON_URL}{session_id}/")
        return response
    except Exception as e:
        return None

def update_performance_data():
    """Update performance data (FR03)"""
    try:
        response = requests.post(HIT_COUNTS_UPDATE_URL, json={})
        return response
    except Exception as e:
        return None

def get_performance_dashboard():
    """Get performance dashboard data"""
    try:
        response = requests.get(HIT_COUNTS_DASHBOARD_URL)
        return response
    except Exception as e:
        return None