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
    """Display rule analysis results with enhanced design including AI suggestions"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Analysis Results")
    
    # Handle different response formats
    if 'data' in results:
        data = results['data']
    else:
        data = results
    
    # Enhanced Metrics Display
    metrics_data = [
        {"label": "Total Rules", "value": data.get('total_rules', 0)},
        {"label": "Relationships", "value": data.get('total_relationships', 0)},
        {"label": "Shadowing", "value": data.get('shd_count', 0)},
        {"label": "Redundant", "value": data.get('rxd_count', 0)},
        {"label": "Correlated", "value": data.get('cor_count', 0)},
        {"label": "AI Enhanced", "value": "✅" if data.get('ai_available') else "❌"}
    ]
    
    display_enhanced_metrics(metrics_data)
    
    # Display AI suggestions if available
    if data.get('ai_available') and data.get('ai_suggestions'):
        display_ai_suggestions(data['ai_suggestions'])
    elif data.get('ai_available') is False:
        st.warning("🤖 AI enhancement was not available for this analysis")
        if data.get('ai_error'):
            st.error(f"AI Error: {data.get('ai_error')}")
    
    # Relationships
    relationships_data = data.get('relationships', {})
    
    if relationships_data and data.get('total_relationships', 0) > 0:
        st.subheader("🔍 Rule Relationships")
        
        # Handle both list and dict formats for relationships
        if isinstance(relationships_data, list):
            # Direct list of relationships
            for rel in relationships_data:
                display_relationship_item(rel)
        elif isinstance(relationships_data, dict):
            # Organized by relationship type
            for rel_type, rel_list in relationships_data.items():
                if rel_list and isinstance(rel_list, list):
                    st.markdown(f"**{get_relationship_name(rel_type)}**")
                    for rel in rel_list:
                        display_relationship_item(rel)
    
    # Recommendations
    recommendations = data.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Optimization Suggestions")
        for rec in recommendations:
            st.write(f"**{rec.get('type', 'Suggestion')}:** {rec.get('description', 'No description')}")
            st.write(f"*Impact:* {rec.get('impact', 'Not specified')}")
            st.markdown("---")
    
    # Show sample rules if available
    sample_rules = data.get('sample_rules', [])
    if sample_rules:
        with st.expander("📋 Sample Rules Analyzed"):
            st.write(f"First {len(sample_rules)} rules: {', '.join(map(str, sample_rules))}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_relationship_item(rel):
    """Display individual relationship item"""
    rel_type = rel.get('relationship_type', 'UNK')
    rule_a = rel.get('rule_a', 'N/A')
    rule_b = rel.get('rule_b', 'N/A')
    subsuming_rule = rel.get('subsuming_rule')
    subsumed_rule = rel.get('subsumed_rule')
    
    # Handle different relationship types
    if subsuming_rule and subsumed_rule:
        # Subsumption relationship
        title = f"🔄 Rule {subsuming_rule} subsumes Rule {subsumed_rule}"
    else:
        # Standard relationship
        title = f"🛡️ Rule {rule_a} → Rule {rule_b} ({rel_type})"
    
    with st.expander(title):
        col1, col2 = st.columns(2)
        with col1:
            confidence = rel.get('confidence')
            if confidence is not None:
                st.write(f"**Confidence:** {confidence:.3f}" if isinstance(confidence, (int, float)) else f"**Confidence:** {confidence}")
            
            jaccard = rel.get('jaccard')
            if jaccard is not None:
                st.write(f"**Jaccard:** {jaccard:.3f}")
                
        with col2:
            evidence_count = rel.get('evidence_count')
            if evidence_count is not None:
                st.write(f"**Evidence:** {evidence_count} matches")
            
            lift = rel.get('lift')
            if lift is not None:
                st.write(f"**Lift:** {lift:.2f}")
        
        description = rel.get('description', 'No description available')
        st.write(f"**Description:** {description}")

def display_ai_suggestions(ai_suggestions):
    """Display AI-generated optimization suggestions"""
    st.subheader("🤖 AI Optimization Suggestions")
    
    # Redundant rules suggestions
    if ai_suggestions.get('redundant'):
        st.markdown("#### 🔄 Redundant Rule Optimizations")
        for i, suggestion in enumerate(ai_suggestions['redundant']):
            with st.expander(f"Redundant Rules Optimization #{i+1}"):
                display_ai_suggestion_details(suggestion)
    
    # Shadowed rules suggestions
    if ai_suggestions.get('shadowed'):
        st.markdown("#### 🎯 Shadowed Rule Optimizations")
        for i, suggestion in enumerate(ai_suggestions['shadowed']):
            with st.expander(f"Shadowing Optimization #{i+1}"):
                display_ai_suggestion_details(suggestion)
    
    # Correlated rules suggestions  
    if ai_suggestions.get('correlated'):
        st.markdown("#### 🔗 Correlated Rule Optimizations")
        for i, suggestion in enumerate(ai_suggestions['correlated']):
            with st.expander(f"Correlation Optimization #{i+1}"):
                display_ai_suggestion_details(suggestion)

def display_ai_suggestion_details(suggestion):
    """Display details of an AI suggestion"""
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Action:** `{suggestion.get('action', 'N/A')}`")
        st.write(f"**Security Impact:** {suggestion.get('security_impact', 'N/A')}")
    with col2:
        st.write(f"**Performance:** {suggestion.get('performance_improvement', 'N/A')}")
    
    st.markdown("**Optimized Rule:**")
    st.code(suggestion.get('optimized_rule', 'No rule provided'), language='text')
    
    st.markdown("**Explanation:**")
    st.write(suggestion.get('explanation', 'No explanation provided'))
    
    st.markdown("**Implementation Steps:**")
    steps = suggestion.get('implementation_steps', [])
    if steps:
        for i, step in enumerate(steps, 1):
            st.write(f"{i}. {step}")

def get_relationship_name(rel_type):
    """Convert relationship type code to readable name"""
    names = {
        'SHD': 'Shadowing Relationships',
        'RXD': 'Redundant Rules', 
        'COR': 'Correlated Rules',
        'SUB': 'Subsumption Relationships',
        'GEN': 'Generalization Relationships'
    }
    return names.get(rel_type, rel_type)

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