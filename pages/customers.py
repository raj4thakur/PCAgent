# pages/customers.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def show_customers_page(db, whatsapp_manager=None):
    """Show customer analytics, segmentation, and action planning page"""
    st.title("👥 Customer Intelligence Center")
    
    if not db:
        st.error("Database not available. Please check initialization.")
        return
    
    # Tabs for different customer functions
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🎯 Segmentation", "📞 Action Center", "🔍 Customer Directory"])
    
    with tab1:
        show_customer_dashboard_tab(db)
    
    with tab2:
        show_customer_segmentation_tab(db)
    
    with tab3:
        show_action_center_tab(db, whatsapp_manager)
    
    with tab4:
        show_customer_directory_tab(db)

def show_customer_dashboard_tab(db):
    """Show customer analytics dashboard"""
    st.subheader("📊 Customer Analytics Dashboard")
    
    try:
        # Get comprehensive customer data
        customers_data = get_customer_analytics_data(db)
        
        if customers_data.empty:
            st.info("No customer data available yet.")
            return
        
        # Key Metrics
        st.subheader("🎯 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_customers = len(customers_data)
            st.metric("Total Customers", total_customers)
        
        with col2:
            active_customers = len(customers_data[customers_data['total_purchases'] > 0])
            st.metric("Active Customers", active_customers)
        
        with col3:
            avg_purchase_value = customers_data[customers_data['total_spent'] > 0]['total_spent'].mean()
            st.metric("Avg Purchase Value", f"₹{avg_purchase_value:,.0f}" if not pd.isna(avg_purchase_value) else "₹0")
        
        with col4:
            repeat_customers = len(customers_data[customers_data['total_purchases'] > 1])
            st.metric("Repeat Customers", repeat_customers)
        
        # Village-wise Analysis
        st.subheader("🗺️ Geographic Distribution")
        col1, col2 = st.columns(2)
        
        with col1:
            village_stats = customers_data.groupby('village').agg({
                'customer_id': 'count',
                'total_spent': 'sum',
                'total_purchases': 'sum'
            }).reset_index()
            village_stats.columns = ['Village', 'Customers', 'Total Revenue', 'Total Purchases']
            village_stats = village_stats.sort_values('Customers', ascending=False)
            
            if not village_stats.empty:
                fig = px.bar(village_stats.head(10), x='Village', y='Customers',
                           title='Top 10 Villages by Customer Count',
                           color='Customers')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not village_stats.empty:
                fig = px.pie(village_stats.head(8), values='Customers', names='Village',
                           title='Customer Distribution by Village')
                st.plotly_chart(fig, use_container_width=True)
        
        # Purchase Behavior
        st.subheader("💰 Purchase Behavior Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            # Customer lifetime value distribution
            spending_brackets = customers_data[customers_data['total_spent'] > 0]['total_spent']
            if not spending_brackets.empty:
                fig = px.histogram(spending_brackets, nbins=10,
                                 title='Customer Spending Distribution',
                                 labels={'value': 'Total Spent (₹)', 'count': 'Number of Customers'})
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Recency analysis
            if 'last_purchase_date' in customers_data.columns:
                recent_customers = customers_data[customers_data['last_purchase_date'].notna()]
                if not recent_customers.empty:
                    recent_customers['days_since_purchase'] = (datetime.now() - pd.to_datetime(recent_customers['last_purchase_date'])).dt.days
                    fig = px.histogram(recent_customers, x='days_since_purchase', nbins=10,
                                     title='Days Since Last Purchase',
                                     labels={'days_since_purchase': 'Days', 'count': 'Customers'})
                    st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading customer analytics: {e}")

def show_customer_segmentation_tab(db):
    """Show customer segmentation and targeting"""
    st.subheader("🎯 Customer Segmentation")
    
    try:
        customers_data = get_customer_analytics_data(db)
        
        if customers_data.empty:
            st.info("No customer data available for segmentation.")
            return
        
        # Segmentation criteria
        st.subheader("🔍 Define Segments")
        
        col1, col2 = st.columns(2)
        
        with col1:
            segment_by = st.selectbox("Segment By", 
                                    ["Purchase Behavior", "Geographic", "Demographic", "Custom"])
            
            if segment_by == "Purchase Behavior":
                min_purchases = st.slider("Minimum Purchases", 0, 20, 1)
                min_spent = st.number_input("Minimum Amount Spent (₹)", 0, 100000, 1000)
                
                segment_customers = customers_data[
                    (customers_data['total_purchases'] >= min_purchases) &
                    (customers_data['total_spent'] >= min_spent)
                ]
            
            elif segment_by == "Geographic":
                selected_villages = st.multiselect("Select Villages", 
                                                 customers_data['village'].unique())
                if selected_villages:
                    segment_customers = customers_data[customers_data['village'].isin(selected_villages)]
                else:
                    segment_customers = customers_data
            
            elif segment_by == "Demographic":
                # Add demographic filters here
                segment_customers = customers_data
        
        with col2:
            st.write("**Segment Actions**")
            segment_size = len(segment_customers)
            st.metric("Segment Size", segment_size)
            
            if segment_size > 0:
                avg_segment_value = segment_customers['total_spent'].mean()
                st.metric("Avg Customer Value", f"₹{avg_segment_value:,.0f}")
                
                # Quick actions for segment
                if st.button("📱 Send Bulk WhatsApp", key="segment_whatsapp"):
                    st.info(f"Ready to send message to {segment_size} customers")
                
                if st.button("📍 Plan Field Visit", key="segment_visit"):
                    villages = segment_customers['village'].value_counts().head(5)
                    st.success(f"Top villages to visit: {', '.join(villages.index.tolist())}")
        
        # Show segment details
        if not segment_customers.empty:
            st.subheader("👥 Segment Details")
            
            # Segment characteristics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                top_village = segment_customers['village'].mode()[0] if not segment_customers['village'].mode().empty else "N/A"
                st.metric("Most Common Village", top_village)
            
            with col2:
                avg_purchases = segment_customers['total_purchases'].mean()
                st.metric("Avg Purchases/Customer", f"{avg_purchases:.1f}")
            
            with col3:
                total_potential = segment_customers['total_spent'].sum()
                st.metric("Segment Total Value", f"₹{total_potential:,.0f}")
            
            # Customer list in segment
            st.dataframe(segment_customers[['name', 'village', 'mobile', 'total_purchases', 'total_spent']].head(20), 
                        use_container_width=True)
    
    except Exception as e:
        st.error(f"Error in customer segmentation: {e}")

def show_action_center_tab(db, whatsapp_manager):
    """Show action planning and communication center"""
    st.subheader("📞 Customer Action Center")
    
    try:
        customers_data = get_customer_analytics_data(db)
        
        if customers_data.empty:
            st.info("No customer data available for actions.")
            return
        
        # Action categories
        action_type = st.selectbox("Action Type", 
                                 ["Follow-up Calls", "Demo Follow-ups", "Payment Reminders", 
                                  "New Product Announcements", "Customer Feedback"])
        
        if action_type == "Follow-up Calls":
            show_followup_calls_section(db, customers_data)
        
        elif action_type == "Demo Follow-ups":
            show_demo_followups_section(db, customers_data)
        
        elif action_type == "Payment Reminders":
            show_payment_reminders_section(db, customers_data, whatsapp_manager)
        
        elif action_type == "New Product Announcements":
            show_product_announcements_section(db, customers_data, whatsapp_manager)
        
        elif action_type == "Customer Feedback":
            show_feedback_section(db, customers_data, whatsapp_manager)
    
    except Exception as e:
        st.error(f"Error in action center: {e}")

def show_followup_calls_section(db, customers_data):
    """Show customers needing follow-up calls"""
    st.write("### 📞 Customers Needing Follow-up")
    
    # Identify customers for follow-up
    follow_up_criteria = st.multiselect("Follow-up Criteria",
                                      ["No Purchase in 30 days", "High Value Customers", 
                                       "Single Purchase Only", "Specific Villages"])
    
    target_customers = customers_data.copy()
    
    if "No Purchase in 30 days" in follow_up_criteria:
        # This would require last_purchase_date in your data
        st.info("Last purchase date tracking needed for this feature")
    
    if "High Value Customers" in follow_up_criteria:
        high_value_threshold = st.number_input("High Value Threshold (₹)", 1000, 10000, 5000)
        target_customers = target_customers[target_customers['total_spent'] >= high_value_threshold]
    
    if "Single Purchase Only" in follow_up_criteria:
        target_customers = target_customers[target_customers['total_purchases'] == 1]
    
    if not target_customers.empty:
        st.write(f"**{len(target_customers)} customers identified for follow-up**")
        
        # Village concentration
        village_concentration = target_customers['village'].value_counts().head(5)
        st.write("**Top villages for field visits:**")
        for village, count in village_concentration.items():
            st.write(f"- {village}: {count} customers")
        
        # Display customer list
        st.dataframe(target_customers[['name', 'village', 'mobile', 'total_purchases', 'total_spent']], 
                    use_container_width=True)

def show_demo_followups_section(db, customers_data):
    """Show demo conversion tracking"""
    st.write("### 🎯 Demo Conversion Tracking")
    
    try:
        # Get demo data
        demo_data = db.get_dataframe('demos', '''
        SELECT d.*, c.name as customer_name, c.village, c.mobile, p.product_name
        FROM demos d
        LEFT JOIN customers c ON d.customer_id = c.customer_id
        LEFT JOIN products p ON d.product_id = p.product_id
        ORDER BY d.demo_date DESC
        ''')
        
        if not demo_data.empty:
            # Demo conversion stats
            total_demos = len(demo_data)
            converted_demos = len(demo_data[demo_data['conversion_status'] == 'Converted'])
            conversion_rate = (converted_demos / total_demos) * 100 if total_demos > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Demos", total_demos)
            with col2:
                st.metric("Converted", converted_demos)
            with col3:
                st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
            
            # Pending follow-ups
            pending_followups = demo_data[
                (demo_data['conversion_status'] == 'Not Converted') &
                (pd.to_datetime(demo_data['follow_up_date']) <= datetime.now())
            ]
            
            if not pending_followups.empty:
                st.warning(f"🚨 {len(pending_followups)} demos need immediate follow-up!")
                st.dataframe(pending_followups[['customer_name', 'village', 'product_name', 'demo_date', 'follow_up_date']],
                           use_container_width=True)
            
            # All demo records
            st.write("**All Demo Records**")
            st.dataframe(demo_data[['customer_name', 'village', 'product_name', 'demo_date', 'conversion_status']],
                       use_container_width=True)
        else:
            st.info("No demo records found.")
    
    except Exception as e:
        st.error(f"Error loading demo data: {e}")

def show_payment_reminders_section(db, customers_data, whatsapp_manager):
    """Show payment reminder system"""
    st.write("### 💰 Payment Reminders")
    
    try:
        # Get pending payments
        pending_payments = db.get_pending_payments()
        
        if not pending_payments.empty:
            total_pending = pending_payments['pending_amount'].sum()
            st.metric("Total Pending Amount", f"₹{total_pending:,.2f}")
            
            # Group by customer
            customer_pending = pending_payments.groupby('customer_name').agg({
                'pending_amount': 'sum',
                'invoice_no': 'count'
            }).reset_index()
            customer_pending.columns = ['Customer', 'Total Pending', 'Pending Invoices']
            customer_pending = customer_pending.sort_values('Total Pending', ascending=False)
            
            st.dataframe(customer_pending, use_container_width=True)
            
            # Bulk WhatsApp reminders
            st.write("**Bulk Payment Reminders**")
            if st.button("📱 Send Payment Reminders to All", type="primary") and whatsapp_manager:
                st.info("This would send payment reminders to all customers with pending payments")
        else:
            st.success("🎉 All payments are cleared! No pending payments.")
    
    except Exception as e:
        st.error(f"Error loading payment data: {e}")

def show_product_announcements_section(db, customers_data, whatsapp_manager):
    """Show new product announcement system"""
    st.write("### 🆕 New Product Announcements")
    
    # Target segments for new products
    segment = st.selectbox("Target Segment", 
                         ["All Customers", "High Value Customers", "Specific Village", "Previous Product Buyers"])
    
    message_template = st.text_area("Announcement Message", 
                                  height=100,
                                  value="Hello {name}! We have exciting new products available. Reply YES for details!")
    
    if st.button("📢 Send Announcement", type="primary") and whatsapp_manager:
        st.success("Ready to send announcement to selected segment!")

def show_feedback_section(db, customers_data, whatsapp_manager):
    """Show customer feedback collection system"""
    st.write("### 💬 Customer Feedback Collection")
    
    feedback_segment = st.selectbox("Request Feedback From",
                                  ["Recent Customers", "High Value Customers", "Inactive Customers"])
    
    feedback_message = st.text_area("Feedback Request Message",
                                  height=100,
                                  value="Hello {name}! We value your feedback. How was your experience with us?")
    
    if st.button("📝 Request Feedback", type="primary") and whatsapp_manager:
        st.info("Feedback requests ready to send!")

def show_customer_directory_tab(db):
    """Show comprehensive customer directory"""
    st.subheader("🔍 Customer Directory")
    
    try:
        customers_data = get_customer_analytics_data(db)
        
        if customers_data.empty:
            st.info("No customers found in the database.")
            return
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            village_filter = st.multiselect("Filter by Village", customers_data['village'].unique())
        
        with col2:
            purchase_filter = st.selectbox("Filter by Purchase History", 
                                         ["All", "Has Purchases", "No Purchases", "Multiple Purchases"])
        
        with col3:
            search_term = st.text_input("Search by Name/Mobile")
        
        # Apply filters
        filtered_customers = customers_data.copy()
        
        if village_filter:
            filtered_customers = filtered_customers[filtered_customers['village'].isin(village_filter)]
        
        if purchase_filter == "Has Purchases":
            filtered_customers = filtered_customers[filtered_customers['total_purchases'] > 0]
        elif purchase_filter == "No Purchases":
            filtered_customers = filtered_customers[filtered_customers['total_purchases'] == 0]
        elif purchase_filter == "Multiple Purchases":
            filtered_customers = filtered_customers[filtered_customers['total_purchases'] > 1]
        
        if search_term:
            filtered_customers = filtered_customers[
                filtered_customers['name'].str.contains(search_term, case=False, na=False) |
                filtered_customers['mobile'].str.contains(search_term, na=False)
            ]
        
        # Display results
        st.write(f"**Found {len(filtered_customers)} customers**")
        
        display_columns = ['name', 'village', 'mobile', 'total_purchases', 'total_spent']
        display_df = filtered_customers[display_columns]
        display_df.columns = ['Name', 'Village', 'Mobile', 'Total Purchases', 'Total Spent (₹)']
        display_df['Total Spent (₹)'] = display_df['Total Spent (₹)'].apply(lambda x: f"₹{x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading customer directory: {e}")

def get_customer_analytics_data(db):
    """Get comprehensive customer data with analytics"""
    try:
        customers = db.get_dataframe('customers', '''
        SELECT c.*, 
               COUNT(s.sale_id) as total_purchases,
               COALESCE(SUM(s.total_amount), 0) as total_spent,
               MAX(s.sale_date) as last_purchase_date
        FROM customers c
        LEFT JOIN sales s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id
        ORDER BY total_spent DESC
        ''')
        return customers
    except Exception as e:
        st.error(f"Error loading customer analytics data: {e}")
        return pd.DataFrame()