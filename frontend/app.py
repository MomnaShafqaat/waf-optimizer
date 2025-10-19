import streamlit as st
import requests
import pandas as pd
import json

# API URLs - CORRECTED
API_URL = "http://127.0.0.1:8000/api/files/"
RULE_ANALYSIS_API_URL = "http://127.0.0.1:8000/api/analyze/"

# Define the function at the TOP level, before it's used
def display_analysis_results(results):
    """Display the rule analysis results"""
    
    st.header("📊 Rule Analysis Results")
    
    # Handle response format
    if 'data' in results:
        data = results['data']
    else:
        data = results
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rules Analyzed", data.get('total_rules_analyzed', 0))
    with col2:
        st.metric("Relationships Found", data.get('relationships_found', 0))
    with col3:
        shd_count = len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'SHD'])
        st.metric("Shadowing (SHD)", shd_count)
    with col4:
        rxd_count = len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'RXD'])
        st.metric("Redundancy (RXD)", rxd_count)
    
    # Detailed results
    relationships = data.get('relationships', [])
    if relationships:
        st.subheader("📋 Detailed Relationships")
        
        for rel in relationships:
            with st.expander(f"Rule {rel.get('rule_a')} 🠖 Rule {rel.get('rule_b')} ({rel.get('relationship_type')})"):
                st.write(f"**Confidence:** {rel.get('confidence', 'N/A')}")
                st.write(f"**Evidence Count:** {rel.get('evidence_count', 'N/A')}")
                st.write(f"**Description:** {rel.get('description', 'No description')}")
    else:
        st.info("No relationships found in the analysis.")
    
    # Optimization recommendations
    recommendations = data.get('recommendations', [])
    if recommendations:
        st.subheader("🎯 Optimization Recommendations")
        for rec in recommendations:
            st.write(f"**{rec.get('type', 'Recommendation')}:** {rec.get('description', 'No description')}")
            st.write(f"**Impact:** {rec.get('impact', 'Not specified')}")
            st.write("---")

st.title("🚀 WAF Rule Analysis & Optimization System")

# Check if Django is running
try:
    test_response = requests.get(API_URL, timeout=3)
    django_online = True
except:
    django_online = False
    st.error("🚨 Django backend not running! Start it with: `python manage.py runserver`")
    st.stop()

# Section 1: File Management
st.header("📁 File Management")

# Upload section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload WAF Rules File")
    rules_file = st.file_uploader(
        "Upload Rules CSV", 
        type=['csv'],
        key="rules_upload"
    )

with col2:
    st.subheader("Upload WAF Traffic Logs")
    traffic_file = st.file_uploader(
        "Upload Traffic Logs CSV", 
        type=['csv'],
        key="traffic_upload"
    )

# Upload files
if rules_file or traffic_file:
    if st.button("📤 Upload Files", type="primary"):
        if rules_file:
            rules_files = {'file': (rules_file.name, rules_file.getvalue())}
            rules_data = {'file_type': 'rules'}
            rules_response = requests.post(API_URL, files=rules_files, data=rules_data)
            if rules_response.status_code == 201:
                st.success(f"✅ Rules file '{rules_file.name}' uploaded successfully!")
                st.rerun()
            else:
                st.error(f"❌ Rules upload failed: {rules_response.status_code}")
        
        if traffic_file:
            traffic_files = {'file': (traffic_file.name, traffic_file.getvalue())}
            traffic_data = {'file_type': 'traffic'}
            traffic_response = requests.post(API_URL, files=traffic_files, data=traffic_data)
            if traffic_response.status_code == 201:
                st.success(f"✅ Traffic file '{traffic_file.name}' uploaded successfully!")
                st.rerun()
            else:
                st.error(f"❌ Traffic upload failed: {traffic_response.status_code}")

# Section 2: Rule Analysis
st.header("🔍 Rule Relationship Analysis")

# Fetch uploaded files
response = requests.get(API_URL)
if response.status_code == 200:
    files_data = response.json()
    
    # Separate rules and traffic files
    rules_files = [f for f in files_data if f['file_type'] == 'rules']
    traffic_files = [f for f in files_data if f['file_type'] == 'traffic']
    
    if rules_files and traffic_files:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_rules = st.selectbox(
                "Select Rules File:",
                options=rules_files,
                format_func=lambda x: x['file'].split('/')[-1]
            )
        
        with col2:
            selected_traffic = st.selectbox(
                "Select Traffic File:",
                options=traffic_files,
                format_func=lambda x: x['file'].split('/')[-1]
            )
        
        # Analysis options
        st.subheader("Analysis Configuration")
        analysis_types = st.multiselect(
            "Select Analysis Types:",
            options=[
                "Shadowing (SHD)",
                "Generalization (GEN)", 
                "Redundancy (RXD)",
                "Correlation (COR)"
            ],
            default=["Shadowing (SHD)", "Redundancy (RXD)"]
        )
        
        if st.button("🔬 Run Rule Analysis", type="primary"):
            # Prepare analysis request
            analysis_data = {
                'rules_file_id': selected_rules['id'],
                'traffic_file_id': selected_traffic['id'],
                'analysis_types': [atype.split(' ')[0] for atype in analysis_types]
            }
            
            st.write("📡 Sending request to:", RULE_ANALYSIS_API_URL)
            
            # Call rule analysis API
            with st.spinner("Analyzing rule relationships..."):
                try:
                    analysis_response = requests.post(RULE_ANALYSIS_API_URL, json=analysis_data, timeout=30)
                    
                    st.write(f"Response Status: {analysis_response.status_code}")
                    
                    if analysis_response.status_code == 200:
                        results = analysis_response.json()
                        st.success("✅ Analysis completed successfully!")
                        display_analysis_results(results)  # Now this function is defined above
                    else:
                        st.error(f"❌ Analysis failed with status {analysis_response.status_code}")
                        st.write(f"Response: {analysis_response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to analysis API")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    else:
        st.warning("⚠️ Please upload both rules and traffic files to perform analysis")
else:
    st.error("Failed to fetch uploaded files")

# Section 3: File Management
st.header("📊 Previously Uploaded Files")

# Fetch data from Django API
response = requests.get(API_URL)
if response.status_code == 200:
    data = response.json()
else:
    st.error(f"Failed to fetch data: {response.status_code}")
    data = []

# Convert to DataFrame for display
if data:
    df = pd.DataFrame(data)
    
    st.subheader("File Inventory")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Files", len(df))
    with col2:
        st.metric("Rules Files", len(df[df['file_type'] == 'rules']))
    with col3:
        st.metric("Traffic Files", len(df[df['file_type'] == 'traffic']))
    
    # Show files table
    st.dataframe(
        df[['id', 'file', 'file_type', 'uploaded_at']].rename(
            columns={'file': 'File Name', 'file_type': 'Type', 'uploaded_at': 'Uploaded At'}
        ),
        use_container_width=True
    )
    
    # DELETE SECTION
    st.subheader("🗑️ Delete Files")
    
    file_options = [f"ID {f['id']}: {f['file'].split('/')[-1]} ({f['file_type']})" for f in data]
    selected_file = st.selectbox("Select file to delete:", ["Choose a file..."] + file_options)
    
    if selected_file != "Choose a file..." and st.button("Delete File", type="secondary"):
        file_id = int(selected_file.split(":")[0].replace("ID ", ""))
        delete_url = f"{API_URL}{file_id}/"
        
        response = requests.delete(delete_url)
        if response.status_code == 204:
            st.success("✅ File deleted successfully!")
            st.rerun()
        else:
            st.error(f"❌ Delete failed: {response.status_code}")
    
else:
    st.info("No files uploaded yet. Upload your WAF rules and traffic files above.")