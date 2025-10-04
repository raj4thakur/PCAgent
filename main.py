import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime, timedelta
import sys
import hashlib

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # First run, show input for password
    if "password_correct" not in st.session_state:
        st.text_input(
            "Enter Access Key",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False
    
    # Password not correct, show input + error
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Enter Access Key", 
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("😕 Invalid access key")
        return False
    
    # Password correct
    else:
        return True

if not check_password():
    st.stop()






# Try to import plotly with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly not available. Charts will be displayed as tables.")

# Try to import custom modules with fallback
try:
    from database import DatabaseManager
    from data_processor import DataProcessor
    from analytics import Analytics
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.info("Please make sure all required files are in the same directory.")
    MODULES_AVAILABLE = False

# Page configuration with custom theme
st.set_page_config(
    page_title="Sales Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
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
    /* Responsive design */
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

# Initialize all components with error handling
@st.cache_resource
def init_database():
    """Initialize database only - this can be cached"""
    try:
        return DatabaseManager()
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return None

def get_data_processor(_db):
    """Get data processor instance"""
    try:
        return DataProcessor(_db)
    except Exception as e:
        st.error(f"Data Processor initialization failed: {e}")
        return None

def get_analytics(_db):
    """Get analytics instance"""
    try:
        return Analytics(_db)
    except Exception as e:
        st.error(f"Analytics initialization failed: {e}")
        return None

# Initialize components only if modules are available
if MODULES_AVAILABLE:
    try:
        if 'db' not in st.session_state:
            st.session_state.db = init_database()

        if st.session_state.db and 'data_processor' not in st.session_state:
            st.session_state.data_processor = get_data_processor(st.session_state.db)

        if st.session_state.db and 'analytics' not in st.session_state:
            st.session_state.analytics = get_analytics(st.session_state.db)

        # Assign to local variables for easier access
        db = st.session_state.db
        data_processor = st.session_state.data_processor
        analytics = st.session_state.analytics

    except Exception as e:
        st.error(f"Application initialization failed: {e}")
        db = None
        data_processor = None
        analytics = None
else:
    db = None
    data_processor = None
    analytics = None

def process_existing_files():
    """Process all existing Excel files in data folder"""
    if not data_processor:
        return []
        
    data_dir = "data"
    processed_files = []
    
    if os.path.exists(data_dir):
        excel_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.xls"))
        
        if excel_files:
            with st.spinner(f"Processing {len(excel_files)} Excel file(s)..."):
                for file_path in excel_files:
                    try:
                        file_name = os.path.basename(file_path)
                        if data_processor.process_excel_file(file_path):
                            processed_files.append(file_name)
                    except Exception as e:
                        st.error(f"Error processing {file_name}: {str(e)}")
    
    return processed_files

# Process existing files automatically when the app starts
if 'files_processed' not in st.session_state and data_processor:
    processed = process_existing_files()
    if processed:
        st.success(f"✅ Processed {len(processed)} files: {', '.join(processed)}")
    st.session_state.files_processed = True

# Color themes for different sections
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ffbb78'
}

def create_metric_card(value, label, icon="📊", color=COLORS['primary']):
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

def create_simple_chart(data, title, x_col, y_col):
    """Create a simple chart using Streamlit's native charts or fallback to table"""
    if PLOTLY_AVAILABLE and not data.empty:
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
        st.dataframe(data[[x_col, y_col]])
        return None

# Sidebar navigation with icons
st.sidebar.markdown("<h1 style='text-align: center;'>🚀 Sales Management</h1>", unsafe_allow_html=True)

page = st.sidebar.radio("Navigation", [
    "📊 Dashboard", "👥 Customers", "💰 Sales", "💳 Payments", 
    "🎯 Demos", "🤝 Distributors", "📤 Data Import", "📈 Reports"
], index=0)

def create_dashboard():
    """Create the main dashboard with metrics and charts"""
    st.markdown("<h1 class='main-header'>📊 Sales Dashboard</h1>", unsafe_allow_html=True)
    
    # Check if components are available
    if not analytics or not db:
        st.error("Analytics or Database not available. Please check the initialization.")
        return
    
    # Key Metrics
    try:
        sales_summary = analytics.get_sales_summary()
        demo_stats = analytics.get_demo_conversion_rates()
        customer_analysis = analytics.get_customer_analysis()
        payment_analysis = analytics.get_payment_analysis()
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        sales_summary = {'total_sales': 0, 'pending_amount': 0}
        demo_stats = {'conversion_rate': 0}
        customer_analysis = {'total_customers': 0}
        payment_analysis = {'total_pending': 0}
    
    # Top row metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            f"₹{sales_summary.get('total_sales', 0):,.0f}", 
            "Total Sales", "💰", COLORS['primary']
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            f"₹{sales_summary.get('pending_amount', 0):,.0f}", 
            "Pending Payments", "⏳", COLORS['warning']
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            f"{demo_stats.get('conversion_rate', 0):.1f}%", 
            "Demo Conversion", "🎯", COLORS['success']
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            f"{customer_analysis.get('total_customers', 0)}", 
            "Total Customers", "👥", COLORS['secondary']
        ), unsafe_allow_html=True)
    
    # Charts and Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='section-header'>Sales Trend</h3>", unsafe_allow_html=True)
        try:
            sales_trend = analytics.get_sales_trend()
            if not sales_trend.empty:
                if PLOTLY_AVAILABLE:
                    fig = px.line(sales_trend, x='sale_date', y='total_amount', 
                                 title='Daily Sales Trend', color_discrete_sequence=[COLORS['primary']])
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(sales_trend[['sale_date', 'total_amount']])
            else:
                st.info("No sales data available for trend analysis")
        except Exception as e:
            st.error(f"Error loading sales trend: {e}")
    
    with col2:
        st.markdown("<h3 class='section-header'>Payment Status</h3>", unsafe_allow_html=True)
        try:
            payment_data = analytics.get_payment_distribution()
            if not payment_data.empty:
                if PLOTLY_AVAILABLE:
                    fig = px.pie(payment_data, values='amount', names='payment_method',
                                title='Payment Methods Distribution', color_discrete_sequence=px.colors.qualitative.Set3)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.dataframe(payment_data[['payment_method', 'amount']])
            else:
                st.info("No payment data available")
        except Exception as e:
            st.error(f"Error loading payment data: {e}")
    
    # Recent Activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='section-header'>Recent Sales</h3>", unsafe_allow_html=True)
        try:
            recent_sales = db.get_dataframe('sales', '''
            SELECT s.*, c.name as customer_name, c.village
            FROM sales s 
            JOIN customers c ON s.customer_id = c.customer_id 
            ORDER BY s.created_date DESC LIMIT 8
            ''')
            if not recent_sales.empty:
                st.dataframe(recent_sales[['invoice_no', 'customer_name', 'village', 'total_amount', 'sale_date']], 
                            use_container_width=True)
            else:
                st.info("No recent sales found")
        except Exception as e:
            st.error(f"Error loading recent sales: {e}")
    
    with col2:
        st.markdown("<h3 class='section-header'>Upcoming Demos</h3>", unsafe_allow_html=True)
        try:
            upcoming_demos = db.get_dataframe('demos', '''
            SELECT d.*, c.name as customer_name, p.product_name
            FROM demos d
            LEFT JOIN customers c ON d.customer_id = c.customer_id
            LEFT JOIN products p ON d.product_id = p.product_id
            WHERE d.demo_date >= date('now')
            ORDER BY d.demo_date ASC LIMIT 8
            ''')
            if not upcoming_demos.empty:
                st.dataframe(upcoming_demos[['customer_name', 'product_name', 'demo_date', 'follow_up_date']], 
                            use_container_width=True)
            else:
                st.info("No upcoming demos scheduled")
        except Exception as e:
            st.error(f"Error loading upcoming demos: {e}")

# Show warning if modules are not available
if not MODULES_AVAILABLE:
    st.warning("""
    ⚠️ **Some modules are not available.**
    
    Please make sure the following files are in the same directory:
    - `database.py`
    - `data_processor.py` 
    - `analytics.py`
    
    The app will run in limited functionality mode.
    """)

# Page routing with error handling
try:
    if page == "📊 Dashboard":
        create_dashboard()

    elif page == "👥 Customers":
        st.title("👥 Customer Management")
        
        if not db:
            st.error("Database not available. Please check initialization.")
        else:
            with st.form("add_customer"):
                st.subheader("Add New Customer")
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Name*")
                    mobile = st.text_input("Mobile")
                    customer_code = st.text_input("Customer Code (optional)")
                with col2:
                    village = st.text_input("Village")
                    taluka = st.text_input("Taluka")
                    district = st.text_input("District")
                
                submitted = st.form_submit_button("Add Customer")
                if submitted and name:
                    try:
                        db.add_customer(name, mobile, village, taluka, district, customer_code)
                        st.success("✅ Customer added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding customer: {e}")
                elif submitted:
                    st.error("Please fill at least the name field")
            
            st.subheader("Customer List")
            try:
                customers = db.get_dataframe('customers')
                if not customers.empty:
                    st.dataframe(customers, use_container_width=True)
                else:
                    st.info("No customers found")
            except Exception as e:
                st.error(f"Error loading customers: {e}")

    elif page == "💰 Sales":
        st.title("💰 Sales Management")
        
        if not db:
            st.error("Database not available. Please check initialization.")
        else:
            with st.form("add_sale"):
                st.subheader("Create New Sale")
                
                try:
                    customers = db.get_dataframe('customers')
                    if not customers.empty:
                        customer_options = {f"{row['name']} ({row['village']})": row['customer_id'] 
                                          for _, row in customers.iterrows()}
                        selected_customer = st.selectbox("Customer*", options=list(customer_options.keys()))
                        customer_id = customer_options[selected_customer] if selected_customer else None
                    else:
                        st.warning("No customers found. Please add customers first.")
                        customer_id = None
                except Exception as e:
                    st.error(f"Error loading customers: {e}")
                    customer_id = None
                
                col1, col2 = st.columns(2)
                with col1:
                    invoice_no = st.text_input("Invoice Number*")
                    sale_date = st.date_input("Sale Date", datetime.now())
                
                st.subheader("Add Products to Sale")
                try:
                    products = db.get_dataframe('products')
                    sale_items = []
                    
                    if not products.empty:
                        product_options = {row['product_name']: row['product_id'] for _, row in products.iterrows()}
                        
                        for i in range(3):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                selected_product = st.selectbox(f"Product {i+1}", 
                                                              options=[""] + list(product_options.keys()),
                                                              key=f"product_{i}")
                            with col2:
                                quantity = st.number_input(f"Quantity {i+1}", min_value=0, value=0, key=f"qty_{i}")
                            with col3:
                                rate = st.number_input(f"Rate {i+1}", min_value=0.0, value=0.0, key=f"rate_{i}")
                            
                            if selected_product and quantity > 0:
                                sale_items.append({
                                    'product_id': product_options[selected_product],
                                    'quantity': quantity,
                                    'rate': rate
                                })
                    else:
                        st.warning("No products found.")
                except Exception as e:
                    st.error(f"Error loading products: {e}")
                    sale_items = []
                
                submitted = st.form_submit_button("Add Sale")
                if submitted and customer_id and sale_items and invoice_no:
                    try:
                        sale_id = db.add_sale(invoice_no, customer_id, sale_date, sale_items)
                        st.success(f"✅ Sale added successfully! Sale ID: {sale_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding sale: {e}")
                elif submitted:
                    st.error("Please fill all required fields (*) and add at least one product")
            
            st.subheader("Sales History")
            try:
                sales = db.get_dataframe('sales', '''
                SELECT s.*, c.name as customer_name 
                FROM sales s 
                JOIN customers c ON s.customer_id = c.customer_id
                ORDER BY s.created_date DESC
                ''')
                if not sales.empty:
                    st.dataframe(sales, use_container_width=True)
                else:
                    st.info("No sales found")
            except Exception as e:
                st.error(f"Error loading sales: {e}")

    elif page == "💳 Payments":
        st.title("💳 Payment Management")
        
        if not db:
            st.error("Database not available. Please check initialization.")
        else:
            try:
                pending_payments = db.get_pending_payments()
                
                if not pending_payments.empty:
                    st.subheader("Pending Payments")
                    st.dataframe(pending_payments, use_container_width=True)
                    
                    with st.form("add_payment"):
                        st.subheader("Record Payment")
                        
                        sales_options = {f"Invoice {row['invoice_no']} - {row['customer_name']} (₹{row['pending_amount']:,.2f})": row['sale_id'] 
                                       for _, row in pending_payments.iterrows()}
                        selected_sale = st.selectbox("Select Sale", options=list(sales_options.keys()))
                        sale_id = sales_options[selected_sale] if selected_sale else None
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            payment_date = st.date_input("Payment Date", datetime.now())
                            amount = st.number_input("Amount*", min_value=0.0)
                            payment_method = st.selectbox("Payment Method", ["Cash", "G-Pay", "Cheque", "Bank Transfer"])
                        with col2:
                            rrn = st.text_input("RRN (Reference)")
                            reference = st.text_input("Additional Reference")
                        
                        submitted = st.form_submit_button("Record Payment")
                        if submitted and sale_id and amount > 0:
                            try:
                                db.execute_query('''
                                INSERT INTO payments (sale_id, payment_date, payment_method, amount, rrn, reference)
                                VALUES (?, ?, ?, ?, ?, ?)
                                ''', (sale_id, payment_date, payment_method, amount, rrn, reference))
                                st.success("✅ Payment recorded successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error recording payment: {e}")
                        elif submitted:
                            st.error("Please select a sale and enter payment amount")
                else:
                    st.success("🎉 All payments are cleared! No pending payments.")
            except Exception as e:
                st.error(f"Error loading pending payments: {e}")

    elif page == "🎯 Demos":
        st.title("🎯 Demo Management")
        
        if not db:
            st.error("Database not available. Please check initialization.")
        else:
            with st.form("add_demo"):
                st.subheader("Schedule Demo")
                
                col1, col2 = st.columns(2)
                with col1:
                    try:
                        customers = db.get_dataframe('customers')
                        if not customers.empty:
                            customer_options = {f"{row['name']} ({row['village']})": row['customer_id'] 
                                              for _, row in customers.iterrows()}
                            selected_customer = st.selectbox("Customer*", options=list(customer_options.keys()))
                            customer_id = customer_options[selected_customer] if selected_customer else None
                        else:
                            st.warning("No customers found.")
                            customer_id = None
                    except Exception as e:
                        st.error(f"Error loading customers: {e}")
                        customer_id = None
                    
                    try:
                        distributors = db.get_dataframe('distributors')
                        if not distributors.empty:
                            distributor_options = {f"{row['name']}": row['distributor_id'] 
                                                 for _, row in distributors.iterrows()}
                            selected_distributor = st.selectbox("Distributor", options=list(distributor_options.keys()))
                            distributor_id = distributor_options[selected_distributor] if selected_distributor else None
                        else:
                            distributor_id = None
                    except Exception as e:
                        st.error(f"Error loading distributors: {e}")
                        distributor_id = None
                    
                with col2:
                    try:
                        products = db.get_dataframe('products')
                        if not products.empty:
                            product_options = {row['product_name']: row['product_id'] for _, row in products.iterrows()}
                            selected_product = st.selectbox("Product*", options=list(product_options.keys()))
                            product_id = product_options[selected_product] if selected_product else None
                        else:
                            st.warning("No products found.")
                            product_id = None
                    except Exception as e:
                        st.error(f"Error loading products: {e}")
                        product_id = None
                    
                    demo_date = st.date_input("Demo Date*", datetime.now())
                    follow_up_date = st.date_input("Follow-up Date", datetime.now() + timedelta(days=7))
                    quantity = st.number_input("Quantity Provided", min_value=1, value=1)
                
                notes = st.text_area("Notes")
                
                submitted = st.form_submit_button("Schedule Demo")
                if submitted and customer_id and product_id and demo_date:
                    try:
                        db.execute_query('''
                        INSERT INTO demos (customer_id, distributor_id, product_id, demo_date, 
                                         follow_up_date, quantity_provided, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (customer_id, distributor_id, product_id, demo_date, follow_up_date, quantity, notes))
                        st.success("✅ Demo scheduled successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error scheduling demo: {e}")
                elif submitted:
                    st.error("Please fill all required fields (*)")

    elif page == "🤝 Distributors":
        st.title("🤝 Distributor Management")
        
        if not db:
            st.error("Database not available. Please check initialization.")
        else:
            with st.form("add_distributor"):
                st.subheader("Add New Distributor")
                
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Distributor Name*")
                    village = st.text_input("Village")
                    taluka = st.text_input("Taluka")
                    district = st.text_input("District")
                with col2:
                    mantri_name = st.text_input("Mantri Name")
                    mantri_mobile = st.text_input("Mantri Mobile")
                    sabhasad_count = st.number_input("Sabhasad Count", min_value=0, value=0)
                    contact_in_group = st.number_input("Contacts in Group", min_value=0, value=0)
                
                submitted = st.form_submit_button("Add Distributor")
                if submitted and name:
                    try:
                        db.execute_query('''
                        INSERT INTO distributors (name, village, taluka, district, mantri_name, 
                                                mantri_mobile, sabhasad_count, contact_in_group)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (name, village, taluka, district, mantri_name, mantri_mobile, 
                             sabhasad_count, contact_in_group))
                        st.success("✅ Distributor added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding distributor: {e}")
                elif submitted:
                    st.error("Please enter distributor name")
            
            st.subheader("Distributor List")
            try:
                distributors = db.get_dataframe('distributors')
                if not distributors.empty:
                    st.dataframe(distributors, use_container_width=True)
                else:
                    st.info("No distributors found")
            except Exception as e:
                st.error(f"Error loading distributors: {e}")

    elif page == "📤 Data Import":
        st.title("📤 Data Import & Processing")
        
        if not data_processor:
            st.error("Data processor not available. Please check initialization.")
        else:
            data_dir = "data"
            if os.path.exists(data_dir):
                excel_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.xls"))
                
                if excel_files:
                    st.subheader("📁 Existing Files in Data Folder")
                    
                    for file_path in excel_files:
                        file_name = os.path.basename(file_path)
                        file_size = os.path.getsize(file_path) / 1024
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"**{file_name}**")
                            st.write(f"Size: {file_size:.1f} KB | Modified: {file_mtime.strftime('%Y-%m-%d %H:%M')}")
                        with col2:
                            if st.button(f"🔄 Process", key=f"process_{file_name}"):
                                try:
                                    if data_processor.process_excel_file(file_path):
                                        st.success(f"✅ Processed: {file_name}")
                                        st.rerun()
                                    else:
                                        st.warning(f"⚠️ No data processed from: {file_name}")
                                except Exception as e:
                                    st.error(f"❌ Error processing {file_name}: {str(e)}")
                        with col3:
                            if st.button(f"🗑️ Delete", key=f"delete_{file_name}"):
                                try:
                                    os.remove(file_path)
                                    st.success(f"✅ Deleted: {file_name}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting file: {e}")
                    
                    if st.button("🔄 Process All Files", type="primary"):
                        success_count = 0
                        for file_path in excel_files:
                            try:
                                if data_processor.process_excel_file(file_path):
                                    success_count += 1
                            except Exception as e:
                                st.error(f"Error processing {os.path.basename(file_path)}: {str(e)}")
                        st.success(f"✅ Processed {success_count}/{len(excel_files)} files successfully!")
                        if success_count > 0:
                            st.rerun()
                else:
                    st.info("No Excel files found in the data folder.")
            else:
                os.makedirs(data_dir, exist_ok=True)
                st.info("Data folder created. Upload Excel files to get started.")
            
            st.subheader("📤 Upload New Excel File")
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
            
            if uploaded_file:
                file_path = os.path.join("data", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"✅ File saved: {uploaded_file.name}")
                
                if st.button(f"🔄 Process {uploaded_file.name}"):
                    try:
                        if data_processor.process_excel_file(file_path):
                            st.success(f"✅ Processed: {uploaded_file.name}")
                            
                            # Show data preview
                            st.subheader("📊 Imported Data Preview")
                            try:
                                customers = db.get_dataframe('customers')
                                sales = db.get_dataframe('sales')
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Customers", len(customers))
                                    if not customers.empty:
                                        st.dataframe(customers.tail(3), use_container_width=True)
                                with col2:
                                    st.metric("Sales", len(sales))
                                    if not sales.empty:
                                        st.dataframe(sales.tail(3), use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading preview data: {e}")
                            
                            st.rerun()
                        else:
                            st.warning(f"⚠️ No data processed from: {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")

    elif page == "📈 Reports":
        st.title("📈 Advanced Reports")
        
        if not db:
            st.error("Database not available. Please check initialization.")
        else:
            tab1, tab2, tab3, tab4 = st.tabs(["Sales Report", "Demo Report", "Payment Report", "Customer Report"])
            
            with tab1:
                st.subheader("Sales Report")
                try:
                    sales_report = db.get_dataframe('sales', '''
                    SELECT s.invoice_no, s.sale_date, c.name as customer_name, c.village,
                           s.total_amount, s.payment_status, 
                           COALESCE(SUM(p.amount), 0) as paid_amount,
                           (s.total_amount - COALESCE(SUM(p.amount), 0)) as pending_amount
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.customer_id
                    LEFT JOIN payments p ON s.sale_id = p.sale_id
                    GROUP BY s.sale_id
                    ORDER BY s.sale_date DESC
                    ''')
                    if not sales_report.empty:
                        st.dataframe(sales_report, use_container_width=True)
                        
                        if st.button("Export Sales Report to CSV", key="export_sales"):
                            sales_report.to_csv("sales_report.csv", index=False)
                            st.success("Sales report exported successfully!")
                    else:
                        st.info("No sales data available")
                except Exception as e:
                    st.error(f"Error loading sales report: {e}")
            
            with tab2:
                st.subheader("Demo Conversion Report")
                try:
                    demo_report = db.get_dataframe('demos', '''
                    SELECT d.demo_date, c.name as customer_name, c.village,
                           p.product_name, d.quantity_provided, d.conversion_status,
                           dist.name as distributor_name, d.follow_up_date
                    FROM demos d
                    LEFT JOIN customers c ON d.customer_id = c.customer_id
                    LEFT JOIN products p ON d.product_id = p.product_id
                    LEFT JOIN distributors dist ON d.distributor_id = dist.distributor_id
                    ORDER BY d.demo_date DESC
                    ''')
                    if not demo_report.empty:
                        st.dataframe(demo_report, use_container_width=True)
                    else:
                        st.info("No demo data available")
                except Exception as e:
                    st.error(f"Error loading demo report: {e}")
            
            with tab3:
                st.subheader("Payment Report")
                try:
                    payment_report = db.get_dataframe('payments', '''
                    SELECT p.*, s.invoice_no, c.name as customer_name, c.village
                    FROM payments p
                    LEFT JOIN sales s ON p.sale_id = s.sale_id
                    LEFT JOIN customers c ON s.customer_id = c.customer_id
                    ORDER BY p.payment_date DESC
                    ''')
                    if not payment_report.empty:
                        st.dataframe(payment_report, use_container_width=True)
                    else:
                        st.info("No payment data available")
                except Exception as e:
                    st.error(f"Error loading payment report: {e}")
            
            with tab4:
                st.subheader("Customer Report")
                try:
                    customer_report = db.get_dataframe('customers', '''
                    SELECT c.*, 
                           COUNT(s.sale_id) as total_purchases,
                           COALESCE(SUM(s.total_amount), 0) as total_spent,
                           MAX(s.sale_date) as last_purchase_date
                    FROM customers c
                    LEFT JOIN sales s ON c.customer_id = s.customer_id
                    GROUP BY c.customer_id
                    ORDER BY total_spent DESC
                    ''')
                    if not customer_report.empty:
                        st.dataframe(customer_report, use_container_width=True)
                    else:
                        st.info("No customer data available")
                except Exception as e:
                    st.error(f"Error loading customer report: {e}")

except Exception as e:
    st.error(f"Application error: {e}")
    st.info("Please check the console for more details.")

# Footer with database stats
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Database Statistics")

try:
    if db:
        customers_count = len(db.get_dataframe('customers'))
        sales_count = len(db.get_dataframe('sales'))
        distributors_count = len(db.get_dataframe('distributors'))
        demos_count = len(db.get_dataframe('demos'))
        
        st.sidebar.metric("👥 Customers", customers_count)
        st.sidebar.metric("💰 Sales", sales_count)
        st.sidebar.metric("🤝 Distributors", distributors_count)
        st.sidebar.metric("🎯 Demos", demos_count)
    else:
        st.sidebar.error("Database not available")
    
except Exception as e:
    st.sidebar.error("Database connection issue")

st.sidebar.markdown("---")
st.sidebar.info("🚀 Sales Management System v2.0")