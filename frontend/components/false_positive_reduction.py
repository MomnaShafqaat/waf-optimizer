import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *
from components.file_handling import render_file_selection

def render_false_positive_management():
    """FR04: False Positive Reduction Management with enhanced design"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Enhanced header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 20px; border-radius: 12px; margin-bottom: 24px;">
        <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;"> False Positive Reduction</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 8px 0 0 0; font-size: 16px;">Detect and reduce false positives to improve WAF accuracy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab layout for different FR04 features
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Detection", "🧠 Learning Mode", "📝 Suggestions", "📤 Export"])
    
    with tab1:
        render_false_positive_detection()
    
    with tab2:
        render_learning_mode()
    
    with tab3:
        render_whitelist_suggestions()
    
    with tab4:
        render_whitelist_export()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_false_positive_detection():
    """FR04-01: False Positive Detection with enhanced design"""
    st.markdown("""
    <div style="background: #242424; padding: 20px; border-radius: 12px; border: 1px solid #333333; margin-bottom: 24px;">
        <h3 style="color: #ffffff; margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">🔍 False Positive Detection</h3>
        <p style="color: #a3a3a3; margin: 0; font-size: 14px;">Analyze traffic patterns to identify rules blocking legitimate requests</p>
    </div>
    """, unsafe_allow_html=True)

    # Use the shared file selection UI to pick rules + logs files
    selected_rules, selected_logs = render_file_selection(key_prefix='fp_detect')

    if not selected_rules or not selected_logs:
        st.error("No files available for analysis")
        return

    # Attempt to create a real RuleAnalysisSession in the backend using uploaded file records
    selected_session = None
    try:
        # Get all uploaded files metadata from backend
        uploaded_files = get_files_data()
        # Find matching UploadedFile entries by filename
        rules_uploaded = next((f for f in uploaded_files if f.get('filename') == selected_rules['name'] and f.get('file_type') in ['rules']), None)
        logs_uploaded = next((f for f in uploaded_files if f.get('filename') == selected_logs['name'] and f.get('file_type') in ['traffic', 'logs']), None)

        if rules_uploaded and logs_uploaded:
            # Create a session on the backend and use its ID
            session_name = f"{selected_rules['name']} + {selected_logs['name']}"
            resp = create_analysis_session(session_name, rules_uploaded['id'], logs_uploaded['id'])
            if resp and resp.status_code in [200, 201]:
                session_data = resp.json()
                # API returns created session; ensure we have an id
                session_id = session_data.get('id') or session_data.get('pk') or session_data.get('session_id')
                if not session_id and isinstance(session_data, dict):
                    # Some serializers nest the object under keys
                    session_id = session_data.get('data', {}).get('session_id')

                if session_id:
                    selected_session = {
                        'id': session_id,
                        'name': session_name,
                        'rules_file': rules_uploaded,
                        'logs_file': logs_uploaded
                    }
        else:
            # If UploadedFile records are missing, leave selected_session None so user can be informed
            selected_session = None
    except Exception:
        selected_session = None

    # Configuration section
    st.markdown("### Configuration")
    col1, col2 = st.columns(2)
    with col1:
        # Use .get to avoid subscripting None or non-dict types
        session_name = None
        if isinstance(selected_session, dict):
            session_name = selected_session.get('name')

        if session_name:
            st.info(f"Selected session: {session_name}")
        else:
            st.warning("No backend analysis session available — upload selected files via File Management to enable detection.")
    with col2:
        detection_method = st.selectbox(
            "Detection Method:",
            options=["manual", "learning", "ai"],
            format_func=lambda x: x.title(),
            key="detection_method"
        )

    col1, col2 = st.columns(2)
    with col1:
        threshold = st.slider("False Positive Threshold:", 0.05, 0.5, 0.1, 0.05)
    with col2:
        st.markdown("""
        <div style="background: #242424; padding: 16px; border-radius: 8px; border: 1px solid #333333;">
            <div style="color: #10b981; font-size: 14px; font-weight: 500;">Current Threshold</div>
            <div style="color: #ffffff; font-size: 20px; font-weight: 600;">{:.1%}</div>
        </div>
        """.format(threshold), unsafe_allow_html=True)

    # Detection button with enhanced styling
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Detect False Positives", type="primary", key="detect_fp", width='stretch'):
            with st.spinner("Analyzing traffic patterns for false positives..."):
                # Ensure we have a backend session id; otherwise show an error
                if not selected_session or not selected_session.get('id'):
                    st.error("❌ Could not create analysis session on backend. Please upload selected files via File Management first.")
                    return

                # Call backend detection endpoint (backend expects a session id referencing stored UploadedFile objects)
                response = detect_false_positives_api(selected_session['id'], detection_method, threshold)

                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")

                    # Enhanced results display
                    data = result['data']
                    metrics_data = [
                        {"label": "Rules Analyzed", "value": data.get('total_rules_analyzed', 0)},
                        {"label": "High FP Rules", "value": data.get('high_false_positive_rules', 0)},
                        {"label": "Detection Method", "value": data.get('detection_method', '').title()},
                        {"label": "Threshold Used", "value": f"{data.get('threshold_used', threshold):.1%}"}
                    ]
                    # Simple metrics display (avoid external dependency)
                    cols = st.columns(len(metrics_data)) if metrics_data else []
                    for i, metric in enumerate(metrics_data):
                        with cols[i]:
                            st.metric(metric['label'], metric['value'])

                    # Show detected false positives with enhanced design
                    false_positives = data.get('false_positives_detected', [])
                    if false_positives:
                        st.markdown("### 🚨 Detected False Positives")
                        for fp in false_positives:
                            status_color = "#ef4444" if fp['false_positive_rate'] > 0.2 else "#f59e0b"
                            st.markdown(f"""
                            <div style="background: #242424; padding: 16px; border-radius: 8px; border: 1px solid #333333; margin: 8px 0;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="color: #ffffff; font-size: 16px; font-weight: 600;">Rule {fp['rule_id']}</div>
                                        <div style="color: #a3a3a3; font-size: 14px;">False Positive Rate: <span style="color: {status_color}; font-weight: 600;">{fp['false_positive_rate']:.1%}</span></div>
                                    </div>
                                    <div style="background: {status_color}; color: #ffffff; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 500;">
                                        {fp['status'].title()}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error("❌ False positive detection failed")

def render_learning_mode():
    """FR04-03: Learning Mode"""
    st.subheader("🧠 Learning Mode")
    st.write("Enable adaptive learning to understand normal traffic patterns")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.files_data:
            sessions = [f for f in st.session_state.files_data if f['file_type'] in ['rules', 'traffic']]
            if sessions:
                selected_session = st.selectbox(
                    "Select Session for Learning:",
                    options=[{"id": 1, "name": "Analysis Session 1"}],
                    format_func=lambda x: x['name'],
                    key="learning_session_select"
                )
            else:
                st.warning("No sessions available")
                selected_session = None
        else:
            st.error("No files available")
            selected_session = None
    
    with col2:
        learning_duration = st.slider("Learning Duration (hours):", 1, 72, 24)
    
    col1, col2 = st.columns(2)
    with col1:
        sample_size = st.number_input("Traffic Sample Size:", 100, 10000, 1000)
    with col2:
        st.write("")
    
    if st.button("🚀 Start Learning Mode", type="primary", key="start_learning"):
        if selected_session:
            with st.spinner("Starting learning mode analysis..."):
                response = start_learning_mode_api(selected_session['id'], learning_duration, sample_size)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    # Display learning results
                    data = result['data']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Learning Session ID", data['learning_session_id'])
                    with col2:
                        st.metric("Patterns Learned", data['patterns_learned'])
                    with col3:
                        st.metric("Accuracy Score", f"{data['accuracy_score']:.1%}")
                    with col4:
                        st.metric("Status", data['status'].title())
                    
                    # Store learning session for status checking
                    st.session_state.current_learning_session = data['learning_session_id']
                else:
                    st.error("❌ Learning mode start failed")
        else:
            st.warning("Please select a session for learning")
    
    # Show learning status if active
    if hasattr(st.session_state, 'current_learning_session'):
        st.subheader("📊 Learning Status")
        learning_session_id = st.session_state.current_learning_session
        
        if st.button("🔄 Refresh Learning Status", key="refresh_learning"):
            with st.spinner("Checking learning status..."):
                response = get_learning_mode_status_api(learning_session_id)
                
                if response and response.status_code == 200:
                    status_data = response.json()['data']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", status_data['status'].title())
                    with col2:
                        st.metric("Patterns Learned", status_data['patterns_learned'])
                    with col3:
                        st.metric("Accuracy", f"{status_data['accuracy_score']:.1%}")
                    
                    # Show learned patterns
                    if status_data.get('normal_traffic_patterns'):
                        with st.expander("View Learned Patterns"):
                            patterns = status_data['normal_traffic_patterns']
                            st.write("**User Agents:**")
                            for ua in patterns.get('user_agents', [])[:3]:
                                st.write(f"- {ua}")
                            st.write("**Common Paths:**")
                            for path in patterns.get('common_paths', [])[:5]:
                                st.write(f"- {path}")

def render_whitelist_suggestions():
    """FR04-02: Whitelist Suggestions"""
    st.subheader("📝 Whitelist Suggestions")
    st.write("Generate intelligent whitelist patterns to reduce false positives")
    
    # Fetch false positives from backend
    fp_response = get_false_positive_dashboard_api()
    false_positives = []
    if fp_response and fp_response.status_code == 200:
        fp_data = fp_response.json().get('data', {})
        false_positives = fp_data.get('recent_false_positives', [])

    if false_positives:
        col1, col2 = st.columns(2)
        with col1:
            selected_fp = st.selectbox(
                "Select False Positive:",
                options=false_positives,
                format_func=lambda x: f"Rule {x['rule_id']} ({x['false_positive_rate']:.1%} FP Rate)",
                key="fp_select"
            )
        with col2:
            suggestion_types = st.multiselect(
                "Suggestion Types:",
                options=["ip_whitelist", "path_whitelist", "user_agent_whitelist", "parameter_whitelist"],
                default=["ip_whitelist", "path_whitelist"],
                key="suggestion_types"
            )
        
        if st.button("💡 Generate Suggestions", type="primary", key="generate_suggestions"):
            if selected_fp and suggestion_types:
                with st.spinner("Generating whitelist suggestions..."):
                    response = generate_whitelist_suggestions_api(selected_fp['id'], suggestion_types)
                    
                    if response and response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                        
                        # Display suggestions
                        suggestions = result['data']['suggestions']
                        if suggestions:
                            st.subheader("🎯 Generated Suggestions")
                            for suggestion in suggestions:
                                with st.expander(f"{suggestion['type'].replace('_', ' ').title()} - {suggestion['estimated_reduction']:.0f}% Reduction"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Description:** {suggestion['description']}")
                                        st.write(f"**Risk Assessment:** {suggestion['risk_assessment'].title()}")
                                    with col2:
                                        st.write(f"**Estimated Reduction:** {suggestion['estimated_reduction']:.0f}%")
                                        st.write(f"**Type:** {suggestion['type'].replace('_', ' ').title()}")
                    else:
                        st.error("❌ Suggestion generation failed")
            else:
                st.warning("Please select a false positive and suggestion types")
    else:
        st.info("No false positives detected yet. Run detection first or check backend dashboard.")

def render_whitelist_export():
    """FR04-04: Whitelist Export"""
    st.subheader("📤 Export Whitelist")
    st.write("Export suggested whitelist patterns as CSV file")
    
    col1, col2 = st.columns(2)
    with col1:
        # Use same file selection UI to pick rules + logs and then create a backend session
        sel_rules, sel_logs = render_file_selection(key_prefix='fp_export')
        selected_session = None
        if sel_rules and sel_logs:
            uploaded_files = get_files_data()
            rules_uploaded = next((f for f in uploaded_files if f.get('filename') == sel_rules['name'] and f.get('file_type') in ['rules']), None)
            logs_uploaded = next((f for f in uploaded_files if f.get('filename') == sel_logs['name'] and f.get('file_type') in ['traffic', 'logs']), None)
            if rules_uploaded and logs_uploaded:
                session_name = f"{sel_rules['name']} + {sel_logs['name']}"
                resp = create_analysis_session(session_name, rules_uploaded['id'], logs_uploaded['id'])
                if resp and resp.status_code in [200, 201]:
                    session_obj = resp.json()
                    session_id = session_obj.get('id') or session_obj.get('pk') or session_obj.get('session_id')
                    selected_session = {'id': session_id, 'name': session_name}
                else:
                    selected_session = None
            else:
                st.warning("Please upload selected files via File Management before exporting.")
        else:
            st.info("Select files in the File Selection area to prepare an export.")
    
    with col2:
        export_name = st.text_input("Export Filename:", "waf_whitelist.csv", key="export_filename")
    
    col1, col2 = st.columns(2)
    with col1:
        include_patterns = st.multiselect(
            "Include Pattern Types:",
            options=["ip_whitelist", "path_whitelist", "user_agent_whitelist", "parameter_whitelist"],
            default=["ip_whitelist", "path_whitelist"],
            key="export_patterns"
        )
    with col2:
        st.write("")
    
    if st.button("📥 Export CSV", type="primary", key="export_csv"):
        if selected_session and include_patterns:
            with st.spinner("Generating CSV export..."):
                response = export_whitelist_csv_api(selected_session['id'], export_name, include_patterns)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    # Display export results
                    data = result['data']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Export ID", data['export_id'])
                    with col2:
                        st.metric("Total Patterns", data['total_patterns'])
                    with col3:
                        st.metric("File Size", f"{data['file_size_bytes']} bytes")
                    with col4:
                        st.metric("Status", "Completed")
                    
                    # Provide download link
                    st.info(f"📁 File saved as: {data['file_name']}")
                    st.markdown(f"**Download URL:** `{data['download_url']}`")
                else:
                    st.error("❌ CSV export failed")
        else:
            st.warning("Please select a session and pattern types")
