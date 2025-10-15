# pages/dashboard.py
import streamlit as st
from utils.styling import create_metric_card, COLORS
import plotly.express as px

def create_dashboard(db, analytics):
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
                fig = px.line(sales_trend, x='sale_date', y='total_amount', 
                             title='Daily Sales Trend', color_discrete_sequence=[COLORS['primary']])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sales data available for trend analysis")
        except Exception as e:
            st.error(f"Error loading sales trend: {e}")
    
    with col2:
        st.markdown("<h3 class='section-header'>Payment Status</h3>", unsafe_allow_html=True)
        try:
            payment_data = analytics.get_payment_distribution()
            if not payment_data.empty:
                fig = px.pie(payment_data, values='amount', names='payment_method',
                            title='Payment Methods Distribution', color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, use_container_width=True)
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