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

# --- NEW: Render Main Dashboard elements here if you want a landing page experience ---
# For example, you could show this dashboard first, then other sections as tabs or based on user interaction
# render_main_dashboard()
# --- End New Section ---

# Render all sections
render_file_management()
render_rule_analysis()
render_performance_profiling()
render_performance_dashboard()
render_rule_ranking()
render_false_positive_management()  # NEW: FR04 False Positive Reduction

# Show ranking visualization if available
if hasattr(st.session_state, 'current_ranking_session'):
    show_ranking_visualization(st.session_state.current_ranking_session)

render_file_library()

# Footer with enhanced design
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
# # frontend/app.py
# import streamlit as st
# from components import *
# from utils import *

# # Set page config
# st.set_page_config(
#     page_title="WAF Optimizer Pro",
#     page_icon="🛡️",
#     layout="wide"
# )

# # Apply styles
# apply_custom_styles()

# # Render header
# render_header()

# # System check
# if check_backend_status():
#     st.success("✅ System Status: Online")
# else:
#     st.error("🚨 Backend offline - Run: `python manage.py runserver`")
#     st.stop()

# # Initialize session state
# if 'files_data' not in st.session_state:
#     st.session_state.files_data = get_files_data()

# # Render all sections
# render_file_management()
# render_rule_analysis()
# render_performance_profiling()
# render_performance_dashboard()
# render_rule_ranking()
# render_false_positive_management()  # NEW: FR04 False Positive Reduction

# # Show ranking visualization if available
# if hasattr(st.session_state, 'current_ranking_session'):
#     show_ranking_visualization(st.session_state.current_ranking_session)

# render_file_library()

# # Footer with enhanced design
# st.markdown("""
# <div style="background: linear-gradient(135deg, #1a1a1a, #242424); padding: 32px 0; margin-top: 48px; border-radius: 16px 16px 0 0;">
#     <div style="max-width: 1200px; margin: 0 auto; padding: 0 32px; text-align: center;">
#         <div style="display: flex; justify-content: center; align-items: center; gap: 16px; margin-bottom: 16px;">
#             <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 8px 16px; border-radius: 8px;">
#                 <span style="color: #ffffff; font-weight: 600; font-size: 16px;">🛡️ WAF Optimizer Pro</span>
#             </div>
#         </div>
#         <div style="color: #a3a3a3; font-size: 14px;">
#             <span style="color: #10b981;">Security</span> • 
#             <span style="color: #3b82f6;">Performance</span> • 
#             <span style="color: #7c3aed;">Intelligence</span>
#         </div>
#         <div style="color: #737373; font-size: 12px; margin-top: 8px;">
#             Intelligent Web Application Firewall Optimization Platform
#         </div>
#     </div>
# </div>
# """, unsafe_allow_html=True)