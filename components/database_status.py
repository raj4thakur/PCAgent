# components/database_status.py
import streamlit as st

def show_database_status(db):
    """Show current database status"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Database Status")
    
    try:
        if db:
            customers_count = len(db.get_dataframe('customers'))
            sales_count = len(db.get_dataframe('sales'))
            distributors_count = len(db.get_dataframe('distributors'))
            payments_count = len(db.get_dataframe('payments'))
            products_count = len(db.get_dataframe('products'))
            
            st.sidebar.metric("👥 Customers", customers_count)
            st.sidebar.metric("💰 Sales", sales_count)
            st.sidebar.metric("🤝 Distributors", distributors_count)
            st.sidebar.metric("💳 Payments", payments_count)
            st.sidebar.metric("📦 Products", products_count)
        else:
            st.sidebar.error("Database not available")
            
    except Exception as e:
        st.sidebar.error("Database connection issue")