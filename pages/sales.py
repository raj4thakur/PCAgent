# pages/sales.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re

def show_sales_page(db, whatsapp_manager=None):
    """Show enhanced sales management page with quick customer creation and WhatsApp"""
    st.title("💰 Sales Management")
    
    if not db:
        st.error("Database not available. Please check initialization.")
        return
    
    # Tabs for different sales functions
    tab1, tab2, tab3 = st.tabs(["➕ Quick Sale", "📋 Sales History", "🔍 Sales Analytics"])
    
    with tab1:
        show_quick_sale_tab(db, whatsapp_manager)
    
    with tab2:
        show_sales_history_tab(db)
    
    with tab3:
        show_sales_analytics_tab(db)

def show_quick_sale_tab(db, whatsapp_manager):
    """Show tab for quick sales with instant customer creation"""
    st.subheader("🚀 Quick Sale - Create Customer & Sale in One Go")
    
    with st.form("quick_sale_form"):
        # Customer Section - Quick Create
        st.markdown("### 👥 Customer Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Option 1: Select existing customer
            st.write("**Select Existing Customer**")
            customers = db.get_dataframe('customers')
            existing_customer_options = {f"{row['name']} ({row['mobile']})": row['customer_id'] 
                                       for _, row in customers.iterrows()} if not customers.empty else {}
            
            use_existing = st.selectbox("Choose Customer", 
                                      options=[""] + list(existing_customer_options.keys()),
                                      key="existing_customer")
            
            if use_existing:
                customer_id = existing_customer_options[use_existing]
                # Get customer details for display
                customer_details = customers[customers['customer_id'] == customer_id].iloc[0]
                st.success(f"Selected: {customer_details['name']} - {customer_details['mobile']}")
            else:
                customer_id = None
        
        with col2:
            # Option 2: Create new customer instantly
            st.write("**Or Create New Customer**")
            new_customer_name = st.text_input("Customer Name*", placeholder="Enter customer name")
            new_customer_mobile = st.text_input("Mobile Number", placeholder="Enter mobile number")
            new_customer_village = st.text_input("Village", placeholder="Enter village")
            
            if new_customer_name:
                # Check if customer already exists
                existing_customer = db.execute_query(
                    "SELECT customer_id FROM customers WHERE name = ? OR mobile = ?",
                    (new_customer_name, new_customer_mobile),
                    log_action=False
                )
                
                if existing_customer:
                    st.warning("⚠️ Customer with same name/mobile already exists!")
                    customer_id = existing_customer[0][0]
                else:
                    customer_id = None  # Will create during sale submission
        
        # Sale Information
        st.markdown("### 📄 Sale Information")
        col1, col2 = st.columns(2)
        
        with col1:
            invoice_no = st.text_input("Invoice Number*", value=db.generate_invoice_number())
        with col2:
            sale_date = st.date_input("Sale Date", datetime.now())
        
        # Products Section with Smart Pricing
        st.markdown("### 📦 Add Products")
        
        products = db.get_dataframe('products')
        if products.empty:
            st.error("❌ No products found in database. Please add products first.")
            return
        
        product_options = {row['product_name']: {
            'product_id': row['product_id'],
            'standard_rate': row['standard_rate'],
            'packing_type': row['packing_type'],
            'capacity_ltr': row['capacity_ltr']
        } for _, row in products.iterrows()}
        
        sale_items = []
        total_amount = 0
        
        # Create 3 product rows
        for i in range(3):
            st.markdown(f"**Product {i+1}**")
            col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
            
            with col1:
                selected_product = st.selectbox(f"Select Product", 
                                              options=[""] + list(product_options.keys()),
                                              key=f"product_{i}")
            
            with col2:
                quantity = st.number_input(f"Qty", min_value=0, value=0, key=f"qty_{i}")
            
            with col3:
                if selected_product:
                    default_rate = product_options[selected_product]['standard_rate']
                    rate = st.number_input(f"Rate (₹)", min_value=0.0, value=float(default_rate), 
                                         step=1.0, key=f"rate_{i}")
                    # Show discount indicator if rate is changed
                    if rate < default_rate:
                        discount = ((default_rate - rate) / default_rate) * 100
                        st.info(f"🎯 {discount:.1f}% off")
                else:
                    rate = st.number_input(f"Rate (₹)", min_value=0.0, value=0.0, key=f"rate_{i}")
            
            with col4:
                if selected_product and quantity > 0:
                    amount = quantity * rate
                    st.metric("Amount", f"₹{amount:,.2f}")
                else:
                    amount = 0
                    st.metric("Amount", "₹0")
            
            with col5:
                if selected_product and quantity > 0:
                    product_info = product_options[selected_product]
                    st.write(f"*{product_info['packing_type']}*")
                    if product_info['capacity_ltr'] > 0:
                        st.write(f"{product_info['capacity_ltr']}L")
            
            if selected_product and quantity > 0:
                sale_items.append({
                    'product_id': product_options[selected_product]['product_id'],
                    'product_name': selected_product,
                    'quantity': quantity,
                    'rate': rate,
                    'amount': amount,
                    'standard_rate': product_options[selected_product]['standard_rate']
                })
                total_amount += amount
        
        # Show running total
        if total_amount > 0:
            st.success(f"### 🎯 Running Total: ₹{total_amount:,.2f}")
        
        # Additional Options
        st.markdown("### ⚙️ Additional Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            notes = st.text_area("Sale Notes", placeholder="Any special notes about this sale...")
        
        with col2:
            # WhatsApp Notification Options
            st.write("**📱 Customer Notification**")
            send_whatsapp = st.checkbox("Send WhatsApp Notification", value=True)
            if send_whatsapp and not whatsapp_manager:
                st.warning("WhatsApp manager not available")
            
            # Payment options
            payment_received = st.checkbox("Payment Received", value=False)
            if payment_received:
                payment_amount = st.number_input("Payment Amount", min_value=0.0, value=float(total_amount))
                payment_method = st.selectbox("Payment Method", ["Cash", "G-Pay", "Cheque", "Bank Transfer"])
        
        # Submit Section
        st.markdown("---")
        submitted = st.form_submit_button("🚀 Create Sale & Notify Customer", type="primary")
        
        if submitted:
            # Validation
            errors = []
            
            if not customer_id and not new_customer_name:
                errors.append("Please select a customer or enter new customer name")
            if not invoice_no:
                errors.append("Invoice number is required")
            if not sale_items:
                errors.append("Please add at least one product")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    # Create customer if new
                    if not customer_id and new_customer_name:
                        customer_id = db.add_customer(
                            name=new_customer_name,
                            mobile=new_customer_mobile,
                            village=new_customer_village
                        )
                        if customer_id and customer_id > 0:
                            st.success(f"✅ New customer created: {new_customer_name}")
                    
                    if customer_id:
                        # Create sale
                        sale_id = db.add_sale(
                            invoice_no=invoice_no,
                            customer_id=customer_id,
                            sale_date=sale_date,
                            items=sale_items,
                            notes=notes
                        )
                        
                        if sale_id and sale_id > 0:
                            st.success(f"✅ Sale created successfully! Sale ID: {sale_id}")
                            
                            # Add payment if received
                            if payment_received:
                                db.execute_query('''
                                INSERT INTO payments (sale_id, payment_date, payment_method, amount)
                                VALUES (?, ?, ?, ?)
                                ''', (sale_id, sale_date, payment_method, payment_amount))
                                st.success(f"✅ Payment recorded: ₹{payment_amount:,.2f}")
                            
                            # Send WhatsApp notification
                            if send_whatsapp and whatsapp_manager:
                                send_sale_notification(whatsapp_manager, db, sale_id, customer_id)
                            
                            # Show sale summary
                            show_quick_sale_summary(db, sale_id, sale_items, customer_id)
                            
                            # Clear form for next sale
                            if st.button("🔄 Create Another Sale"):
                                st.rerun()
                        else:
                            st.error("❌ Failed to create sale.")
                    
                except Exception as e:
                    st.error(f"Error creating sale: {e}")

def send_sale_notification(whatsapp_manager, db, sale_id, customer_id):
    """Send WhatsApp notification to customer about their sale"""
    try:
        # Get sale and customer details
        sale_details = db.get_dataframe('sales', f"SELECT * FROM sales WHERE sale_id = {sale_id}")
        customer_details = db.get_dataframe('customers', f"SELECT * FROM customers WHERE customer_id = {customer_id}")
        
        if sale_details.empty or customer_details.empty:
            return False
        
        sale = sale_details.iloc[0]
        customer = customer_details.iloc[0]
        
        # Get sale items
        items_details = db.get_dataframe('sale_items', f'''
        SELECT si.*, p.product_name 
        FROM sale_items si 
        JOIN products p ON si.product_id = p.product_id 
        WHERE si.sale_id = {sale_id}
        ''')
        
        if customer.get('mobile'):
            # Create notification message
            message = f"""Hello {customer['name']}! 🎉

Thank you for your purchase! 

📄 Invoice: {sale['invoice_no']}
📅 Date: {sale['sale_date']}
💰 Total Amount: ₹{sale['total_amount']:,.2f}

📦 Items Purchased:
"""
            
            # Add items to message
            for _, item in items_details.iterrows():
                message += f"• {item['product_name']}: {item['quantity']} x ₹{item['rate']} = ₹{item['amount']}\n"
            
            message += f"""

Payment Status: {sale['payment_status']}

We appreciate your business! 🙏

For any queries, contact us.

Thank you!"""
            
            # Send message
            success = whatsapp_manager.send_message(customer['mobile'], message)
            if success:
                st.success("📱 WhatsApp notification sent to customer!")
            else:
                st.warning("⚠️ Failed to send WhatsApp notification")
            
            return success
    
    except Exception as e:
        st.warning(f"Could not send notification: {e}")
        return False

def show_quick_sale_summary(db, sale_id, sale_items, customer_id):
    """Show comprehensive sale summary"""
    st.markdown("## 🎉 Sale Completed Successfully!")
    
    try:
        # Get sale and customer details
        sale_details = db.get_dataframe('sales', f"SELECT * FROM sales WHERE sale_id = {sale_id}")
        customer_details = db.get_dataframe('customers', f"SELECT * FROM customers WHERE customer_id = {customer_id}")
        
        if sale_details.empty or customer_details.empty:
            return
        
        sale = sale_details.iloc[0]
        customer = customer_details.iloc[0]
        
        # Display in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Customer Details")
            st.write(f"**Name:** {customer['name']}")
            if customer['mobile']:
                st.write(f"**Mobile:** {customer['mobile']}")
            if customer['village']:
                st.write(f"**Village:** {customer['village']}")
            
            st.subheader("Sale Details")
            st.write(f"**Invoice No:** {sale['invoice_no']}")
            st.write(f"**Sale Date:** {sale['sale_date']}")
            st.write(f"**Payment Status:** {sale['payment_status']}")
            if sale['notes']:
                st.write(f"**Notes:** {sale['notes']}")
        
        with col2:
            st.subheader("Financial Summary")
            st.metric("Total Amount", f"₹{sale['total_amount']:,.2f}")
            
            # Get payment details
            payment_details = db.get_dataframe('payments', f"SELECT * FROM payments WHERE sale_id = {sale_id}")
            if not payment_details.empty:
                total_paid = payment_details['amount'].sum()
                pending = sale['total_amount'] - total_paid
                st.metric("Amount Paid", f"₹{total_paid:,.2f}")
                st.metric("Pending Amount", f"₹{pending:,.2f}")
            
            st.subheader("Items Summary")
            for item in sale_items:
                st.write(f"• {item['product_name']}: {item['quantity']} x ₹{item['rate']}")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 View All Sales"):
                # This would switch to sales history tab in a real implementation
                st.info("Navigate to Sales History tab")
        
        with col2:
            if st.button("👥 View Customer"):
                st.info(f"Customer: {customer['name']}")
        
        with col3:
            if st.button("💳 Record Payment"):
                st.info("Use Payments page to record additional payments")
    
    except Exception as e:
        st.error(f"Error displaying sale summary: {e}")

def show_sales_history_tab(db):
    """Show tab for sales history and management"""
    st.subheader("Sales History & Management")
    
    try:
        # Quick filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            date_filter = st.selectbox("Date Filter", 
                                     ["All", "Today", "Last 7 days", "This month", "Custom"])
        
        with col2:
            status_filter = st.multiselect("Payment Status", 
                                         ["Pending", "Partial", "Paid"], 
                                         default=["Pending", "Partial", "Paid"])
        
        with col3:
            search_term = st.text_input("Search Invoice/Customer")
        
        with col4:
            show_rows = st.selectbox("Show", [10, 25, 50, 100], index=0)
        
        # Build query
        query = '''
        SELECT s.*, c.name as customer_name, c.village, c.mobile,
               COALESCE(SUM(p.amount), 0) as paid_amount,
               (s.total_amount - COALESCE(SUM(p.amount), 0)) as pending_amount
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN payments p ON s.sale_id = p.sale_id
        '''
        
        conditions = []
        if status_filter:
            status_cond = " OR ".join([f"s.payment_status = '{status}'" for status in status_filter])
            conditions.append(f"({status_cond})")
        
        if search_term:
            conditions.append(f"(s.invoice_no LIKE '%{search_term}%' OR c.name LIKE '%{search_term}%')")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " GROUP BY s.sale_id ORDER BY s.sale_date DESC LIMIT " + str(show_rows)
        
        # Get sales data
        sales_data = db.get_dataframe('sales', query)
        
        if not sales_data.empty:
            st.write(f"**Showing {len(sales_data)} sales**")
            
            # Enhanced display
            display_df = sales_data[['invoice_no', 'sale_date', 'customer_name', 'village', 
                                   'total_amount', 'paid_amount', 'pending_amount', 'payment_status']].copy()
            
            # Formatting
            display_df['total_amount'] = display_df['total_amount'].apply(lambda x: f"₹{x:,.2f}")
            display_df['paid_amount'] = display_df['paid_amount'].apply(lambda x: f"₹{x:,.2f}")
            display_df['pending_amount'] = display_df['pending_amount'].apply(lambda x: f"₹{x:,.2f}")
            
            display_df.columns = ['Invoice', 'Date', 'Customer', 'Village', 'Total', 'Paid', 'Pending', 'Status']
            
            st.dataframe(display_df, use_container_width=True)
            
            # Summary metrics
            total_sales = sales_data['total_amount'].sum()
            total_pending = sales_data['pending_amount'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sales Value", f"₹{total_sales:,.2f}")
            with col2:
                st.metric("Total Pending", f"₹{total_pending:,.2f}")
            with col3:
                if total_sales > 0:
                    collection_rate = ((total_sales - total_pending) / total_sales) * 100
                    st.metric("Collection Rate", f"{collection_rate:.1f}%")
        
        else:
            st.info("No sales found matching the current filters.")
    
    except Exception as e:
        st.error(f"Error loading sales history: {e}")

def show_sales_analytics_tab(db):
    """Show tab for sales analytics"""
    st.subheader("Sales Analytics & Insights")
    
    try:
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        if start_date > end_date:
            st.error("Start date cannot be after end date")
            return
        
        # Get analytics
        analytics = db.get_sales_analytics(start_date.strftime('%Y-%m-%d'), 
                                         end_date.strftime('%Y-%m-%d'))
        
        if analytics:
            # Key metrics
            st.subheader("📈 Performance Metrics")
            cols = st.columns(4)
            metrics = [
                ("Total Sales", analytics.get('total_sales', 0), "💰"),
                ("Total Revenue", f"₹{analytics.get('total_revenue', 0):,.2f}", "💵"),
                ("Avg Sale", f"₹{analytics.get('avg_sale_value', 0):,.2f}", "📊"),
                ("Unique Customers", analytics.get('unique_customers', 0), "👥")
            ]
            
            for col, (label, value, icon) in zip(cols, metrics):
                with col:
                    st.metric(label, value)
        
        # Additional analytics can be added here
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")