import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

# frontend/components/threshold_tuning.py
def threshold_tuning_module():
    """Threshold Tuning Module for FR04 - False Positive Reduction"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 20px; border-radius: 12px; margin-bottom: 24px;">
        <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">🎯 Threshold Tuning</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 8px 0 0 0; font-size: 16px;">
            Optimize WAF anomaly score thresholds to reduce false positives
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main functionality
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Run Threshold Analysis")
        st.write("Analyze uploaded traffic logs to find optimal anomaly score threshold")
        
        if st.button("🚀 Run Threshold Tuning", type="primary", use_container_width=True):
            with st.spinner("Analyzing traffic patterns and finding optimal threshold..."):
                try:
                    response = requests.post('http://127.0.0.1:8000/api/threshold_tuning/')
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Threshold tuning completed successfully!")
                        
                        # Display results
                        display_threshold_results(result)
                        
                    else:
                        error_msg = response.json().get('error', 'Unknown error')
                        st.error(f"❌ Analysis failed: {error_msg}")
                        
                except Exception as e:
                    st.error(f"🚨 Connection error: {str(e)}")
                    st.info("💡 Make sure Django backend is running on port 8000")
    
    with col2:
        st.markdown("### ⚙️ Settings")
        st.info("""
        **Input Requirements:**
        - CSV files in `uploads/` folder
        - Must contain `anomaly_score` column
        - Must contain `action` column
        """)
        
        # Quick actions
        if st.button("🔄 Check Uploads Folder", type="secondary"):
            check_uploads_folder()
    
    # Display existing suggestions
    display_existing_suggestions()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_threshold_results(result):
    """Display threshold tuning results"""
    st.markdown("---")
    st.markdown("### 📈 Analysis Results")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Optimal Threshold", f"{result['best_threshold']:.2f}")
    with col2:
        st.metric("Accuracy", f"{result['accuracy']:.1%}")
    with col3:
        st.metric("Records Tested", result['records_tested'])
    with col4:
        st.metric("File Used", result['file_used'][:15] + "...")
    
    # Detailed explanation
    with st.expander("📋 View Detailed Analysis"):
        st.write(f"**File Analyzed:** {result['file_used']}")
        st.write(f"**Optimal Threshold:** {result['best_threshold']}")
        st.write(f"**Achieved Accuracy:** {result['accuracy']:.1%}")
        st.write(f"**Suggestion ID:** {result['saved_id']}")
        
        st.info("""
        **Interpretation:**
        - Threshold represents the minimum anomaly score to block a request
        - Higher threshold = fewer false positives but might miss some attacks
        - Lower threshold = better attack detection but more false positives
        """)

def render_threshold_tuning():
    """Threshold Tuning Module for FR04 - False Positive Reduction"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 20px; border-radius: 12px; margin-bottom: 24px;">
        <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">🎯 Threshold Tuning</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 8px 0 0 0; font-size: 16px;">
            Optimize WAF anomaly score thresholds to reduce false positives
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main functionality
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Run Threshold Analysis")
        st.write("Analyze uploaded traffic logs to find optimal anomaly score threshold")
        
        if st.button("🚀 Run Threshold Tuning", type="primary", use_container_width=True):
            with st.spinner("Analyzing traffic patterns and finding optimal threshold..."):
                try:
                    # CHANGED: Using GET instead of POST to avoid CSRF
                    response = requests.get('http://127.0.0.1:8000/api/threshold_tuning/', timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Threshold tuning completed successfully!")
                        display_threshold_results(result)
                    else:
                        st.error(f"❌ Analysis failed: {response.status_code}")
                        st.write(f"**Error:** {response.text[:200]}...")
                        
                except Exception as e:
                    st.error(f"🚨 Connection error: {str(e)}")
    
    with col2:
        st.markdown("### ⚙️ Settings")
        st.info("""
        **API Endpoint:**
        `GET http://127.0.0.1:8000/api/threshold_tuning/`
        
        """)
    
    # Display existing suggestions
    display_existing_suggestions()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_existing_suggestions():
    """Display existing threshold suggestions"""
    st.markdown("---")
    st.markdown("### 💾 Saved Suggestions")
    
    try:
        response = requests.get('http://127.0.0.1:8000/api/threshold_suggestions/')
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            
            if suggestions:
                df = pd.DataFrame(suggestions)
                
                # Format the dataframe for better display
                display_df = df[['id', 'value', 'approved', 'applied', 'created_at']].copy()
                display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['status'] = display_df.apply(
                    lambda row: '✅ Approved' if row['approved'] else '⏳ Pending', 
                    axis=1
                )
                
                st.dataframe(
                    display_df.rename(columns={
                        'id': 'ID',
                        'value': 'Threshold',
                        'status': 'Status',
                        'created_at': 'Created'
                    }),
                    use_container_width=True
                )
                
                # Approval and Delete functionality
                st.markdown("#### 🔧 Manage Suggestions")
                all_suggestions = {f"ID {s['id']}: Threshold {s['value']}": s['id'] for s in suggestions}
                
                selected_suggestion = st.selectbox(
                    "Choose suggestion to manage:",
                    options=list(all_suggestions.keys())
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("👍 Approve Selected", type="primary", use_container_width=True):
                        suggestion_id = all_suggestions[selected_suggestion]
                        approve_response = requests.post(
                            f'http://127.0.0.1:8000/api/threshold_suggestions/approve/{suggestion_id}/'
                        )
                        
                        if approve_response.status_code == 200:
                            st.success("✅ Suggestion approved successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Approval failed")
                
                with col2:
                    if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
                        suggestion_id = all_suggestions[selected_suggestion]
                        
                        # Confirm deletion
                        with st.expander("⚠️ Confirm Deletion", expanded=True):
                            st.warning(f"Are you sure you want to delete suggestion {suggestion_id}?")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Yes, Delete", type="primary"):
                                    try:
                                        delete_response = requests.post(
                                            f'http://127.0.0.1:8000/api/threshold_suggestions/delete/{suggestion_id}/'
                                        )
                                        
                                        if delete_response.status_code == 200:
                                            st.success("🗑️ Suggestion deleted successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Delete failed: {delete_response.text}")
                                    except Exception as e:
                                        st.error(f"🚨 Delete error: {str(e)}")
                            with col2:
                                if st.button("❌ Cancel"):
                                    st.info("Deletion cancelled")
                    
            else:
                st.info("📝 No threshold suggestions yet. Run analysis first.")
                
        else:
            st.error(f"❌ Failed to load suggestions: {response.status_code}")
            
    except Exception as e:
        st.error(f"🚨 Error loading suggestions: {str(e)}")