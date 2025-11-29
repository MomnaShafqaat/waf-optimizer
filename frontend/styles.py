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
    """Header customized for WAF Optimizer"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a1a, #242424); padding: 32px 48px; margin: 0 auto; max-width: 900px; box-sizing: border-box;">

        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px;">

            <div>
                <p style="margin: 0 0 4px 0; font-size: 28px; line-height: 1.2; color: #ffffff; font-weight: 600;">
                    WAF Optimizer Dashboard
                </p>
                <p style="margin: 4px 0 0 0; color: #a3a3a3; font-size: 16px;">
                    Monitor, analyze, and reduce false positives in real time.
                </p>
            </div>

            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="background: #242424; padding: 8px; border-radius: 6px; position: relative; cursor: pointer; border: 1px solid #333333;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" stroke="#a3a3a3" stroke-width="2" fill="none" class="feather feather-bell">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; position: absolute; top: 6px; right: 6px; border: 2px solid #1a1a1a;"></div>
                </div>

                <div style="width: 1px; height: 30px; background-color: #404040;"></div>

                <div style="background: #242424; padding: 8px; border-radius: 6px; cursor: pointer; border: 1px solid #333333;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" stroke="#a3a3a3" stroke-width="2" fill="none" class="feather feather-shield">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                    </svg>
                </div>
            </div>

        </div>

    </div>
    """, unsafe_allow_html=True)
def render_main_dashboard():
    """Professional WAF analysis dashboard"""
    st.markdown("""
    <div style="max-width: 900px; margin: 0 auto; padding: 0 48px;">

        <div class="element-spacing">
            <h3 style="margin-bottom: 16px; font-size: 16px; color: #a3a3a3;">Select an analysis category</h3>
            <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 32px;">
                <span class="pill pill-active">False Positive Reduction</span>
                <span class="pill">Rule Performance</span>
                <span class="pill">Traffic Insights</span>
                <span class="pill">Threat Intelligence</span>
                <span class="pill">Log Deep Analysis</span>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 20px 24px; display: flex; justify-content: space-between; align-items: center;">
            <p style="margin: 0; font-size: 16px; color: #ffffff;">
                Run an automated analysis on uploaded WAF logs.
            </p>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" stroke="#a3a3a3" fill="none" stroke-width="2" class="feather feather-cpu" style="cursor: pointer;">
                <rect x="4" y="4" width="16" height="16" rx="2"></rect>
                <path d="M9 9h6v6H9z"></path>
                <path d="M3 9h1"/>
                <path d="M3 12h1"/>
                <path d="M3 15h1"/>
                <path d="M20 9h1"/>
                <path d="M20 12h1"/>
                <path d="M20 15h1"/>
            </svg>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 32px; display: flex; gap: 24px; align-items: center;">
            <div style="width: 120px; height: 120px; border-radius: 16px; padding: 16px;
                background: linear-gradient(135deg, #7c3aed, #8b5cf6, #ec4899);
                display: flex; justify-content: center; align-items: center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" stroke="#ffffff" fill="none" stroke-width="2" class="feather feather-activity">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                </svg>
            </div>

            <div style="flex: 1;">
                <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #ffffff;">
                    Analyze anomaly patterns and generate recommended rule adjustments.
                </p>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 12px; font-size: 13px; color: #a3a3a3;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #f59e0b;"></div>
                    Processing…
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 28px;">
            <span class="badge badge-purple" style="margin-bottom: 16px;">SYSTEM OBJECTIVE</span>

            <p style="margin-bottom: 24px; font-size: 17px; line-height: 1.6; font-weight: 500; color: #ffffff;">
                Improve WAF precision by reducing false positives while maintaining robust attack detection.
            </p>

            <div style="padding: 16px 0; border-top: 1px solid #333333; display: flex; justify-content: space-between;">
                <div style="flex: 1;">
                    <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 500; color: #ffffff;">Phase 1: Log Integration</p>
                    <p style="margin: 0; font-size: 14px; color: #a3a3a3;">Connect log sources and validate data ingestion pipeline.</p>
                </div>
                <span class="badge badge-success">Completed</span>
            </div>

            <div style="padding: 16px 0; border-top: 1px solid #333333; display: flex; justify-content: space-between;">
                <div style="flex: 1;">
                    <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 500; color: #ffffff;">Phase 2: Automated Rule Scoring</p>
                    <p style="margin: 0; font-size: 14px; color: #a3a3a3;">Generate dynamic confidence levels for each triggered rule.</p>
                </div>
                <span class="badge badge-warning">In Progress</span>
            </div>
        </div>

    </div>
    """, unsafe_allow_html=True)
