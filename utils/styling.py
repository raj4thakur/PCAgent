# utils/styling.py
import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .section-header {
            border-left: 5px solid #1f77b4;
            padding-left: 1rem;
            margin: 1.5rem 0 1rem 0;
            font-size: 1.5rem;
        }
        .stButton button {
            width: 100%;
        }
        @media (max-width: 768px) {
            .main-header {
                font-size: 2rem;
            }
            .metric-value {
                font-size: 1.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def create_metric_card(value, label, icon="📊", color="#1f77b4"):
    """Create a styled metric card"""
    return f"""
    <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {color}88 100%);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            <div style="font-size: 2rem;">{icon}</div>
        </div>
    </div>
    """

COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ffbb78'
}