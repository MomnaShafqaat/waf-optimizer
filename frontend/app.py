# frontend/app.py
import streamlit as st
from components import *
from utils import *

# Set page config
st.set_page_config(
    page_title="WAF Optimizer Pro",
    page_icon="🛡️",
    layout="wide"
)

# Apply styles
apply_custom_styles()

# Render header
render_header()

# System check
if check_backend_status():
    st.success("✅ System Status: Online")
else:
    st.error("🚨 Backend offline - Run: `python manage.py runserver`")
    st.stop()

# Initialize session state
if 'files_data' not in st.session_state:
    st.session_state.files_data = get_files_data()

# Render all sections
render_file_management()
render_rule_analysis()
render_performance_profiling()
render_performance_dashboard()
render_rule_ranking()

# Show ranking visualization if available
if hasattr(st.session_state, 'current_ranking_session'):
    show_ranking_visualization(st.session_state.current_ranking_session)

render_file_library()
render_file_deletion()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 20px 0;">
    <strong>🛡️ WAF Optimizer Pro</strong> • Security • Performance • Intelligence
</div>
""", unsafe_allow_html=True)