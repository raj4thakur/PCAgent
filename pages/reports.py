# pages/reports.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def show_reports_page(db, whatsapp_manager=None):
    """Show comprehensive business intelligence and reporting"""
    st.title("📈 Business Intelligence & Reports")
    
    if not db:
        st.error("Database not available. Please check initialization.")
        return
    
    # Tabs for different report types
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Sales Reports", "👥 Customer Reports", 
                                           "🤝 Distributor Reports", "💰 Financial Reports", 
                                           "🎯 Performance Reports"])
    
    with tab1:
        show_sales_reports_tab(db)
    
    with tab2:
        show_customer_reports_tab(db)
    
    with tab3:
        show_distributor_reports_tab(db)
    
    with tab4:
        show_financial_reports_tab(db)
    
    with tab5:
        show_performance_reports_tab(db)

def show_sales_reports_tab(db):
    """Show sales-related reports and analytics"""
    st.subheader("📊 Sales Performance Reports")
    
    # Date range selection
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    with col3:
        report_granularity = st.selectbox("Granularity", ["Daily", "Weekly", "Monthly"])
    
    try:
        # Sales Summary
        st.subheader("💰 Sales Summary")
        sales_summary = get_sales_summary(db, start_date, end_date)
        
        if sales_summary:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Sales", f"₹{sales_summary.get('total_sales', 0):,.0f}")
            with col2:
                st.metric("Total Revenue", f"₹{sales_summary.get('total_revenue', 0):,.0f}")
            with col3:
                st.metric("Transactions", sales_summary.get('total_transactions', 0))
            with col4:
                st.metric("Avg Sale Value", f"₹{sales_summary.get('avg_sale_value', 0):,.0f}")
            with col5:
                st.metric("Unique Customers", sales_summary.get('unique_customers', 0))
        
        # Sales Trend Chart
        st.subheader("📈 Sales Trend")
        sales_trend = get_sales_trend(db, start_date, end_date, report_granularity)
        
        if not sales_trend.empty:
            fig = px.line(sales_trend, x='period', y='total_amount', 
                         title=f'Sales Trend ({report_granularity})',
                         labels={'period': 'Period', 'total_amount': 'Sales Amount (₹)'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Product Performance
        st.subheader("📦 Product Performance")
        product_performance = get_product_performance(db, start_date, end_date)
        
        if not product_performance.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top products by revenue
                top_products = product_performance.head(10)
                fig = px.bar(top_products, x='product_name', y='total_revenue',
                           title='Top 10 Products by Revenue',
                           labels={'product_name': 'Product', 'total_revenue': 'Revenue (₹)'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Product sales distribution
                fig = px.pie(product_performance, values='total_quantity', names='product_name',
                           title='Product Sales Distribution (Quantity)')
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed product table
            st.dataframe(product_performance, use_container_width=True)
        
        # Village-wise Sales
        st.subheader("🗺️ Village-wise Sales Performance")
        village_sales = get_village_sales(db, start_date, end_date)
        
        if not village_sales.empty:
            fig = px.bar(village_sales.head(10), x='village', y='total_revenue',
                       title='Top 10 Villages by Sales Revenue',
                       labels={'village': 'Village', 'total_revenue': 'Revenue (₹)'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Village sales table
            st.dataframe(village_sales, use_container_width=True)
        
        # Export options
        st.subheader("📤 Export Sales Report")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Sales Data to CSV"):
                export_sales_data(db, start_date, end_date)
        
        with col2:
            if st.button("📈 Generate Sales PDF Report"):
                generate_sales_pdf_report(db, start_date, end_date)
                
    except Exception as e:
        st.error(f"Error generating sales reports: {e}")

def get_sales_summary(db, start_date, end_date):
    """Get sales summary statistics"""
    try:
        query = '''
        SELECT 
            COUNT(*) as total_transactions,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_sale_value,
            COUNT(DISTINCT customer_id) as unique_customers,
            SUM(total_liters) as total_liters_sold
        FROM sales 
        WHERE sale_date BETWEEN ? AND ?
        '''
        
        result = db.execute_query(query, (start_date, end_date), log_action=False)
        
        if result:
            row = result[0]
            return {
                'total_transactions': row[0] or 0,
                'total_revenue': row[1] or 0,
                'avg_sale_value': row[2] or 0,
                'unique_customers': row[3] or 0,
                'total_liters_sold': row[4] or 0
            }
        return {}
        
    except Exception as e:
        st.error(f"Error getting sales summary: {e}")
        return {}

def get_sales_trend(db, start_date, end_date, granularity):
    """Get sales trend data"""
    try:
        if granularity == "Daily":
            group_by = "DATE(sale_date)"
            period_format = "sale_date"
        elif granularity == "Weekly":
            group_by = "STRFTIME('%Y-%W', sale_date)"
            period_format = "STRFTIME('%Y-W%W', sale_date) as period"
        else:  # Monthly
            group_by = "STRFTIME('%Y-%m', sale_date)"
            period_format = "STRFTIME('%Y-%m', sale_date) as period"
        
        query = f'''
        SELECT {period_format}, 
               SUM(total_amount) as total_amount,
               COUNT(*) as transaction_count,
               AVG(total_amount) as avg_amount
        FROM sales 
        WHERE sale_date BETWEEN ? AND ?
        GROUP BY {group_by}
        ORDER BY period
        '''
        
        return db.get_dataframe('sales', query, params=(start_date, end_date))
        
    except Exception as e:
        st.error(f"Error getting sales trend: {e}")
        return pd.DataFrame()

def get_product_performance(db, start_date, end_date):
    """Get product performance data"""
    try:
        query = '''
        SELECT 
            p.product_name,
            p.packing_type,
            p.capacity_ltr,
            COUNT(si.item_id) as times_sold,
            SUM(si.quantity) as total_quantity,
            SUM(si.amount) as total_revenue,
            AVG(si.rate) as avg_rate
        FROM sale_items si
        JOIN products p ON si.product_id = p.product_id
        JOIN sales s ON si.sale_id = s.sale_id
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY p.product_id, p.product_name, p.packing_type, p.capacity_ltr
        ORDER BY total_revenue DESC
        '''
        
        return db.get_dataframe('sale_items', query, params=(start_date, end_date))
        
    except Exception as e:
        st.error(f"Error getting product performance: {e}")
        return pd.DataFrame()

def get_village_sales(db, start_date, end_date):
    """Get village-wise sales data"""
    try:
        query = '''
        SELECT 
            c.village,
            COUNT(DISTINCT s.customer_id) as unique_customers,
            COUNT(s.sale_id) as total_transactions,
            SUM(s.total_amount) as total_revenue,
            AVG(s.total_amount) as avg_sale_value
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        WHERE s.sale_date BETWEEN ? AND ?
        AND c.village IS NOT NULL AND c.village != ''
        GROUP BY c.village
        ORDER BY total_revenue DESC
        '''
        
        return db.get_dataframe('sales', query, params=(start_date, end_date))
        
    except Exception as e:
        st.error(f"Error getting village sales: {e}")
        return pd.DataFrame()

def show_customer_reports_tab(db):
    """Show customer-related reports and analytics"""
    st.subheader("👥 Customer Intelligence Reports")
    
    try:
        # Customer Overview
        st.subheader("📋 Customer Overview")
        customer_overview = get_customer_overview(db)
        
        if customer_overview:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Customers", customer_overview.get('total_customers', 0))
            with col2:
                st.metric("Active Customers", customer_overview.get('active_customers', 0))
            with col3:
                st.metric("Avg Customer Value", f"₹{customer_overview.get('avg_customer_value', 0):,.0f}")
            with col4:
                st.metric("Repeat Customer Rate", f"{customer_overview.get('repeat_rate', 0):.1f}%")
        
        # Top Customers
        st.subheader("🏆 Top Customers by Spending")
        top_customers = get_top_customers(db)
        
        if not top_customers.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(top_customers.head(10), x='name', y='total_spent',
                           title='Top 10 Customers by Total Spending',
                           labels={'name': 'Customer', 'total_spent': 'Total Spent (₹)'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Customer segmentation by spending
                spending_brackets = categorize_customers_by_spending(top_customers)
                fig = px.pie(values=spending_brackets.values, names=spending_brackets.index,
                           title='Customer Segmentation by Spending')
                st.plotly_chart(fig, use_container_width=True)
            
            # Customer details table
            st.dataframe(top_customers, use_container_width=True)
        
        # Customer Acquisition Trend
        st.subheader("📈 Customer Acquisition Trend")
        acquisition_trend = get_customer_acquisition_trend(db)
        
        if not acquisition_trend.empty:
            fig = px.line(acquisition_trend, x='month', y='new_customers',
                         title='Monthly Customer Acquisition',
                         labels={'month': 'Month', 'new_customers': 'New Customers'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Customer Location Analysis
        st.subheader("🗺️ Customer Geographic Distribution")
        customer_geo = get_customer_geographic_data(db)
        
        if not customer_geo.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Village-wise customer count
                village_customers = customer_geo.groupby('village').size().reset_index(name='customer_count')
                village_customers = village_customers.sort_values('customer_count', ascending=False).head(10)
                
                fig = px.bar(village_customers, x='village', y='customer_count',
                           title='Top 10 Villages by Customer Count',
                           labels={'village': 'Village', 'customer_count': 'Number of Customers'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Taluka-wise distribution
                taluka_customers = customer_geo.groupby('taluka').size().reset_index(name='customer_count')
                
                if not taluka_customers.empty:
                    fig = px.pie(taluka_customers, values='customer_count', names='taluka',
                               title='Customer Distribution by Taluka')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Customer Lifetime Value Analysis
        st.subheader("💰 Customer Lifetime Value Analysis")
        clv_data = get_customer_lifetime_value(db)
        
        if not clv_data.empty:
            st.dataframe(clv_data, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error generating customer reports: {e}")

def get_customer_overview(db):
    """Get customer overview statistics"""
    try:
        # Total customers
        total_customers = db.execute_query(
            "SELECT COUNT(*) FROM customers", log_action=False
        )[0][0]
        
        # Customers with purchases
        active_customers = db.execute_query(
            "SELECT COUNT(DISTINCT customer_id) FROM sales", log_action=False
        )[0][0]
        
        # Average customer value
        avg_value_result = db.execute_query(
            "SELECT AVG(total_amount) FROM sales", log_action=False
        )
        avg_customer_value = avg_value_result[0][0] if avg_value_result else 0
        
        # Repeat customer rate
        repeat_customers = db.execute_query(
            "SELECT COUNT(*) FROM (SELECT customer_id FROM sales GROUP BY customer_id HAVING COUNT(*) > 1)",
            log_action=False
        )[0][0]
        
        repeat_rate = (repeat_customers / active_customers * 100) if active_customers > 0 else 0
        
        return {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'avg_customer_value': avg_customer_value or 0,
            'repeat_rate': repeat_rate
        }
        
    except Exception as e:
        st.error(f"Error getting customer overview: {e}")
        return {}

def get_top_customers(db, limit=20):
    """Get top customers by spending"""
    try:
        query = '''
        SELECT 
            c.customer_id,
            c.name,
            c.village,
            c.taluka,
            c.mobile,
            COUNT(s.sale_id) as total_purchases,
            SUM(s.total_amount) as total_spent,
            MAX(s.sale_date) as last_purchase_date
        FROM customers c
        JOIN sales s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.name, c.village, c.taluka, c.mobile
        ORDER BY total_spent DESC
        LIMIT ?
        '''
        
        return db.get_dataframe('customers', query, params=(limit,))
        
    except Exception as e:
        st.error(f"Error getting top customers: {e}")
        return pd.DataFrame()

def categorize_customers_by_spending(customers_df):
    """Categorize customers by spending levels"""
    try:
        if customers_df.empty:
            return pd.Series()
        
        bins = [0, 1000, 5000, 10000, float('inf')]
        labels = ['Low (<1K)', 'Medium (1K-5K)', 'High (5K-10K)', 'VIP (>10K)']
        
        customers_df['spending_category'] = pd.cut(
            customers_df['total_spent'], bins=bins, labels=labels, right=False
        )
        
        return customers_df['spending_category'].value_counts()
        
    except Exception as e:
        st.error(f"Error categorizing customers: {e}")
        return pd.Series()

def get_customer_acquisition_trend(db):
    """Get customer acquisition trend"""
    try:
        query = '''
        SELECT 
            STRFTIME('%Y-%m', created_date) as month,
            COUNT(*) as new_customers
        FROM customers
        GROUP BY STRFTIME('%Y-%m', created_date)
        ORDER BY month
        '''
        
        return db.get_dataframe('customers', query)
        
    except Exception as e:
        st.error(f"Error getting acquisition trend: {e}")
        return pd.DataFrame()

def get_customer_geographic_data(db):
    """Get customer geographic distribution"""
    try:
        return db.get_dataframe('customers', '''
        SELECT village, taluka, district, COUNT(*) as customer_count
        FROM customers
        WHERE village IS NOT NULL AND village != ''
        GROUP BY village, taluka, district
        ORDER BY customer_count DESC
        ''')
        
    except Exception as e:
        st.error(f"Error getting geographic data: {e}")
        return pd.DataFrame()

def get_customer_lifetime_value(db):
    """Calculate customer lifetime value"""
    try:
        query = '''
        SELECT 
            c.customer_id,
            c.name,
            c.village,
            COUNT(s.sale_id) as purchase_frequency,
            SUM(s.total_amount) as total_value,
            AVG(s.total_amount) as avg_order_value,
            JULIANDAY(MAX(s.sale_date)) - JULIANDAY(MIN(s.sale_date)) as customer_tenure_days,
            CASE 
                WHEN COUNT(s.sale_id) > 0 THEN 
                    SUM(s.total_amount) / (COUNT(s.sale_id) * GREATEST((JULIANDAY(MAX(s.sale_date)) - JULIANDAY(MIN(s.sale_date)))/30, 1))
                ELSE 0 
            END as clv
        FROM customers c
        LEFT JOIN sales s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.name, c.village
        HAVING total_value > 0
        ORDER BY clv DESC
        '''
        
        return db.get_dataframe('customers', query)
        
    except Exception as e:
        st.error(f"Error calculating CLV: {e}")
        return pd.DataFrame()

def show_distributor_reports_tab(db):
    """Show distributor-related reports and analytics"""
    st.subheader("🤝 Distributor Performance Reports")
    
    try:
        # Distributor Overview
        st.subheader("📋 Distributor Network Overview")
        distributor_overview = get_distributor_overview(db)
        
        if distributor_overview:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Distributors", distributor_overview.get('total_distributors', 0))
            with col2:
                st.metric("Active Distributors", distributor_overview.get('active_distributors', 0))
            with col3:
                st.metric("Total Sabhasad", distributor_overview.get('total_sabhasad', 0))
            with col4:
                st.metric("Network Size", distributor_overview.get('network_size', 0))
        
        # Top Performers
        st.subheader("🏆 Top Performing Distributors")
        top_distributors = get_top_distributors(db)
        
        if not top_distributors.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(top_distributors.head(10), x='name', y='sabhasad_count',
                           title='Top 10 Distributors by Sabhasad Count',
                           labels={'name': 'Distributor', 'sabhasad_count': 'Sabhasad Count'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Performance tiers
                tier_distribution = top_distributors['performance_tier'].value_counts()
                fig = px.pie(values=tier_distribution.values, names=tier_distribution.index,
                           title='Distributor Performance Tier Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            # Distributor details table
            st.dataframe(top_distributors, use_container_width=True)
        
        # Territory Coverage
        st.subheader("🗺️ Territory Coverage Analysis")
        territory_coverage = get_territory_coverage(db)
        
        if not territory_coverage.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(territory_coverage.head(10), x='village', y='distributor_count',
                           title='Villages with Multiple Distributors',
                           labels={'village': 'Village', 'distributor_count': 'Distributor Count'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Coverage status
                coverage_status = {
                    'Covered Villages': len(territory_coverage[territory_coverage['distributor_count'] > 0]),
                    'Uncovered Villages': len(territory_coverage[territory_coverage['distributor_count'] == 0])
                }
                
                fig = px.pie(values=coverage_status.values(), names=coverage_status.keys(),
                           title='Village Coverage Status')
                st.plotly_chart(fig, use_container_width=True)
        
        # Growth Potential Analysis
        st.subheader("📈 Growth Potential Analysis")
        growth_potential = get_growth_potential(db)
        
        if not growth_potential.empty:
            st.dataframe(growth_potential, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error generating distributor reports: {e}")

def get_distributor_overview(db):
    """Get distributor network overview"""
    try:
        distributors = db.get_dataframe('distributors', 'SELECT * FROM distributors')
        
        if distributors.empty:
            return {}
        
        total_distributors = len(distributors)
        active_distributors = len(distributors[distributors['sabhasad_count'] > 0])
        total_sabhasad = distributors['sabhasad_count'].sum()
        network_size = total_distributors + total_sabhasad
        
        return {
            'total_distributors': total_distributors,
            'active_distributors': active_distributors,
            'total_sabhasad': total_sabhasad,
            'network_size': network_size
        }
        
    except Exception as e:
        st.error(f"Error getting distributor overview: {e}")
        return {}

def get_top_distributors(db, limit=20):
    """Get top performing distributors"""
    try:
        distributors = db.get_dataframe('distributors', '''
        SELECT *, 
               (sabhasad_count + contact_in_group) as network_score
        FROM distributors 
        ORDER BY sabhasad_count DESC 
        LIMIT ?
        ''', params=(limit,))
        
        if not distributors.empty:
            # Add performance tier
            distributors['performance_tier'] = distributors['sabhasad_count'].apply(
                lambda x: 'Platinum' if x >= 20 else 'Gold' if x >= 10 else 'Silver' if x >= 5 else 'Bronze'
            )
        
        return distributors
        
    except Exception as e:
        st.error(f"Error getting top distributors: {e}")
        return pd.DataFrame()

def get_territory_coverage(db):
    """Get territory coverage analysis"""
    try:
        # Get all villages from customers
        customer_villages = db.get_dataframe('customers', '''
        SELECT DISTINCT village 
        FROM customers 
        WHERE village IS NOT NULL AND village != ''
        ''')
        
        # Get distributor villages
        distributor_villages = db.get_dataframe('distributors', '''
        SELECT village, COUNT(*) as distributor_count
        FROM distributors 
        WHERE village IS NOT NULL AND village != ''
        GROUP BY village
        ''')
        
        # Merge to see coverage
        if not customer_villages.empty:
            if not distributor_villages.empty:
                coverage = pd.merge(customer_villages, distributor_villages, on='village', how='left')
            else:
                coverage = customer_villages.copy()
                coverage['distributor_count'] = 0
            
            coverage['distributor_count'] = coverage['distributor_count'].fillna(0)
            return coverage.sort_values('distributor_count', ascending=False)
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error getting territory coverage: {e}")
        return pd.DataFrame()

def get_growth_potential(db):
    """Get distributor growth potential analysis"""
    try:
        return db.get_dataframe('distributors', '''
        SELECT 
            name,
            village,
            sabhasad_count,
            contact_in_group,
            (contact_in_group - sabhasad_count) as conversion_potential,
            CASE 
                WHEN sabhasad_count = 0 THEN contact_in_group * 0.3
                ELSE (contact_in_group / sabhasad_count - 1) * sabhasad_count
            END as growth_opportunity
        FROM distributors
        WHERE contact_in_group > sabhasad_count
        ORDER BY growth_opportunity DESC
        ''')
        
    except Exception as e:
        st.error(f"Error getting growth potential: {e}")
        return pd.DataFrame()

def show_financial_reports_tab(db):
    """Show financial reports and analytics"""
    st.subheader("💰 Financial Performance Reports")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=90), key="financial_start")
    with col2:
        end_date = st.date_input("End Date", datetime.now(), key="financial_end")
    
    try:
        # Financial Summary
        st.subheader("📋 Financial Summary")
        financial_summary = get_financial_summary(db, start_date, end_date)
        
        if financial_summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Revenue", f"₹{financial_summary.get('total_revenue', 0):,.0f}")
            with col2:
                st.metric("Total Payments", f"₹{financial_summary.get('total_payments', 0):,.0f}")
            with col3:
                st.metric("Pending Amount", f"₹{financial_summary.get('pending_amount', 0):,.0f}")
            with col4:
                collection_rate = financial_summary.get('collection_rate', 0)
                st.metric("Collection Rate", f"{collection_rate:.1f}%")
        
        # Revenue vs Payments Trend
        st.subheader("📈 Revenue vs Payments Trend")
        financial_trend = get_financial_trend(db, start_date, end_date)
        
        if not financial_trend.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=financial_trend['period'], y=financial_trend['revenue'], 
                                   name='Revenue', line=dict(color='green')))
            fig.add_trace(go.Scatter(x=financial_trend['period'], y=financial_trend['payments'], 
                                   name='Payments', line=dict(color='blue')))
            fig.update_layout(title='Revenue vs Payments Trend', xaxis_title='Period', yaxis_title='Amount (₹)')
            st.plotly_chart(fig, use_container_width=True)
        
        # Payment Method Analysis
        st.subheader("💳 Payment Method Analysis")
        payment_methods = get_payment_methods_analysis(db, start_date, end_date)
        
        if not payment_methods.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(payment_methods, values='total_amount', names='payment_method',
                           title='Payment Methods Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(payment_methods, x='payment_method', y='transaction_count',
                           title='Transactions by Payment Method',
                           labels={'payment_method': 'Payment Method', 'transaction_count': 'Number of Transactions'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Aging Analysis
        st.subheader("⏳ Accounts Receivable Aging")
        aging_analysis = get_aging_analysis(db)
        
        if not aging_analysis.empty:
            st.dataframe(aging_analysis, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error generating financial reports: {e}")

def get_financial_summary(db, start_date, end_date):
    """Get financial summary"""
    try:
        # Total revenue
        revenue_result = db.execute_query(
            "SELECT SUM(total_amount) FROM sales WHERE sale_date BETWEEN ? AND ?",
            (start_date, end_date), log_action=False
        )
        total_revenue = revenue_result[0][0] or 0 if revenue_result else 0
        
        # Total payments
        payments_result = db.execute_query(
            "SELECT SUM(amount) FROM payments WHERE payment_date BETWEEN ? AND ? AND status = 'Completed'",
            (start_date, end_date), log_action=False
        )
        total_payments = payments_result[0][0] or 0 if payments_result else 0
        
        # Pending amount
        pending_result = db.execute_query(
            "SELECT SUM(total_amount - COALESCE((SELECT SUM(amount) FROM payments WHERE payments.sale_id = sales.sale_id AND status = 'Completed'), 0)) FROM sales WHERE sale_date BETWEEN ? AND ?",
            (start_date, end_date), log_action=False
        )
        pending_amount = pending_result[0][0] or 0 if pending_result else 0
        
        # Collection rate
        collection_rate = (total_payments / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'total_payments': total_payments,
            'pending_amount': pending_amount,
            'collection_rate': collection_rate
        }
        
    except Exception as e:
        st.error(f"Error getting financial summary: {e}")
        return {}

def get_financial_trend(db, start_date, end_date):
    """Get financial trend data"""
    try:
        query = '''
        SELECT 
            STRFTIME('%Y-%m', sale_date) as period,
            SUM(total_amount) as revenue,
            (SELECT SUM(amount) FROM payments 
             WHERE STRFTIME('%Y-%m', payment_date) = STRFTIME('%Y-%m', sales.sale_date)
             AND status = 'Completed') as payments
        FROM sales
        WHERE sale_date BETWEEN ? AND ?
        GROUP BY STRFTIME('%Y-%m', sale_date)
        ORDER BY period
        '''
        
        return db.get_dataframe('sales', query, params=(start_date, end_date))
        
    except Exception as e:
        st.error(f"Error getting financial trend: {e}")
        return pd.DataFrame()

def get_payment_methods_analysis(db, start_date, end_date):
    """Get payment methods analysis"""
    try:
        query = '''
        SELECT 
            payment_method,
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount
        FROM payments
        WHERE payment_date BETWEEN ? AND ? AND status = 'Completed'
        GROUP BY payment_method
        ORDER BY total_amount DESC
        '''
        
        return db.get_dataframe('payments', query, params=(start_date, end_date))
        
    except Exception as e:
        st.error(f"Error getting payment methods analysis: {e}")
        return pd.DataFrame()

def get_aging_analysis(db):
    """Get accounts receivable aging analysis"""
    try:
        query = '''
        SELECT 
            s.invoice_no,
            c.name as customer_name,
            c.village,
            s.sale_date,
            s.total_amount,
            COALESCE(SUM(p.amount), 0) as paid_amount,
            (s.total_amount - COALESCE(SUM(p.amount), 0)) as pending_amount,
            JULIANDAY('now') - JULIANDAY(s.sale_date) as days_pending,
            CASE 
                WHEN JULIANDAY('now') - JULIANDAY(s.sale_date) <= 30 THEN '0-30 days'
                WHEN JULIANDAY('now') - JULIANDAY(s.sale_date) <= 60 THEN '31-60 days'
                WHEN JULIANDAY('now') - JULIANDAY(s.sale_date) <= 90 THEN '61-90 days'
                ELSE 'Over 90 days'
            END as aging_bucket
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN payments p ON s.sale_id = p.sale_id AND p.status = 'Completed'
        WHERE s.payment_status IN ('Pending', 'Partial')
        GROUP BY s.sale_id, s.invoice_no, c.name, c.village, s.sale_date, s.total_amount
        HAVING pending_amount > 0
        ORDER BY days_pending DESC
        '''
        
        return db.get_dataframe('sales', query)
        
    except Exception as e:
        st.error(f"Error getting aging analysis: {e}")
        return pd.DataFrame()

def show_performance_reports_tab(db):
    """Show overall performance and KPI reports"""
    st.subheader("🎯 Business Performance Dashboard")
    
    try:
        # Key Performance Indicators
        st.subheader("📊 Key Performance Indicators (KPIs)")
        
        kpis = get_performance_kpis(db)
        
        if kpis:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Monthly Revenue", f"₹{kpis.get('monthly_revenue', 0):,.0f}")
            with col2:
                st.metric("Customer Growth", f"+{kpis.get('customer_growth', 0)}")
            with col3:
                st.metric("Demo Conversion", f"{kpis.get('demo_conversion_rate', 0):.1f}%")
            with col4:
                st.metric("Payment Collection", f"{kpis.get('collection_rate', 0):.1f}%")
        
        # Performance Scorecard
        st.subheader("📋 Performance Scorecard")
        scorecard = get_performance_scorecard(db)
        
        if not scorecard.empty:
            st.dataframe(scorecard, use_container_width=True)
        
        # Goal Tracking
        st.subheader("🎯 Goal vs Actual Performance")
        goals_vs_actual = get_goals_vs_actual(db)
        
        if not goals_vs_actual.empty:
            for _, goal in goals_vs_actual.iterrows():
                progress = min((goal['actual'] / goal['target']) * 100, 100) if goal['target'] > 0 else 0
                st.write(f"**{goal['metric']}**")
                st.progress(progress / 100)
                st.write(f"Target: {goal['target']} | Actual: {goal['actual']} | Progress: {progress:.1f}%")
        
        # Export Comprehensive Report
        st.subheader("📤 Export Comprehensive Report")
        
        if st.button("📄 Generate Full Business Report"):
            generate_comprehensive_report(db)
            
    except Exception as e:
        st.error(f"Error generating performance reports: {e}")

def get_performance_kpis(db):
    """Get key performance indicators"""
    try:
        # Monthly revenue (last 30 days)
        monthly_revenue_result = db.execute_query(
            "SELECT SUM(total_amount) FROM sales WHERE sale_date >= date('now', '-30 days')",
            log_action=False
        )
        monthly_revenue = monthly_revenue_result[0][0] or 0 if monthly_revenue_result else 0
        
        # Customer growth (last 30 days)
        customer_growth_result = db.execute_query(
            "SELECT COUNT(*) FROM customers WHERE created_date >= date('now', '-30 days')",
            log_action=False
        )
        customer_growth = customer_growth_result[0][0] or 0 if customer_growth_result else 0
        
        # Demo conversion rate
        demos_result = db.execute_query(
            "SELECT COUNT(*), SUM(CASE WHEN conversion_status = 'Converted' THEN 1 ELSE 0 END) FROM demos",
            log_action=False
        )
        if demos_result and demos_result[0][0] > 0:
            demo_conversion_rate = (demos_result[0][1] / demos_result[0][0]) * 100
        else:
            demo_conversion_rate = 0
        
        # Collection rate
        collection_result = db.execute_query(
            "SELECT SUM(total_amount), SUM(COALESCE((SELECT SUM(amount) FROM payments WHERE payments.sale_id = sales.sale_id AND status = 'Completed'), 0)) FROM sales",
            log_action=False
        )
        if collection_result and collection_result[0][0] and collection_result[0][0] > 0:
            collection_rate = (collection_result[0][1] / collection_result[0][0]) * 100
        else:
            collection_rate = 0
        
        return {
            'monthly_revenue': monthly_revenue,
            'customer_growth': customer_growth,
            'demo_conversion_rate': demo_conversion_rate,
            'collection_rate': collection_rate
        }
        
    except Exception as e:
        st.error(f"Error getting KPIs: {e}")
        return {}

def get_performance_scorecard(db):
    """Get performance scorecard"""
    try:
        scorecard_data = []
        
        # Sales performance
        sales_data = db.execute_query(
            "SELECT COUNT(*), SUM(total_amount), AVG(total_amount) FROM sales WHERE sale_date >= date('now', '-30 days')",
            log_action=False
        )
        if sales_data:
            scorecard_data.append({
                'Category': 'Sales',
                'Metric': 'Monthly Transactions',
                'Value': sales_data[0][0] or 0,
                'Target': 50,
                'Status': 'On Track' if (sales_data[0][0] or 0) >= 40 else 'Needs Attention'
            })
            
            scorecard_data.append({
                'Category': 'Sales',
                'Metric': 'Monthly Revenue',
                'Value': f"₹{sales_data[0][1] or 0:,.0f}",
                'Target': '₹50,000',
                'Status': 'On Track' if (sales_data[0][1] or 0) >= 40000 else 'Needs Attention'
            })
        
        # Customer performance
        customer_data = db.execute_query(
            "SELECT COUNT(*) FROM customers WHERE created_date >= date('now', '-30 days')",
            log_action=False
        )
        if customer_data:
            scorecard_data.append({
                'Category': 'Customers',
                'Metric': 'New Customers',
                'Value': customer_data[0][0] or 0,
                'Target': 20,
                'Status': 'On Track' if (customer_data[0][0] or 0) >= 15 else 'Needs Attention'
            })
        
        # Distributor performance
        distributor_data = db.execute_query(
            "SELECT COUNT(*), SUM(sabhasad_count) FROM distributors",
            log_action=False
        )
        if distributor_data:
            scorecard_data.append({
                'Category': 'Distribution',
                'Metric': 'Total Distributors',
                'Value': distributor_data[0][0] or 0,
                'Target': 10,
                'Status': 'On Track' if (distributor_data[0][0] or 0) >= 8 else 'Needs Attention'
            })
            
            scorecard_data.append({
                'Category': 'Distribution',
                'Metric': 'Total Sabhasad',
                'Value': distributor_data[0][1] or 0,
                'Target': 100,
                'Status': 'On Track' if (distributor_data[0][1] or 0) >= 80 else 'Needs Attention'
            })
        
        return pd.DataFrame(scorecard_data)
        
    except Exception as e:
        st.error(f"Error getting performance scorecard: {e}")
        return pd.DataFrame()

def get_goals_vs_actual(db):
    """Get goals vs actual performance"""
    try:
        goals = [
            {'metric': 'Monthly Revenue', 'target': 50000, 'actual': 0},
            {'metric': 'New Customers', 'target': 20, 'actual': 0},
            {'metric': 'Demos Conducted', 'target': 15, 'actual': 0},
            {'metric': 'Payment Collection', 'target': 95, 'actual': 0}
        ]
        
        # Get actual values
        revenue_result = db.execute_query(
            "SELECT SUM(total_amount) FROM sales WHERE sale_date >= date('now', '-30 days')",
            log_action=False
        )
        if revenue_result:
            goals[0]['actual'] = revenue_result[0][0] or 0
        
        customer_result = db.execute_query(
            "SELECT COUNT(*) FROM customers WHERE created_date >= date('now', '-30 days')",
            log_action=False
        )
        if customer_result:
            goals[1]['actual'] = customer_result[0][0] or 0
        
        demo_result = db.execute_query(
            "SELECT COUNT(*) FROM demos WHERE demo_date >= date('now', '-30 days')",
            log_action=False
        )
        if demo_result:
            goals[2]['actual'] = demo_result[0][0] or 0
        
        collection_result = db.execute_query(
            "SELECT SUM(total_amount), SUM(COALESCE((SELECT SUM(amount) FROM payments WHERE payments.sale_id = sales.sale_id AND status = 'Completed'), 0)) FROM sales WHERE sale_date >= date('now', '-30 days')",
            log_action=False
        )
        if collection_result and collection_result[0][0] and collection_result[0][0] > 0:
            goals[3]['actual'] = (collection_result[0][1] / collection_result[0][0]) * 100
        
        return pd.DataFrame(goals)
        
    except Exception as e:
        st.error(f"Error getting goals vs actual: {e}")
        return pd.DataFrame()

def export_sales_data(db, start_date, end_date):
    """Export sales data to CSV"""
    try:
        sales_data = db.get_dataframe('sales', '''
        SELECT s.*, c.name as customer_name, c.village, c.taluka
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        WHERE s.sale_date BETWEEN ? AND ?
        ORDER BY s.sale_date DESC
        ''', params=(start_date, end_date))
        
        if not sales_data.empty:
            csv = sales_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Sales Data as CSV",
                data=csv,
                file_name=f"sales_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error exporting sales data: {e}")

def generate_sales_pdf_report(db, start_date, end_date):
    """Generate PDF sales report (placeholder)"""
    st.info("📄 PDF report generation feature will be implemented soon!")
    st.info("This would generate a comprehensive PDF report with charts and analysis.")

def generate_comprehensive_report(db):
    """Generate comprehensive business report"""
    st.success("🎉 Comprehensive business report generated!")
    st.info("""
    **Report Includes:**
    - Executive Summary
    - Sales Performance Analysis
    - Customer Insights
    - Distributor Network Performance
    - Financial Overview
    - Key Recommendations
    
    *Note: Full report generation with export features will be implemented in the next version.*
    """)

# Add this to your main file routing