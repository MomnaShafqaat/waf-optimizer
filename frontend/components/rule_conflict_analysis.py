import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.file_handling import render_file_selection

def render_rule_analysis():
    """Render rule analysis section using files from session state"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>🔍 Security Analysis</h2>", unsafe_allow_html=True)

    # Check if files are available in session state
    selected_rules = st.session_state.get('selected_rules_file')
    selected_logs = st.session_state.get('selected_logs_file')
    rules_content = st.session_state.get('rules_file_content')
    logs_content = st.session_state.get('logs_file_content')
    
    # Display current file selection status
    if selected_rules and selected_logs:
        st.success("✅ Files ready for analysis!")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Rules File:** {selected_rules['name']}")
        with col2:
            st.info(f"**Logs File:** {selected_logs['name']}")
    else:
        st.warning("⚠️ Please select files using the global file selection above before running analysis.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    if selected_rules and selected_logs and rules_content and logs_content:
        st.markdown("### Analysis Configuration")
        
        analysis_types = st.multiselect(
            "Select Analysis Types:",
            options=["Shadowing", "Generalization", "Redundancy", "Correlation"],
            default=["Shadowing", "Redundancy"],
            help="Choose which types of rule analysis to perform"
        )
        
        # Map full names to abbreviations
        analysis_map = {
            "Shadowing": "SHD",
            "Generalization": "GEN", 
            "Redundancy": "RXD",
            "Correlation": "COR"
        }
        
        if st.button("Run Security Analysis", type="primary", width='stretch'):
            with st.spinner("Analyzing rule relationships..."):
                # Convert full names to abbreviations before sending
                analysis_types_abbr = [analysis_map[atype] for atype in analysis_types]
                
                # Prefer session-based analysis: create backend session from uploaded files and trigger analysis
                uploaded_files = get_files_data()
                rules_uploaded = next((f for f in uploaded_files if f.get('filename') == selected_rules['name'] and f.get('file_type') in ['rules']), None)
                logs_uploaded = next((f for f in uploaded_files if f.get('filename') == selected_logs['name'] and f.get('file_type') in ['traffic', 'logs']), None)

                if not rules_uploaded or not logs_uploaded:
                    st.error("❌ UploadedFile metadata not found for selected files. Please upload them via File Management first.")
                else:
                    # create backend session
                    session_name = f"{selected_rules['name']} + {selected_logs['name']}"
                    create_resp = create_analysis_session(session_name, rules_uploaded['id'], logs_uploaded['id'])
                    if not create_resp or create_resp.status_code not in [200, 201]:
                        st.error("❌ Failed to create analysis session on backend")
                    else:
                        sess_obj = create_resp.json()
                        session_id = sess_obj.get('id') or sess_obj.get('pk') or sess_obj.get('session_id')
                        if not session_id:
                            st.error("❌ Backend did not return a session id")
                        else:
                            # trigger analysis by session
                            response = analyze_rules_by_session(session_id, analysis_types_abbr)
                            if response and response.status_code == 200:
                                st.success("✅ Analysis completed!")
                                display_analysis_results(response.json())
                            else:
                                st.error("❌ Analysis failed - check backend connection or logs")
        else:
            st.info("👆 Click the button above to start the security analysis with the selected files and analysis types.")
    else:
        st.error("❌ Files are selected but content failed to load. Please try selecting files again.")
    
    st.markdown('</div>', unsafe_allow_html=True)


def display_analysis_results(results):
    """Display rule analysis results with enhanced design"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Analysis Results")
    
    if 'data' in results:
        data = results['data']
    else:
        data = results
    
    # Enhanced Metrics Display
    metrics_data = [
        {"label": "Rules Analyzed", "value": data.get('total_rules_analyzed', 0)},
        {"label": "Relationships Found", "value": data.get('relationships_found', 0)},
        {"label": "Shadowing Rules", "value": len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'SHD'])},
        {"label": "Redundant Rules", "value": len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'RXD'])}
    ]
    
    display_enhanced_metrics(metrics_data)
    
    # Relationships
    relationships = data.get('relationships', [])
    if relationships:
        st.subheader("🔍 Rule Relationships")
        for rel in relationships:
            with st.expander(f"🛡️ Rule {rel.get('rule_a')} → Rule {rel.get('rule_b')} ({rel.get('relationship_type')})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Confidence:** {rel.get('confidence', 'N/A')}")
                with col2:
                    st.write(f"**Evidence:** {rel.get('evidence_count', 'N/A')} matches")
                st.write(f"**Description:** {rel.get('description', 'No description')}")
    
    # Recommendations
    recommendations = data.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Optimization Suggestions")
        for rec in recommendations:
            st.write(f"**{rec.get('type', 'Suggestion')}:** {rec.get('description', 'No description')}")
            st.write(f"*Impact:* {rec.get('impact', 'Not specified')}")
            st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_enhanced_metrics(metrics_data):
    """Display metrics with enhanced dark theme design"""
    cols = st.columns(len(metrics_data))
    
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card" style="
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 12px;
                padding: 16px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                transition: transform 0.2s;
            ">
                <div class="metric-value" style="
                    font-size: 26px;
                    font-weight: bold;
                    color: #00C853;
                    margin-bottom: 6px;
                ">{metric['value']}</div>
                <div class="metric-label" style="
                    font-size: 14px;
                    color: #BBBBBB;
                    text-transform: uppercase;
                ">{metric['label']}</div>
            </div>
            """, unsafe_allow_html=True)