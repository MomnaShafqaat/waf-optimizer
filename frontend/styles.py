#false_positive_reduction/component
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

def apply_custom_styles():
    """Apply modern dark theme CSS styles based on MindLink design system"""
    st.markdown("""
    <style>
        /* Global Dark Theme */
        body {
            font-family: 'Inter', sans-serif; /* Using a modern font */
        }
        .main { 
            background-color: #1a1a1a; 
            color: #ffffff;
        }
        
        /* Sidebar Styling */
        .css-1d391kg, .css-vk32pt { /* Targets for sidebar container */
            background-color: #1a1a1a !important;
            padding: 16px !important;
        }
        .css-r698ls { /* Streamlit sidebar top padding */
            padding-top: 0 !important;
        }

        /* Typography */
        h1 { 
            color: #ffffff; 
            font-size: 32px; /* From MindLink greeting */
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 8px; /* Adjusted spacing */
        }
        
        h2 { 
            color: #ffffff; 
            font-size: 24px; /* From MindLink greeting subtext */
            font-weight: 600;
            margin-bottom: 24px; /* More spacing for sections */
            background: linear-gradient(135deg, #7c3aed, #8b5cf6); /* Gradient for section titles */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block; /* To make gradient apply only to text */
        }

        h3 { 
            color: #ffffff; 
            font-size: 18px; /* From MindLink phase header */
            font-weight: 500;
            margin-bottom: 16px; /* Spacing */
        }
        
        /* Streamlit specific text elements */
        .stMarkdown p, .stText {
            color: #a3a3a3; /* Secondary text color */
            font-size: 14px;
            line-height: 1.5;
        }
        .stMarkdown strong {
            color: #ffffff; /* Primary text for bold */
        }

        /* Cards with Dark Theme */
        .card { 
            background: #242424; /* Secondary background */
            padding: 28px; /* Larger padding for cards */
            border-radius: 14px; /* Larger border radius */
            border: 1px solid #2a2a2a; /* Tertiary background as border */
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4); /* Elevated shadow */
            margin-bottom: 24px; /* Consistent card spacing */
        }
        
        /* Enhanced Buttons */
        .stButton button { 
            background: #7c3aed; /* Primary accent color */
            color: #ffffff; 
            border: none; 
            border-radius: 8px; 
            padding: 12px 24px; 
            font-weight: 500;
            transition: all 0.2s ease;
            display: flex; /* For icon + text alignment */
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .stButton button:hover { 
            background: #8b5cf6; /* Lighter accent on hover */
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4); 
        }
        
        /* Secondary Button (e.g., for 'Clear Filters') */
        .st-btn-secondary button {
            background: #333333 !important; /* Interactive hover color */
            color: #ffffff !important;
            border: 1px solid #404040 !important; /* Interactive active color */
        }
        .st-btn-secondary button:hover {
            background: #404040 !important;
            box-shadow: none !important;
            transform: none !important;
        }

        /* Primary Action Button - Specific styling */
        .primary-button {
            background: #7c3aed !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
        }
        
        /* Success Button */
        .success-button {
            background: #10b981 !important;
            color: #000000 !important; /* Black text for success */
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
        }
        
        /* Warning Button */
        .warning-button {
            background: #f59e0b !important;
            color: #000000 !important; /* Black text for warning */
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
        }
        
        /* Input Fields */
        .stTextInput > label, .stSelectbox > label, .stMultiSelect > label, .stSlider > label {
            color: #ffffff; /* Label color */
            font-size: 14px;
            margin-bottom: 8px;
        }
        .stTextInput > div > div > input, 
        .stSelectbox > div > div > div, 
        .stMultiSelect > div > div > div {
            background-color: #242424 !important; /* Secondary background */
            color: #ffffff !important;
            border: 1px solid #404040 !important; /* Interactive border */
            border-radius: 8px !important;
            padding: 10px 12px !important;
        }
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: #242424 !important;
            color: #ffffff !important;
        }
        
        /* Metrics Cards */
        .metric-card {
            background: #242424;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #333333;
            text-align: center;
            margin: 8px 0; /* Adjusted margin */
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        .metric-value {
            font-size: 28px; /* Larger value */
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }
        
        .metric-label {
            font-size: 14px;
            color: #a3a3a3;
        }
        
        /* Status Indicators */
        .status-completed { color: #10b981; font-weight: 500; }
        .status-in-progress { color: #10b981; font-weight: 500; }
        .status-pending { color: #f59e0b; font-weight: 500; }
        .status-alert { color: #ef4444; font-weight: 500; }
        
        /* Badges */
        .badge {
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: inline-block;
        }
        
        .badge-success { background: #10b981; color: #000000; }
        .badge-warning { background: #f59e0b; color: #000000; }
        .badge-info { background: #3b82f6; color: #ffffff; }
        .badge-purple { background: #7c3aed; color: #ffffff; }
        
        /* Pills/Tags - Focus Selector */
        .pill {
            padding: 10px 18px;
            border-radius: 20px;
            border: 1px solid #404040;
            font-size: 14px;
            white-space: nowrap;
            display: inline-flex; /* Use flex for alignment */
            align-items: center;
            margin-right: 10px; /* Space between pills */
            margin-bottom: 10px; /* For wrapping */
            background: transparent;
            color: #ffffff;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .pill:hover {
            border-color: #7c3aed;
            color: #7c3aed;
        }
        .pill-active {
            background: #10b981;
            color: #000000;
            border: none;
            font-weight: 500;
        }
        
        /* Expander Styling */
        .streamlit-expanderHeader {
            background: #242424 !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
        }
        
        .streamlit-expanderContent {
            background: #1e1e1e !important; /* Tertiary bg for content */
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-top: none !important;
            border-radius: 0 0 8px 8px !important;
            padding: 16px !important;
        }
        
        /* Progress Bars */
        .stProgress > div > div > div {
            background: #7c3aed !important;
        }
        
        /* Data Tables */
        .stDataFrame {
            background: #242424 !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        
        /* Alerts */
        .stAlert {
            border-radius: 8px !important;
            border: 1px solid #333333 !important;
            background-color: rgba(36, 36, 36, 0.7) !important; /* Semi-transparent secondary */
        }
        
        .stSuccess {
            background-color: rgba(16, 185, 129, 0.15) !important;
            border-color: #10b981 !important;
            color: #10b981 !important;
        }
        
        .stError {
            background-color: rgba(239, 68, 68, 0.15) !important;
            border-color: #ef4444 !important;
            color: #ef4444 !important;
        }
        
        .stWarning {
            background-color: rgba(245, 158, 11, 0.15) !important;
            border-color: #f59e0b !important;
            color: #f59e0b !important;
        }
        
        .stInfo {
            background-color: rgba(59, 130, 246, 0.15) !important;
            border-color: #3b82f6 !important;
            color: #3b82f6 !important;
        }
        
        /* Custom spacing - now more granular */
        .section-spacing { margin: 32px 0; } /* 4xl */
        .card-spacing { margin: 24px 0; } /* 2xl */
        .element-spacing { margin: 16px 0; } /* lg */
        .compact-spacing { margin: 12px 0; } /* md */

    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the main header with enhanced dark theme based on MindLink design"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a1a, #242424); padding: 32px 48px; margin: 0 auto; max-width: 900px; box-sizing: border-box;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px;">
            <div>
                <p style="margin: 0 0 4px 0; font-size: 28px; line-height: 1.2; color: #ffffff; font-weight: 600;">
                    Good evening, Mark!
                </p>
                <p style="margin: 4px 0 0 0; color: #a3a3a3; font-size: 16px;">
                    What would you like to explore today?
                </p>
            </div>
            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="background: #242424; padding: 8px; border-radius: 6px; position: relative; cursor: pointer; border: 1px solid #333333;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-bell"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; position: absolute; top: 6px; right: 6px; border: 2px solid #1a1a1a;"></div>
                </div>
                <div style="width: 1px; height: 30px; background-color: #404040;"></div>
                <div style="background: #242424; padding: 8px; border-radius: 6px; cursor: pointer; border: 1px solid #333333;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                </div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)

def render_main_dashboard():
    """Renders a main content dashboard section based on MindLink design system."""
    st.markdown("""
    <div style="max-width: 900px; margin: 0 auto; padding: 0 48px;">
        <div class="element-spacing">
            <h3 style="margin-bottom: 16px; font-size: 16px; color: #a3a3a3;">Choose your focus</h3>
            <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 32px;">
                <span class="pill pill-active">Summarize reports</span>
                <span class="pill">Extract key insights</span>
                <span class="pill">Compare projects</span>
                <span class="pill">Answer questions</span>
                <span class="pill">Draft documents</span>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; background-color: #242424;">
            <p style="margin: 0; font-size: 16px; color: #ffffff;">
                Ask something about your workspace or documents.
            </p>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-refresh-cw" style="cursor: pointer;"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.5 7.9c1.1-2.2 3.4-3.5 5.9-3.5h.5c4.6 0 8.5 3.5 8.9 8"></path><path d="M20.5 16.1c-1.1 2.2-3.4 3.5-5.9 3.5h-.5c-4.6 0-8.5-3.5-8.9-8"></path></svg>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 32px; display: flex; gap: 24px; align-items: center; background-color: #242424;">
            <div style="width: 120px; height: 120px; border-radius: 16px; padding: 16px; background: linear-gradient(135deg, #7c3aed, #8b5cf6, #ec4899); display: flex; justify-content: center; align-items: center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            </div>
            <div style="flex: 1;">
                <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #ffffff;">
                    Generate a one-page summary of the product roadmap.
                </p>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 12px; font-size: 13px; color: #a3a3a3;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #f59e0b;"></div> <!-- Loading dot -->
                    Wait a minute
                </div>
            </div>
        </div>
        
        <div class="card" style="margin-bottom: 24px; padding: 28px; background-color: #242424;">
            <span class="badge" style="background-color: #ec4899; color: #ffffff; margin-bottom: 16px;">GOAL</span>
            <p style="margin-bottom: 24px; font-size: 17px; line-height: 1.6; font-weight: 500; color: #ffffff;">
                Deliver a unified, intelligent workspace that connects all company knowledge and enables contextual answers in real time.
            </p>
            <div style="padding: 16px 0; border-top: 1px solid #333333; display: flex; justify-content: space-between; gap: 16px;">
                <div style="flex: 1;">
                    <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 500; color: #ffffff;">Phase 1: Integrations</p>
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #a3a3a3;">Connect Google Drive, Notion, Slack and Confluence as data sources.</p>
                </div>
                <span class="badge" style="background-color: #10b981; color: #000000; align-self: flex-start;">Completed</span>
            </div>
            <div style="padding: 16px 0; border-top: 1px solid #333333; display: flex; justify-content: space-between; gap: 16px;">
                <div style="flex: 1;">
                    <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 500; color: #ffffff;">Phase 2: Contextual chat</p>
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #a3a3a3;">Launch Ask AI interface with smart document linking and reference citations.</p>
                </div>
                <span class="badge" style="background-color: #10b981; color: #000000; align-self: flex-start;">In Progress</span>
            </div>
        </div>

        <div style="position: fixed; bottom: 32px; left: calc(250px + 48px); right: calc(320px + 48px); max-width: 900px; margin: 0 auto;">
            <div style="padding: 8px 12px; border-radius: 28px; background-color: #242424; display: flex; gap: 8px; align-items: center; border: 1px solid #333333;">
                <button style="padding: 10px; border-radius: 8px; width: 40px; height: 40px; background: none; border: none; cursor: pointer;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-paperclip"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49L17.5 2.5A4 4 0 0 1 23 8l-7.1 7.1"></path></svg>
                </button>
                <button style="padding: 10px; border-radius: 8px; width: 40px; height: 40px; background: none; border: none; cursor: pointer;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                </button>
                <input type="text" placeholder="Ask mindlink..." style="padding: 10px 12px; flex: 1; border: none; outline: none; background: transparent; color: #ffffff; font-size: 14px;">
                <button style="padding: 10px; border-radius: 8px; width: 40px; height: 40px; background: none; border: none; cursor: pointer;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-microphone"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
                </button>
                <button style="padding: 10px 24px; border-radius: 20px; background-color: #7c3aed; color: #ffffff; font-size: 14px; font-weight: 500; border: none; cursor: pointer;">
                    Send
                </button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
