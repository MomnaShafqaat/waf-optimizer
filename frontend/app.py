# frontend/app.py
import streamlit as st
from components.false_positive_reduction import *
from components.file_handling import *
from components.rule_conflict_analysis import *
from components.rule_ranking import *
from components.threshold_tuning import *
from styles import * 
from utils import *

# Ensure project root is on sys.path so imports like `supabase_client` work
import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Some helper components are defined in the flat `components.py` file
# (not inside the `components` package). Try to import `render_threshold_tuning`
# from the package first, then fall back to loading the top-level `components.py`.
try:
    # Try package-based import (preferred)
    from components.threshold_tuning import render_threshold_tuning
except Exception:
    try:
        # Fallback: dynamic load of the file `frontend/components.py`
        import importlib.util, os, sys
        comp_path = os.path.join(os.path.dirname(__file__), 'components.py')
        if os.path.exists(comp_path):
            spec = importlib.util.spec_from_file_location('flat_components', comp_path)
            flat_components = importlib.util.module_from_spec(spec)
            sys.modules['flat_components'] = flat_components
            spec.loader.exec_module(flat_components)
            render_threshold_tuning = getattr(flat_components, 'render_threshold_tuning', None)
    except Exception:
        render_threshold_tuning = None

# -----------------------------
# 1️⃣ Page Config
# -----------------------------
st.set_page_config(
    page_title="WAF Optimizer Pro",
    page_icon="🛡️",
    layout="wide"
)

# -----------------------------
# 2️⃣ Apply Styles
# -----------------------------
apply_custom_styles()

# -----------------------------
# 3️⃣ Render Header
# -----------------------------
render_header()

# -----------------------------
# 4️⃣ System Check
# -----------------------------
if check_backend_status():
    st.success("✅ System Status: Online")
else:
    st.error("🚨 Backend offline - Run: `python manage.py runserver`")
    st.stop()

# -----------------------------
# 5️⃣ Initialize Session State
# -----------------------------
if 'files_data' not in st.session_state:
    st.session_state.files_data = get_files_data()

# -----------------------------
# 6️⃣ Render Dashboard / Sections
# -----------------------------
# Landing page or main dashboard (optional)
# render_main_dashboard()  

# File management & library
render_file_library()
render_file_management()
render_file_selection()

# Analysis sections
render_rule_analysis()
render_performance_profiling()
render_performance_dashboard()
render_rule_ranking()
render_false_positive_management()  # FR04 False Positive Reduction
if callable(globals().get('render_threshold_tuning')):
    render_threshold_tuning()
else:
    # If not available, try to render threshold tuning from package
    try:
        from components.threshold_tuning import render_threshold_tuning as _rt
        _rt()
    except Exception:
        pass

# Show ranking visualization if available
if hasattr(st.session_state, 'current_ranking_session'):
    show_ranking_visualization(st.session_state.current_ranking_session)

# File deletion
render_file_deletion()

# -----------------------------
# 7️⃣ Footer
# -----------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a1a, #242424); padding: 32px 0; margin-top: 48px; border-radius: 16px 16px 0 0;">
    <div style="max-width: 1200px; margin: 0 auto; padding: 0 32px; text-align: center;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 16px; margin-bottom: 16px;">
            <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 8px 16px; border-radius: 8px;">
                <span style="color: #ffffff; font-weight: 600; font-size: 16px;">🛡️ WAF Optimizer Pro</span>
            </div>
        </div>
        <div style="color: #a3a3a3; font-size: 14px;">
            <span style="color: #10b981;">Security</span> • 
            <span style="color: #3b82f6;">Performance</span> • 
            <span style="color: #7c3aed;">Intelligence</span>
        </div>
        <div style="color: #737373; font-size: 12px; margin-top: 8px;">
            Intelligent Web Application Firewall Optimization Platform
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
