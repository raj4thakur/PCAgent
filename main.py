# main.py (Fixed version)
import streamlit as st
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

# MUST BE FIRST - Page configuration
st.set_page_config(
    page_title="Sales Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import utilities - Create these if they don't exist
try:
    from utils.styling import apply_custom_css
    from utils.helpers import init_session_state, check_module_availability
    from components.database_status import show_database_status
except ImportError:
    # Create basic fallbacks if utils don't exist
    def apply_custom_css():
        st.markdown("""
        <style>
        .main-header { color: #1f77b4; }
        .section-header { color: #2e86ab; margin-top: 2rem; }
        </style>
        """, unsafe_allow_html=True)
    
    def init_session_state():
        if 'db' not in st.session_state:
            st.session_state.db = None
        if 'data_processor' not in st.session_state:
            st.session_state.data_processor = None
        if 'analytics' not in st.session_state:
            st.session_state.analytics = None
        if 'whatsapp_manager' not in st.session_state:
            st.session_state.whatsapp_manager = None
    
    def check_module_availability():
        try:
            import pandas, plotly, sqlite3
            MODULES_AVAILABLE = True
        except ImportError:
            MODULES_AVAILABLE = False
        
        try:
            import pywhatkit
            WHATSAPP_AVAILABLE = True
        except ImportError:
            WHATSAPP_AVAILABLE = False
            
        return MODULES_AVAILABLE, WHATSAPP_AVAILABLE
    
    def show_database_status(db):
        if db:
            try:
                health = db.execute_query("SELECT COUNT(*) FROM sqlite_master", log_action=False)
                st.sidebar.success("✅ Database Connected")
            except:
                st.sidebar.error("❌ Database Error")
        else:
            st.sidebar.warning("⚠️ Database Not Initialized")

# Apply custom CSS
apply_custom_css()

# Initialize session state
init_session_state()

# Check module availability
MODULES_AVAILABLE, WHATSAPP_AVAILABLE = check_module_availability()

# Initialize components with error handling
if MODULES_AVAILABLE:
    try:
        from database import DatabaseManager
        from data_processor import DataProcessor
        from analytics import Analytics
        
        if st.session_state.db is None:
            st.session_state.db = DatabaseManager()
            st.success("✅ Database initialized successfully!")
        
        if st.session_state.data_processor is None:
            st.session_state.data_processor = DataProcessor(st.session_state.db)
        
        if st.session_state.analytics is None:
            st.session_state.analytics = Analytics(st.session_state.db)
        
        if WHATSAPP_AVAILABLE and st.session_state.whatsapp_manager is None:
            try:
                from whatsapp_manager import WhatsAppManager
                st.session_state.whatsapp_manager = WhatsAppManager(st.session_state.db)
                st.success("✅ WhatsApp Manager initialized!")
            except Exception as e:
                st.warning(f"⚠️ WhatsApp Manager not available: {e}")
                st.session_state.whatsapp_manager = None
                
    except Exception as e:
        st.error(f"❌ Application initialization failed: {e}")
        st.info("Please check that all required files are in the correct location.")

# Assign to local variables for easier access
db = st.session_state.db
data_processor = st.session_state.data_processor
analytics = st.session_state.analytics
whatsapp_manager = st.session_state.whatsapp_manager

# Sidebar navigation
st.sidebar.markdown("<h1 style='text-align: center;'>🚀 Sales Management</h1>", unsafe_allow_html=True)

page = st.sidebar.radio("Navigation", [
    "📊 Dashboard", "👥 Customers", "💰 Sales", "💳 Payments", 
    "🎯 Demos", "🤝 Distributors", "🔍 File Viewer", "📤 Data Import", "📈 Reports"
], index=0)

# Page routing with error handling
try:
    if page == "📊 Dashboard":
        try:
            from pages.dashboard import create_dashboard
            create_dashboard(db, analytics)
        except ImportError:
            st.error("Dashboard page not available. Creating basic dashboard...")
            show_basic_dashboard(db, analytics)
    
    elif page == "👥 Customers":
        try:
            from pages.customers import show_customers_page
            show_customers_page(db, whatsapp_manager)
        except ImportError:
            st.error("Customers page not available")
    
    elif page == "💰 Sales":
        try:
            from pages.sales import show_sales_page
            show_sales_page(db, whatsapp_manager)
        except ImportError:
            st.error("Sales page not available")
    
    elif page == "🎯 Demos":
        from pages.demos import show_demos_page
        show_demos_page(db, whatsapp_manager)
        
    elif page == "💳 Payments":
        from pages.payments import show_payments_page
        show_payments_page(db, whatsapp_manager)
    
    elif page == "🤝 Distributors":
        try:
            from pages.distributors import show_distributors_page
            show_distributors_page(db, whatsapp_manager)
        except ImportError:
            st.error("Distributors page not available")
    
    elif page == "🔍 File Viewer":
        try:
            from pages.file_viewer import show_file_viewer_page
            show_file_viewer_page(db, data_processor)
        except ImportError:
            st.error("File Viewer page not available")
    
    elif page == "📤 Data Import":
        try:
            from pages.data_import import show_data_import_page
            show_data_import_page(db, data_processor)
        except ImportError:
            st.error("Data Import page not available")
    
    elif page == "📈 Reports":
        try:
            from pages.reports import show_reports_page
            show_reports_page(db,whatsapp_manager)
        except ImportError:
            st.error("Reports page not available")

except Exception as e:
    st.error(f"Application error: {e}")
    st.info("Please check the console for more details.")

# Show database status in sidebar
show_database_status(db)

st.sidebar.markdown("---")
st.sidebar.info("🚀 Sales Management System v2.0")

# Basic dashboard fallback
def show_basic_dashboard(db, analytics):
    st.title("📊 Sales Dashboard")
    
    if db and analytics:
        try:
            sales_summary = analytics.get_sales_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sales", f"₹{sales_summary.get('total_sales', 0):,.0f}")
            with col2:
                st.metric("Pending Payments", f"₹{sales_summary.get('pending_amount', 0):,.0f}")
            with col3:
                st.metric("Total Transactions", sales_summary.get('total_transactions', 0))
            with col4:
                st.metric("Avg Sale", f"₹{sales_summary.get('avg_sale_value', 0):,.0f}")
                
        except Exception as e:
            st.error(f"Error loading dashboard data: {e}")
    else:
        st.warning("Database or analytics not available")