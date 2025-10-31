import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *
from fetch_supabase_files import get_rules_files_from_supabase, get_traffic_files_from_supabase , download_file_from_supabase

def render_file_management():
    """Render file management section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>📁 Configuration Management</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3>WAF Rules</h3>", unsafe_allow_html=True)
        st.info("""
        **Required fields:** id, category, parameter, operator, value, phase, action, priority
        """)
        rules_file = st.file_uploader("Upload rules CSV", type=['csv'], key="rules_upload")
    with col2:
        st.markdown("<h3>Traffic Data</h3>", unsafe_allow_html=True)
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
                        
                        # Handle different response types and error cases
                        if response and isinstance(response, dict) and response.get('id'):
                            st.success(f"✅ Successfully uploaded {rules_file.name}")
                            uploaded_files.append(f"{rules_file.name} (Rules)")
                        elif response and isinstance(response, dict) and response.get('error'):
                            # Handle specific error cases - the error is a string containing the actual error dict
                            error_msg = str(response.get('error', ''))
                            
                            # Debug: Show what we're actually getting
                            st.write("Debug - Raw error:", error_msg)
                            
                            # Check for duplicate file error (nested in string)
                            if any(indicator in error_msg for indicator in ['409', 'Duplicate', 'already exists', 'resource already exists']):
                                st.warning(f"⚠️ File '{rules_file.name}' already exists in the system. Please use a different filename or delete the existing file first.")
                            else:
                                st.error(f"❌ Failed to upload {rules_file.name}: {error_msg}")
                            upload_success = False
                        else:
                            st.error(f"❌ Failed to upload {rules_file.name} - No valid response from server")
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
                        
                        # Handle different response types and error cases
                        if response and isinstance(response, dict) and response.get('id'):
                            st.success(f"✅ Successfully uploaded {traffic_file.name}")
                            uploaded_files.append(f"{traffic_file.name} (Traffic)")
                        elif response and isinstance(response, dict) and response.get('error'):
                            # Handle specific error cases - the error is a string containing the actual error dict
                            error_msg = str(response.get('error', ''))
                            
                            # Check for duplicate file error (nested in string)
                            if any(indicator in error_msg for indicator in ['409', 'Duplicate', 'already exists', 'resource already exists']):
                                st.warning(f"⚠️ File '{traffic_file.name}' already exists in the system. Please use a different filename or delete the existing file first.")
                            else:
                                st.error(f"❌ Failed to upload {traffic_file.name}: {error_msg}")
                            upload_success = False
                        else:
                            st.error(f"❌ Failed to upload {traffic_file.name} - No valid response from server")
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

def render_file_library():
    """Render file library section - fetches files directly from Supabase"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 File Library")

    # Fetch files directly from Supabase buckets
    with st.spinner("Loading files from storage..."):
        rules_files = get_rules_files_from_supabase()
        logs_files = get_traffic_files_from_supabase()
    
    # Combine all files in the format expected by the original code
    all_files = []
    
    # Add rules files
    for file_info in rules_files:
        all_files.append({
            'id': f"rules_{file_info['name']}",  # Generate a unique ID
            'filename': file_info['name'],
            'file_type': 'rules',
            'file_size': file_info.get('size', 0),
            'uploaded_at': file_info.get('created_at', 'Unknown'),
            'bucket': file_info['bucket']
        })
    
    # Add logs files  
    for file_info in logs_files:
        all_files.append({
            'id': f"logs_{file_info['name']}",  # Generate a unique ID
            'filename': file_info['name'],
            'file_type': 'logs',
            'file_size': file_info.get('size', 0),
            'uploaded_at': file_info.get('created_at', 'Unknown'),
            'bucket': file_info['bucket']
        })
    
    if all_files:
        df = pd.DataFrame(all_files)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(df))
        with col2:
            st.metric("Rule Sets", len(df[df['file_type'] == 'rules']))
        with col3:
            st.metric("Logs Files", len(df[df['file_type'] == 'logs']))
        
        # Display the files table (same as original but with Supabase data)
        st.dataframe(
            df[['id', 'filename', 'file_type', 'uploaded_at']].rename(
                columns={'filename': 'File Name', 'file_type': 'Type', 'uploaded_at': 'Uploaded'}
            ),
            use_container_width=True
        )
    else:
        st.info("No files found in Supabase storage")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_file_deletion():
    """Render file deletion section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("🗑️ Delete Files")

    # Fetch files directly from Supabase buckets
    with st.spinner("Loading files from storage..."):
        rules_files = get_rules_files_from_supabase()
        logs_files = get_traffic_files_from_supabase()
    
    # Combine all files in the same format as before
    all_files = []
    
    # Add rules files
    for file_info in rules_files:
        all_files.append({
            'id': f"supabase_rules_{file_info['name']}",  # Generate ID for display
            'filename': file_info['name'],
            'file_type': 'rules',
            'display_name': f"{file_info['name']} (Rules)"
        })
    
    # Add logs files
    for file_info in logs_files:
        all_files.append({
            'id': f"supabase_logs_{file_info['name']}",  # Generate ID for display
            'filename': file_info['name'],
            'file_type': 'logs',
            'display_name': f"{file_info['name']} (Logs)"
        })

    if all_files:
        # FIX: Use 'filename' instead of 'file'
        file_options = [
            f"{f['display_name']}"
            for f in all_files
        ]

        selected_file = st.selectbox("Select file to delete:", ["Choose a file..."] + file_options)

        if selected_file != "Choose a file...":
            # Find the selected file details
            selected_file_info = next((f for f in all_files if f['display_name'] == selected_file), None)
            
            if st.button("🗑️ Delete File", type="secondary"):
                if selected_file_info:
                    try:
                        # Call modified delete_file function with filename and type
                        response = delete_file(selected_file_info['filename'], selected_file_info['file_type'])
                        
                        if response and response.status_code == 204:
                            st.success(f"✅ File '{selected_file}' deleted successfully!")
                            # Refresh files by rerunning
                            st.rerun()
                        else:
                            st.error(f"❌ Delete failed: {response.status_code if response else 'No response'} - {response.text if response else 'Unknown error'}")
                    except Exception as e:
                        st.error(f"🚨 Error deleting file: {e}")
        else:
            st.info("Please select a file to delete.")
    else:
        st.info("No files available for deletion.")

    st.markdown('</div>', unsafe_allow_html=True)


def render_file_selection():
    """
    Render file selection dropdowns for rules and logs files
    Fetches files directly from Supabase storage and stores in session state
    
    Returns:
        tuple: (selected_rules, selected_logs) or (None, None) if no files
    """
    # Display file selection header
    st.markdown("### 📁 File Selection")
    st.markdown("Select the rules and logs files for analysis:")
    
    # Initialize session state for file management
    if 'available_rules_files' not in st.session_state:
        st.session_state.available_rules_files = []
    if 'available_logs_files' not in st.session_state:
        st.session_state.available_logs_files = []
    if 'selected_rules_file' not in st.session_state:
        st.session_state.selected_rules_file = None
    if 'selected_logs_file' not in st.session_state:
        st.session_state.selected_logs_file = None
    if 'rules_file_content' not in st.session_state:
        st.session_state.rules_file_content = None
    if 'logs_file_content' not in st.session_state:
        st.session_state.logs_file_content = None
    
    # Fetch files directly from Supabase buckets
    with st.spinner("Loading files from storage..."):
        rules_files = get_rules_files_from_supabase()
        logs_files = get_traffic_files_from_supabase()
        
        # Store in session state for other modules to use
        st.session_state.available_rules_files = rules_files
        st.session_state.available_logs_files = logs_files
    
    # Debug info (optional)
    st.write(f"📊 Found {len(rules_files)} rules files, {len(logs_files)} logs files")
    
    if not rules_files or not logs_files:
        st.warning("⚠️ Please upload files to Supabase storage to proceed with analysis.")
        return None, None
    
    # Create file selection section with better visual separation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**WAF Rules File**")
        selected_rules = st.selectbox(
            "Select Rules File:", 
            options=rules_files, 
            format_func=lambda x: x['name'],
            key="rules_file_selector",
            help="Choose the WAF rules file for analysis"
        )
        if selected_rules:
            st.info(f"Selected: {selected_rules['name']}")
    
    with col2:
        st.markdown("**Traffic Logs File**")
        selected_logs = st.selectbox(
            "Select Logs File:", 
            options=logs_files, 
            format_func=lambda x: x['name'],
            key="logs_file_selector",
            help="Choose the traffic logs file for analysis"
        )
        if selected_logs:
            st.info(f"Selected: {selected_logs['name']}")
    
    # Store selected files in session state
    if selected_rules:
        st.session_state.selected_rules_file = selected_rules
        # Pre-load content for other modules
        with st.spinner(f"Loading {selected_rules['name']}..."):
            st.session_state.rules_file_content = download_file_from_supabase(selected_rules['name'], 'rules')
    
    if selected_logs:
        st.session_state.selected_logs_file = selected_logs
        # Pre-load content for other modules
        with st.spinner(f"Loading {selected_logs['name']}..."):
            st.session_state.logs_file_content = download_file_from_supabase(selected_logs['name'], 'traffic')
    
    # Display success message if both files are loaded
    if selected_rules and selected_logs:
        st.success("✅ Files successfully loaded and ready for analysis!")
        st.markdown("---")
    
    return selected_rules, selected_logs

# Utility functions for other modules to access file data
def get_current_rules_file():
    """Get currently selected rules file from session state"""
    return st.session_state.get('selected_rules_file')

def get_current_logs_file():
    """Get currently selected logs file from session state"""
    return st.session_state.get('selected_logs_file')

def get_rules_file_content():
    """Get rules file content from session state"""
    return st.session_state.get('rules_file_content')

def get_logs_file_content():
    """Get logs file content from session state"""
    return st.session_state.get('logs_file_content')

def get_available_rules_files():
    """Get all available rules files from session state"""
    return st.session_state.get('available_rules_files', [])

def get_available_logs_files():
    """Get all available logs files from session state"""
    return st.session_state.get('available_logs_files', [])