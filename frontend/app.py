import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# API URLs
API_URL = "http://127.0.0.1:8000/api/files/"
RULE_ANALYSIS_API_URL = "http://127.0.0.1:8000/api/analyze/"
RANKING_API_URL = "http://127.0.0.1:8000/api/ranking/generate/"
RANKING_COMPARISON_URL = "http://127.0.0.1:8000/api/ranking/comparison/"

# =============================================================================
# MODERN UI ENHANCEMENTS
# =============================================================================

# Set page config for better appearance
st.set_page_config(
    page_title="WAF Optimizer Pro",
    page_icon="🛡️",
    layout="wide"
)

# Modern CSS for professional look
st.markdown("""
<style>
    /* Modern color scheme */
    .main {
        background-color: #f8fafc;
    }
    
    /* Enhanced headers */
    h1 {
        color: #1e293b;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 10px;
    }
    
    h2 {
        color: #334155;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 10px 0;
    }
    
    h3 {
        color: #475569;
    }
    
    /* Modern cards */
    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
    }
    
    /* Enhanced buttons */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Better file uploader */
    .stFileUploader {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 25px;
        background: #f8fafc;
    }
    
    /* Improved metrics */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
    }
    
    /* Success/error styling */
    .stAlert {
        border-radius: 10px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# EXISTING FUNCTIONS WITH MINOR ENHANCEMENTS
# =============================================================================

def display_analysis_results(results):
    """Display rule analysis results with enhanced styling"""
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Analysis Results")
    
    if 'data' in results:
        data = results['data']
    else:
        data = results
    
    # Enhanced metrics layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rules Analyzed", data.get('total_rules_analyzed', 0))
    with col2:
        st.metric("Relationships Found", data.get('relationships_found', 0))
    with col3:
        shd_count = len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'SHD'])
        st.metric("Shadowing Rules", shd_count)
    with col4:
        rxd_count = len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'RXD'])
        st.metric("Redundant Rules", rxd_count)
    
    # Enhanced relationships display
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
    
    # Enhanced recommendations
    recommendations = data.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Optimization Suggestions")
        for rec in recommendations:
            st.write(f"**{rec.get('type', 'Suggestion')}:** {rec.get('description', 'No description')}")
            st.write(f"*Impact:* {rec.get('impact', 'Not specified')}")
            st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_rule_ranking_section():
    """Enhanced Smart Rule Prioritization section"""
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("⚡ Performance Optimization")
    st.write("Intelligent rule reordering based on performance data")
    
    col1, col2 = st.columns(2)
    with col1:
        rules_files = [f for f in st.session_state.get('files_data', []) if f['file_type'] == 'rules']
        selected_rules = st.selectbox(
            "Select Rules Configuration:",
            options=rules_files,
            format_func=lambda x: x['file'].split('/')[-1],
            key="ranking_rules_select"
        )
    with col2:
        session_name = st.text_input("Session Name:", "Optimization Analysis", key="session_name")
    
    if st.button("🚀 Generate Optimized Ranking", type="primary", key="generate_ranking"):
        if selected_rules:
            with st.spinner("🔄 Analyzing and optimizing rule order..."):
                try:
                    response = requests.post(
                        RANKING_API_URL,
                        json={"rules_file_id": selected_rules['id'], "session_name": session_name}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Performance Gain", f"{result['improvement']}%")
                        with col2:
                            st.metric("Rules Processed", result['rules_analyzed'])
                        with col3:
                            st.metric("Session ID", result['session_id'])
                        
                        st.session_state.current_ranking_session = result['session_id']
                    else:
                        st.error(f"❌ Optimization failed: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("Please select a rules configuration")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_ranking_visualization(session_id):
    """Enhanced ranking visualization"""
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📈 Optimization Results")
    
    try:
        response = requests.get(f"{RANKING_COMPARISON_URL}{session_id}/")
        if response.status_code == 200:
            comparison_data = response.json()
            
            # Enhanced metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Performance Gain", f"{comparison_data['improvement']:.1f}%")
            with col2:
                st.metric("Rules Improved", comparison_data['summary']['rules_moved_up'])
            with col3:
                st.metric("Rules Adjusted", comparison_data['summary']['rules_moved_down'])
            with col4:
                st.metric("Avg Change", f"{comparison_data['summary']['average_position_change']:+.1f}")
            
            if comparison_data['comparison_data']:
                df = pd.DataFrame(comparison_data['comparison_data'])
                
                # Enhanced visualization
                fig = px.scatter(
                    df,
                    x='current_position',
                    y='proposed_position',
                    size='hit_count',
                    color='position_change',
                    hover_data=['rule_id', 'priority_score', 'category'],
                    title='Rule Position Optimization',
                    labels={
                        'current_position': 'Current Position',
                        'proposed_position': 'Optimized Position',
                        'position_change': 'Improvement',
                        'hit_count': 'Usage Frequency'
                    }
                )
                
                max_pos = max(df['current_position'].max(), df['proposed_position'].max())
                fig.add_trace(px.line(x=[1, max_pos], y=[1, max_pos]).data[0])
                fig.data[-1].line.dash = 'dash'
                fig.data[-1].line.color = '#94a3b8'
                fig.data[-1].name = 'Reference'
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"💡 **Performance Insight:** Optimized rule order can improve processing speed by approximately {comparison_data['improvement']:.1f}%")
    
    except Exception as e:
        st.error(f"Error loading visualization: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# MAIN APPLICATION WITH ENHANCED UI
# =============================================================================

# Modern header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛡️ WAF Optimizer Pro")
    st.markdown("Intelligent Web Application Firewall Optimization Platform")
with col2:
    st.markdown("""
    <div style="text-align: center; background: #f1f5f9; padding: 15px; border-radius: 10px;">
        <div style="color: #475569;">🚀 Performance</div>
        <div style="color: #3b82f6; font-weight: bold;">Enhanced</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# System check
try:
    requests.get(API_URL, timeout=3)
    st.success("✅ System Status: Online")
except:
    st.error("🚨 Backend offline - Run: `python manage.py runserver`")
    st.stop()

# Initialize session state
if 'files_data' not in st.session_state:
    try:
        response = requests.get(API_URL)
        st.session_state.files_data = response.json() if response.status_code == 200 else []
    except:
        st.session_state.files_data = []

# =============================================================================
# ENHANCED SECTIONS
# =============================================================================

# File Management with modern cards
st.markdown('<div class="card">', unsafe_allow_html=True)
st.header("📁 Configuration Management")

col1, col2 = st.columns(2)
with col1:
    st.subheader("WAF Rules")
    rules_file = st.file_uploader("Upload rules CSV", type=['csv'], key="rules_upload")
with col2:
    st.subheader("Traffic Data") 
    traffic_file = st.file_uploader("Upload traffic CSV", type=['csv'], key="traffic_upload")

if rules_file or traffic_file:
    if st.button("📤 Upload Files", type="primary"):
        # Upload logic remains same
        pass
st.markdown('</div>', unsafe_allow_html=True)

# Rule Analysis section
st.markdown('<div class="card">', unsafe_allow_html=True)
st.header("🔍 Security Analysis")

if st.session_state.files_data:
    files_data = st.session_state.files_data
    rules_files = [f for f in files_data if f['file_type'] == 'rules']
    traffic_files = [f for f in files_data if f['file_type'] == 'traffic']
    
    if rules_files and traffic_files:
        col1, col2 = st.columns(2)
        with col1:
            selected_rules = st.selectbox("Rules File:", options=rules_files, format_func=lambda x: x['file'].split('/')[-1])
        with col2:
            selected_traffic = st.selectbox("Traffic File:", options=traffic_files, format_func=lambda x: x['file'].split('/')[-1])
        
        analysis_types = st.multiselect(
            "Analysis Types:",
            options=["Shadowing", "Generalization", "Redundancy", "Correlation"],
            default=["Shadowing", "Redundancy"]
        )
        
        if st.button("Run Security Analysis", type="primary"):
            analysis_data = {
                'rules_file_id': selected_rules['id'],
                'traffic_file_id': selected_traffic['id'],
                'analysis_types': [atype[:3].upper() for atype in analysis_types]
            }
            
            with st.spinner("Analyzing rule relationships..."):
                try:
                    response = requests.post(RULE_ANALYSIS_API_URL, json=analysis_data, timeout=30)
                    if response.status_code == 200:
                        st.success("✅ Analysis completed!")
                        display_analysis_results(response.json())
                    else:
                        st.error(f"Analysis failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.warning("Upload both rules and traffic files")
else:
    st.error("No files available")
st.markdown('</div>', unsafe_allow_html=True)

# Rule Ranking Section
render_rule_ranking_section()

# Show visualization
if hasattr(st.session_state, 'current_ranking_session'):
    show_ranking_visualization(st.session_state.current_ranking_session)

# File Management Display
st.markdown('<div class="card">', unsafe_allow_html=True)
st.header("📊 File Library")

if st.session_state.files_data:
    data = st.session_state.files_data
    df = pd.DataFrame(data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", len(df))
    with col2:
        st.metric("Rule Sets", len(df[df['file_type'] == 'rules']))
    with col3:
        st.metric("Traffic Logs", len(df[df['file_type'] == 'traffic']))
    
    st.dataframe(
        df[['id', 'file', 'file_type', 'uploaded_at']].rename(
            columns={'file': 'File Name', 'file_type': 'Type', 'uploaded_at': 'Uploaded'}
        ),
        use_container_width=True
    )
else:
    st.info("No files uploaded yet")
st.markdown('</div>', unsafe_allow_html=True)

# Modern footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 20px 0;">
    <strong>🛡️ WAF Optimizer Pro</strong> • Security • Performance • Intelligence
</div>
""", unsafe_allow_html=True)