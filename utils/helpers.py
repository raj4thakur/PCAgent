# utils/helpers.py
import streamlit as st
import pandas as pd
import plotly.express as px

def init_session_state():
    """Initialize session state variables"""
    if 'db' not in st.session_state:
        st.session_state.db = None
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = None
    if 'analytics' not in st.session_state:
        st.session_state.analytics = None
    if 'whatsapp_manager' not in st.session_state:
        st.session_state.whatsapp_manager = None
    if 'files_processed' not in st.session_state:
        st.session_state.files_processed = False

def create_simple_chart(data, title, x_col, y_col):
    """Create a simple chart using Streamlit's native charts or fallback to table"""
    if not data.empty:
        try:
            fig = px.line(data, x=x_col, y=y_col, title=title)
            return fig
        except Exception:
            # Fallback to table display
            st.write(f"**{title}**")
            st.dataframe(data[[x_col, y_col]])
            return None
    else:
        st.write(f"**{title}**")
        return None

def check_module_availability():
    """Check if all required modules are available"""
    try:
        from database import DatabaseManager
        from data_processor import DataProcessor
        from analytics import Analytics
        try:
            from whatsapp_manager import WhatsAppManager
            WHATSAPP_AVAILABLE = True
        except ImportError:
            WHATSAPP_AVAILABLE = False
            
        return True, WHATSAPP_AVAILABLE
    except ImportError as e:
        st.error(f"Import Error: {e}")
        st.info("Please make sure all required files are in the same directory.")
        return False, False