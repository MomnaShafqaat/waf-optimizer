"""
Utility functions for fetching files from Supabase Storage
"""
import pandas as pd
import io
from supabase_client import supabase


def get_file_from_supabase(uploaded_file):
    """
    Fetch file content from Supabase Storage based on UploadedFile model
    
    Args:
        uploaded_file: UploadedFile model instance
        
    Returns:
        bytes: File content from Supabase
    """
    if not uploaded_file or not uploaded_file.supabase_path:
        raise ValueError(f"File {uploaded_file.filename if uploaded_file else 'None'} has no Supabase path")
    
    # Determine bucket based on file type
    if uploaded_file.file_type == 'rules':
        bucket_name = "waf-rule-files"
    elif uploaded_file.file_type in ['traffic', 'logs']:
        bucket_name = "waf-log-files"
    else:
        raise ValueError(f"Unknown file type: {uploaded_file.file_type}")
    
    try:
        # Download file from Supabase
        file_content = supabase.storage.from_(bucket_name).download(uploaded_file.supabase_path)
        return file_content
    except Exception as e:
        raise Exception(f"Failed to fetch file {uploaded_file.filename} from Supabase: {str(e)}")


def get_file_as_dataframe(uploaded_file):
    """
    Fetch file from Supabase and convert to pandas DataFrame
    
    Args:
        uploaded_file: UploadedFile model instance
        
    Returns:
        pd.DataFrame: File content as DataFrame
    """
    file_content = get_file_from_supabase(uploaded_file)
    
    # Convert bytes to string if needed
    if isinstance(file_content, bytes):
        file_content = file_content.decode('utf-8')
    
    # Read CSV from string
    df = pd.read_csv(io.StringIO(file_content))
    return df


def get_file_as_string(uploaded_file):
    """
    Fetch file from Supabase and return as string
    
    Args:
        uploaded_file: UploadedFile model instance
        
    Returns:
        str: File content as string
    """
    file_content = get_file_from_supabase(uploaded_file)
    
    # Convert bytes to string if needed
    if isinstance(file_content, bytes):
        return file_content.decode('utf-8')
    
    return file_content


def file_exists_in_supabase(uploaded_file):
    """
    Check if file exists in Supabase storage
    """
    try:
        if uploaded_file.file_type == 'rules':
            bucket_name = "waf-rule-files"
        elif uploaded_file.file_type in ['traffic', 'logs']:
            bucket_name = "waf-log-files"
        else:
            return False
        
        # Try to list the file
        files = supabase.storage.from_(bucket_name).list()
        return any(f['name'] == uploaded_file.supabase_path for f in files)
    except:
        return False