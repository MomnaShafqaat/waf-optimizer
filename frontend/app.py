import streamlit as st
import requests
import pandas as pd

# API URL
API_URL = "http://127.0.0.1:8000/api/files/"

# Fetch data from Django API
response = requests.get(API_URL)
if response.status_code == 200:
    data = response.json()  # DRF returns list, not dict
else:
    st.error(f"Failed to fetch data: {response.status_code}")
    data = []

# Convert to DataFrame for display
if data:
    df = pd.DataFrame(data)
    st.title("Uploaded Files")
    
    # Show table
    st.dataframe(df)
    
    # Optional: Filter by file_type
    file_type_filter = st.selectbox("Filter by file type:", ["All"] + list(df['file_type'].unique()))
    if file_type_filter != "All":
        df_filtered = df[df['file_type'] == file_type_filter]
        st.dataframe(df_filtered)
else:
    st.info("No files uploaded yet.")
