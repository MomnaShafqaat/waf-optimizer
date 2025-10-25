# frontend/components.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

def apply_custom_styles():
    """Apply modern CSS styles"""
    st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        h1 { color: #1e293b; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }
        h2 { color: #334155; background: linear-gradient(90deg, #3b82f6, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 10px 0; }
        .card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin: 15px 0; }
        .stButton button { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600; }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4); }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the main header"""
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

def render_file_management():
    """Render file management section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📁 Configuration Management")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("WAF Rules")
        st.info("""
        **Required fields:** id, category, parameter, operator, value, phase, action, priority
        """)
        rules_file = st.file_uploader("Upload rules CSV", type=['csv'], key="rules_upload")
    with col2:
        st.subheader("Traffic Data") 
        st.info("""
        **Required fields:** timestamp, src_ip, method, url
        """)
        traffic_file = st.file_uploader("Upload traffic CSV", type=['csv'], key="traffic_upload")

    if rules_file or traffic_file:
        if st.button("📤 Upload Files", type="primary"):
            upload_success = True
            uploaded_files = []
            
            # Upload rules file if provided
            if rules_file:
                with st.spinner(f"Uploading {rules_file.name}..."):
                    # Validate file structure
                    is_valid, message = validate_csv_structure(rules_file, 'rules')
                    if not is_valid:
                        st.error(f"❌ Rules file validation failed: {message}")
                        upload_success = False
                    else:
                        # Upload the file
                        response = upload_file(rules_file, 'rules')
                        if response and response.status_code in [200, 201]:
                            st.success(f"✅ Successfully uploaded {rules_file.name}")
                            uploaded_files.append(f"{rules_file.name} (Rules)")
                        else:
                            st.error(f"❌ Failed to upload {rules_file.name}")
                            upload_success = False
            
            # Upload traffic file if provided
            if traffic_file:
                with st.spinner(f"Uploading {traffic_file.name}..."):
                    # Validate file structure
                    is_valid, message = validate_csv_structure(traffic_file, 'traffic')
                    if not is_valid:
                        st.error(f"❌ Traffic file validation failed: {message}")
                        upload_success = False
                    else:
                        # Upload the file
                        response = upload_file(traffic_file, 'traffic')
                        if response and response.status_code in [200, 201]:
                            st.success(f"✅ Successfully uploaded {traffic_file.name}")
                            uploaded_files.append(f"{traffic_file.name} (Traffic)")
                        else:
                            st.error(f"❌ Failed to upload {traffic_file.name}")
                            upload_success = False
            
            # Show overall result
            if upload_success and uploaded_files:
                st.success(f"🎉 All files uploaded successfully: {', '.join(uploaded_files)}")
                # Refresh the files data
                st.session_state.files_data = get_files_data()
                st.rerun()
            elif not upload_success:
                st.error("❌ Some files failed to upload. Please check the errors above.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_rule_analysis():
    """Render rule analysis section"""
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
            
            # Map full names to abbreviations
            analysis_map = {
                "Shadowing": "SHD",
                "Generalization": "GEN", 
                "Redundancy": "RXD",
                "Correlation": "COR"
            }
            
            if st.button("Run Security Analysis", type="primary"):
                with st.spinner("Analyzing rule relationships..."):
                    # Convert full names to abbreviations before sending
                    analysis_types_abbr = [analysis_map[atype] for atype in analysis_types]
                    response = analyze_rules(selected_rules['id'], selected_traffic['id'], analysis_types_abbr)
                    
                    if response and response.status_code == 200:
                        st.success("✅ Analysis completed!")
                        display_analysis_results(response.json())
                    else:
                        st.error("Analysis failed - check backend connection")
        else:
            st.warning("Upload both rules and traffic files")
    else:
        st.error("No files available")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
def display_analysis_results(results):
    """Display rule analysis results"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Analysis Results")
    
    if 'data' in results:
        data = results['data']
    else:
        data = results
    
    # Metrics
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

def render_performance_profiling():
    """FR03: Performance Profiling Section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Performance Profiling")
    st.write("Analyze rule efficiency and identify optimization opportunities")
    
    col1, col2 = st.columns(2)
    with col1:
        traffic_files = [f for f in st.session_state.get('files_data', []) if f['file_type'] == 'traffic']
        selected_traffic = st.selectbox(
            "Select Traffic Data:",
            options=traffic_files,
            format_func=lambda x: x['file'].split('/')[-1],
            key="performance_traffic_select"
        )
    with col2:
        snapshot_name = st.text_input("Analysis Name:", "Performance Analysis", key="snapshot_name")
    
    if st.button("🔍 Analyze Rule Performance", type="primary", key="analyze_performance"):
        if selected_traffic:
            with st.spinner("🔄 Analyzing rule performance patterns..."):
                response = update_performance_data()
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    # Show summary
                    summary = result['summary']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Requests", summary['total_requests'])
                    with col2:
                        st.metric("Rules Triggered", summary['rules_triggered'])
                    with col3:
                        st.metric("Hits Updated", summary['hits_updated'])
                    with col4:
                        st.metric("Metrics Calculated", summary['metrics_calculated'])
                    
                    # Show flagged rules
                    flagged = result.get('flagged_rules', {})
                    if flagged:
                        st.subheader("🚩 Flagged Rules")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if flagged.get('rarely_used'):
                                st.metric("Rarely Used", len(flagged['rarely_used']), delta="Optimize")
                        with col2:
                            if flagged.get('redundant'):
                                st.metric("Redundant", len(flagged['redundant']), delta="Review")
                        with col3:
                            if flagged.get('high_performance'):
                                st.metric("High Performers", len(flagged['high_performance']), delta="Excellent")
                        
                        # Show details of flagged rules
                        with st.expander("View Flagged Rule Details"):
                            for category, rules in flagged.items():
                                if rules:
                                    st.write(f"**{category.upper().replace('_', ' ')}:**")
                                    for rule in rules:
                                        st.write(f"- {rule['rule_id']}: {rule.get('reason', 'No reason provided')}")
                    
                    # Show performance metrics
                    metrics = result.get('performance_metrics', {})
                    if metrics:
                        st.subheader("📈 Performance Metrics")
                        metrics_df = pd.DataFrame.from_dict(metrics, orient='index').reset_index()
                        metrics_df.columns = ['Rule ID', 'Match Frequency', 'Effectiveness Ratio', 'Hit Count']
                        metrics_df['Match Frequency'] = metrics_df['Match Frequency'].apply(lambda x: f"{x:.2%}")
                        metrics_df['Effectiveness Ratio'] = metrics_df['Effectiveness Ratio'].apply(lambda x: f"{x:.1%}")
                        st.dataframe(metrics_df, use_container_width=True)
                        
                else:
                    st.error("❌ Performance analysis failed")
        else:
            st.warning("Please select traffic data for analysis")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_performance_dashboard():
    """Show performance dashboard"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📈 Performance Dashboard")
    
    response = get_performance_dashboard()
    if response and response.status_code == 200:
        dashboard_data = response.json()
        
        # Overview metrics
        metrics = dashboard_data['summary']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rules", metrics['total_rules_tracked'])
        with col2:
            st.metric("Total Hits", metrics['total_hits_recorded'])
        with col3:
            st.metric("Avg Hits/Rule", f"{metrics['average_hits_per_rule']:.1f}")
        with col4:
            flagged = metrics.get('flagged_rules_summary', {})
            st.metric("Optimization Opportunities", flagged.get('rarely_used', 0) + flagged.get('redundant', 0))
        
        # Top performers
        top_rules = dashboard_data.get('top_performing_rules', [])
        if top_rules:
            st.subheader("🏆 Top Performing Rules")
            perf_df = pd.DataFrame(top_rules)
            st.dataframe(perf_df, use_container_width=True)
        
        # All rules with metrics
        all_rules = dashboard_data.get('all_rules', [])
        if all_rules:
            with st.expander("View All Rule Performance Data"):
                rules_df = pd.DataFrame(all_rules)
                # Format percentages for better display
                if 'match_frequency' in rules_df.columns:
                    rules_df['match_frequency'] = rules_df['match_frequency'].apply(
                        lambda x: f"{float(x):.2%}" if x else "0%"
                    )
                if 'effectiveness_ratio' in rules_df.columns:
                    rules_df['effectiveness_ratio'] = rules_df['effectiveness_ratio'].apply(
                        lambda x: f"{float(x):.1%}" if x else "0%"
                    )
                st.dataframe(rules_df, use_container_width=True)
    else:
        st.error("Error loading dashboard")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_rule_ranking():
    """Rule Ranking Section"""
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
                response = generate_rule_ranking(selected_rules['id'], session_name)
                
                if response and response.status_code == 200:
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
                    st.error("❌ Optimization failed")
        else:
            st.warning("Please select a rules configuration")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_ranking_visualization(session_id):
    """Enhanced ranking visualization"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📈 Optimization Results")
    
    try:
        response = get_ranking_comparison(session_id)
        if response and response.status_code == 200:
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
                
                # Add detailed table view of reordered rules
                st.subheader("📋 Detailed Rule Reordering")
                
                # Create display dataframe with better formatting
                display_df = df.copy()
                display_df = display_df.sort_values('proposed_position')
                display_df['Position Change'] = display_df['position_change'].apply(
                    lambda x: f"↑ {abs(x)}" if x > 0 else (f"↓ {abs(x)}" if x < 0 else "→ 0")
                )
                display_df['Status'] = display_df.apply(
                    lambda row: '🔥 High Performance' if row.get('is_high_performance', False) 
                    else ('⚠️ Rarely Used' if row.get('is_rarely_used', False) else '✓ Normal'),
                    axis=1
                )
                
                # Select and rename columns for display
                columns_to_show = {
                    'rule_id': 'Rule ID',
                    'current_position': 'Original Position',
                    'proposed_position': 'New Position',
                    'Position Change': 'Change',
                    'hit_count': 'Hit Count',
                    'priority_score': 'Priority Score',
                    'category': 'Category',
                    'Status': 'Status'
                }
                
                # Filter to only include columns that exist
                existing_columns = [col for col in columns_to_show.keys() if col in display_df.columns]
                table_df = display_df[existing_columns].rename(columns=columns_to_show)
                
                st.dataframe(
                    table_df,
                    use_container_width=True,
                    height=400
                )
                
                # Add download button for the ranking
                csv = table_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Optimized Rule Order",
                    data=csv,
                    file_name=f"optimized_rules_session_{session_id}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"Error loading visualization: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_file_library():
    """Render file library section"""
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

def render_file_deletion():
    """Render file deletion section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Delete Files")

    if st.session_state.files_data:
        data = st.session_state.files_data
        df = pd.DataFrame(data)

        # Dropdown options: show ID, filename, and file type
        file_options = [
            f"ID {f['id']}: {f['file'].split('/')[-1]} ({f['file_type']})"
            for f in data
        ]

        selected_file = st.selectbox("Select file to delete:", ["Choose a file..."] + file_options)

        if selected_file != "Choose a file...":
            if st.button("🗑️ Delete File", type="secondary"):
                file_id = int(selected_file.split(":")[0].replace("ID ", "").strip())

                try:
                    response = delete_file(file_id)
                    if response.status_code == 204:
                        st.success(f"✅ File '{selected_file}' deleted successfully!")
                        # Refresh files
                        st.session_state.files_data = get_files_data()
                        st.rerun()
                    else:
                        st.error(f"❌ Delete failed: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"🚨 Error deleting file: {e}")
        else:
            st.info("Please select a file to delete.")
    else:
        st.info("No files available for deletion.")

    st.markdown('</div>', unsafe_allow_html=True)