# pages/payments.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def show_payments_page(db, whatsapp_manager=None):
    """Show payments management and tracking page"""
    st.title("💳 Payments Management")
    
    if not db:
        st.error("Database not available. Please check initialization.")
        return
    
    # Tabs for different payment functions
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Record Payment", "📋 Payment History", "⏳ Pending Payments", "📊 Payment Analytics"])
    
    with tab1:
        show_record_payment_tab(db, whatsapp_manager)
    
    with tab2:
        show_payment_history_tab(db)
    
    with tab3:
        show_pending_payments_tab(db, whatsapp_manager)
    
    with tab4:
        show_payment_analytics_tab(db)

def show_record_payment_tab(db, whatsapp_manager):
    """Show form to record new payments"""
    st.subheader("💰 Record New Payment")
    
    with st.form("record_payment_form"):
        st.markdown("### 📄 Payment Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get pending sales for selection
            pending_sales = get_pending_sales(db)
            if not pending_sales.empty:
                sale_options = {f"{row['invoice_no']} - {row['customer_name']} (₹{row['pending_amount']:,.2f})": row['sale_id'] 
                              for _, row in pending_sales.iterrows()}
                selected_sale = st.selectbox("Select Sale*", options=list(sale_options.keys()))
                sale_id = sale_options[selected_sale] if selected_sale else None
                
                # Show sale details
                if sale_id:
                    sale_details = pending_sales[pending_sales['sale_id'] == sale_id].iloc[0]
                    st.info(f"**Sale Details:** {sale_details['customer_name']} - Pending: ₹{sale_details['pending_amount']:,.2f}")
            else:
                st.warning("No pending sales found. All sales are fully paid!")
                sale_id = None
        
        with col2:
            payment_date = st.date_input("Payment Date*", datetime.now())
            payment_method = st.selectbox("Payment Method*", 
                                        ["Cash", "G-Pay", "PhonePe", "Bank Transfer", "Cheque", "Other"])
            payment_status = st.selectbox("Payment Status", ["Completed", "Pending", "Failed"])
        
        st.markdown("### 💵 Payment Amount")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if sale_id:
                sale_data = pending_sales[pending_sales['sale_id'] == sale_id].iloc[0]
                max_amount = sale_data['pending_amount']
                payment_amount = st.number_input("Payment Amount*", min_value=0.0, max_value=float(max_amount), 
                                               value=float(max_amount), step=100.0)
                st.write(f"Pending Amount: ₹{max_amount:,.2f}")
            else:
                payment_amount = st.number_input("Payment Amount*", min_value=0.0, value=0.0, step=100.0)
        
        with col2:
            reference_number = st.text_input("Reference Number", 
                                           placeholder="UPI ID, Cheque No, Transaction ID, etc.")
            rrn_number = st.text_input("RRN Number", placeholder="For bank transfers")
        
        notes = st.text_area("Payment Notes", placeholder="Any additional notes about this payment...")
        
        # Submit button
        submitted = st.form_submit_button("💳 Record Payment", type="primary")
        
        if submitted:
            # Validation
            errors = []
            if not sale_id:
                errors.append("Sale selection is required")
            if not payment_amount or payment_amount <= 0:
                errors.append("Valid payment amount is required")
            if not payment_date:
                errors.append("Payment date is required")
            if not payment_method:
                errors.append("Payment method is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                try:
                    # Record payment in database
                    payment_id = add_payment_to_database(db, {
                        'sale_id': sale_id,
                        'payment_date': payment_date,
                        'payment_method': payment_method,
                        'amount': payment_amount,
                        'rrn': rrn_number,
                        'reference': reference_number,
                        'status': payment_status,
                        'notes': notes
                    })
                    
                    if payment_id and payment_id > 0:
                        st.success(f"✅ Payment recorded successfully! Payment ID: {payment_id}")
                        
                        # Update sale payment status
                        update_sale_payment_status(db, sale_id)
                        
                        # Send notification if WhatsApp available
                        if whatsapp_manager and sale_id:
                            send_payment_notification(whatsapp_manager, db, sale_id, payment_amount)
                        
                        # Show payment summary
                        show_payment_summary(db, payment_id)
                    
                    else:
                        st.error("❌ Failed to record payment. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Error recording payment: {e}")

def get_pending_sales(db):
    """Get sales with pending payments"""
    try:
        return db.get_dataframe('sales', '''
        SELECT s.sale_id, s.invoice_no, s.total_amount, s.payment_status,
               c.name as customer_name, c.mobile, c.village,
               (s.total_amount - COALESCE(SUM(p.amount), 0)) as pending_amount
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN payments p ON s.sale_id = p.sale_id
        WHERE s.payment_status IN ('Pending', 'Partial')
        GROUP BY s.sale_id
        HAVING pending_amount > 0
        ORDER BY s.sale_date DESC
        ''')
    except Exception as e:
        st.error(f"Error getting pending sales: {e}")
        return pd.DataFrame()

def add_payment_to_database(db, payment_data):
    """Add payment record to database"""
    try:
        db.execute_query('''
        INSERT INTO payments (sale_id, payment_date, payment_method, amount, rrn, reference, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            payment_data['sale_id'],
            payment_data['payment_date'],
            payment_data['payment_method'],
            payment_data['amount'],
            payment_data['rrn'],
            payment_data['reference'],
            payment_data['status'],
            payment_data['notes']
        ), log_action=False)
        
        # Get the inserted payment_id
        result = db.execute_query('SELECT last_insert_rowid()', log_action=False)
        return result[0][0] if result else -1
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return -1

def update_sale_payment_status(db, sale_id):
    """Update sale payment status based on payments"""
    try:
        # Get total paid amount
        payments_data = db.get_dataframe('payments', f'''
        SELECT COALESCE(SUM(amount), 0) as total_paid
        FROM payments 
        WHERE sale_id = {sale_id} AND status = 'Completed'
        ''')
        
        if not payments_data.empty:
            total_paid = payments_data.iloc[0]['total_paid']
            
            # Get sale total
            sale_data = db.get_dataframe('sales', f'SELECT total_amount FROM sales WHERE sale_id = {sale_id}')
            if not sale_data.empty:
                sale_total = sale_data.iloc[0]['total_amount']
                
                # Determine payment status
                if total_paid >= sale_total:
                    new_status = 'Paid'
                elif total_paid > 0:
                    new_status = 'Partial'
                else:
                    new_status = 'Pending'
                
                # Update sale status
                db.execute_query('''
                UPDATE sales SET payment_status = ?, updated_date = CURRENT_TIMESTAMP
                WHERE sale_id = ?
                ''', (new_status, sale_id), log_action=False)
                
    except Exception as e:
        st.error(f"Error updating payment status: {e}")

def send_payment_notification(whatsapp_manager, db, sale_id, payment_amount):
    """Send payment confirmation to customer"""
    try:
        # Get sale and customer details
        sale_data = db.get_dataframe('sales', f'''
        SELECT s.*, c.name as customer_name, c.mobile
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        WHERE s.sale_id = {sale_id}
        ''')
        
        if not sale_data.empty:
            sale = sale_data.iloc[0]
            
            if sale.get('mobile'):
                message = f"""Hello {sale['customer_name']}! 💰

We have received your payment of ₹{payment_amount:,.2f} for invoice {sale['invoice_no']}.

Thank you for your prompt payment!

If you have any questions, please feel free to contact us.

Best regards,
Sales Team"""
                
                success = whatsapp_manager.send_message(sale['mobile'], message)
                if success:
                    st.success("📱 Payment confirmation sent to customer!")
                else:
                    st.warning("⚠️ Could not send payment confirmation")
    
    except Exception as e:
        st.warning(f"Could not send payment notification: {e}")

def show_payment_summary(db, payment_id):
    """Show summary of recorded payment"""
    try:
        payment_data = db.get_dataframe('payments', f'''
        SELECT p.*, s.invoice_no, s.total_amount, c.name as customer_name, c.village
        FROM payments p
        LEFT JOIN sales s ON p.sale_id = s.sale_id
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        WHERE p.payment_id = {payment_id}
        ''')
        
        if not payment_data.empty:
            payment = payment_data.iloc[0]
            
            st.markdown("## 🎉 Payment Recorded Successfully!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💳 Payment Details")
                st.write(f"**Payment ID:** {payment_id}")
                st.write(f"**Invoice No:** {payment['invoice_no']}")
                st.write(f"**Customer:** {payment['customer_name']}")
                st.write(f"**Village:** {payment['village']}")
                st.write(f"**Payment Method:** {payment['payment_method']}")
            
            with col2:
                st.subheader("💰 Amount & Status")
                st.write(f"**Amount Paid:** ₹{payment['amount']:,.2f}")
                st.write(f"**Sale Total:** ₹{payment['total_amount']:,.2f}")
                st.write(f"**Payment Date:** {payment['payment_date']}")
                st.write(f"**Status:** {payment['status']}")
                
                if payment['reference']:
                    st.write(f"**Reference:** {payment['reference']}")
            
            # Quick actions
            st.markdown("### ⚡ Quick Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 View Payment History"):
                    st.session_state.current_tab = "📋 Payment History"
            
            with col2:
                if st.button("💰 Record Another"):
                    st.rerun()
            
            with col3:
                if st.button("⏳ View Pending"):
                    st.session_state.current_tab = "⏳ Pending Payments"
                    
    except Exception as e:
        st.error(f"Error displaying payment summary: {e}")

def show_payment_history_tab(db):
    """Show payment history and records"""
    st.subheader("📋 Payment History")
    
    try:
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Status filter
        status_filter = st.multiselect("Filter by Status", 
                                     ["Completed", "Pending", "Failed"],
                                     default=["Completed"])
        
        # Method filter
        methods = db.get_dataframe('payments', "SELECT DISTINCT payment_method FROM payments")
        if not methods.empty:
            method_options = methods['payment_method'].dropna().unique().tolist()
            method_filter = st.multiselect("Filter by Method", method_options, default=method_options)
        
        # Get payments data
        payments_data = get_payments_data(db, start_date, end_date, status_filter, method_filter)
        
        if not payments_data.empty:
            st.write(f"**💰 Showing {len(payments_data)} payments**")
            
            # Display payments
            display_data = payments_data[['payment_date', 'customer_name', 'invoice_no', 'amount', 
                                        'payment_method', 'status', 'reference']].copy()
            display_data.columns = ['Date', 'Customer', 'Invoice', 'Amount', 'Method', 'Status', 'Reference']
            display_data['Amount'] = display_data['Amount'].apply(lambda x: f"₹{x:,.2f}")
            display_data = display_data.sort_values('Date', ascending=False)
            
            st.dataframe(display_data, use_container_width=True)
            
            # Payment statistics
            st.subheader("📊 Payment Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_payments = len(payments_data)
                st.metric("Total Payments", total_payments)
            
            with col2:
                total_amount = payments_data['amount'].sum()
                st.metric("Total Amount", f"₹{total_amount:,.2f}")
            
            with col3:
                completed = len(payments_data[payments_data['status'] == 'Completed'])
                st.metric("Completed", completed)
            
            with col4:
                avg_payment = payments_data['amount'].mean()
                st.metric("Avg Payment", f"₹{avg_payment:,.0f}")
        
        else:
            st.info("No payments found for the selected criteria.")
            
    except Exception as e:
        st.error(f"Error loading payment history: {e}")

def get_payments_data(db, start_date, end_date, status_filter, method_filter):
    """Get payments data with filters"""
    try:
        query = '''
        SELECT p.*, s.invoice_no, c.name as customer_name, c.village
        FROM payments p
        LEFT JOIN sales s ON p.sale_id = s.sale_id
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        WHERE p.payment_date BETWEEN ? AND ?
        '''
        
        params = [start_date, end_date]
        
        if status_filter:
            placeholders = ','.join(['?' for _ in status_filter])
            query += f' AND p.status IN ({placeholders})'
            params.extend(status_filter)
        
        if method_filter:
            placeholders = ','.join(['?' for _ in method_filter])
            query += f' AND p.payment_method IN ({placeholders})'
            params.extend(method_filter)
        
        query += ' ORDER BY p.payment_date DESC'
        
        return db.get_dataframe('payments', query, params=params)
        
    except Exception as e:
        st.error(f"Error getting payments data: {e}")
        return pd.DataFrame()

def show_pending_payments_tab(db, whatsapp_manager):
    """Show pending payments and reminders"""
    st.subheader("⏳ Pending Payments")
    
    try:
        # Get pending payments
        pending_payments = get_pending_sales(db)
        
        if not pending_payments.empty:
            st.warning(f"🚨 {len(pending_payments)} Sales with Pending Payments!")
            
            # Display pending payments
            display_data = pending_payments[['invoice_no', 'customer_name', 'village', 'total_amount', 'pending_amount', 'payment_status']].copy()
            display_data.columns = ['Invoice', 'Customer', 'Village', 'Total Amount', 'Pending Amount', 'Status']
            display_data['Total Amount'] = display_data['Total Amount'].apply(lambda x: f"₹{x:,.2f}")
            display_data['Pending Amount'] = display_data['Pending Amount'].apply(lambda x: f"₹{x:,.2f}")
            
            st.dataframe(display_data, use_container_width=True)
            
            # Total pending amount
            total_pending = pending_payments['pending_amount'].sum()
            st.error(f"**💰 Total Pending Amount: ₹{total_pending:,.2f}**")
            
            # Send reminders
            st.subheader("📱 Send Payment Reminders")
            selected_invoices = st.multiselect("Select Invoices for Reminders",
                                             pending_payments['invoice_no'].tolist())
            
            if selected_invoices and whatsapp_manager:
                if st.button("📧 Send WhatsApp Reminders"):
                    send_bulk_payment_reminders(whatsapp_manager, db, pending_payments, selected_invoices)
                    st.success("✅ Payment reminders sent!")
            
            elif not whatsapp_manager:
                st.info("📱 WhatsApp manager not available for sending reminders")
        
        else:
            st.success("🎉 All payments are cleared! No pending payments.")
            
    except Exception as e:
        st.error(f"Error loading pending payments: {e}")

def send_bulk_payment_reminders(whatsapp_manager, db, pending_payments, selected_invoices):
    """Send bulk payment reminders"""
    try:
        selected_sales = pending_payments[pending_payments['invoice_no'].isin(selected_invoices)]
        
        for _, sale in selected_sales.iterrows():
            if sale.get('mobile'):
                message = f"""Hello {sale['customer_name']}! ⏰

Friendly reminder regarding your pending payment.

Invoice: {sale['invoice_no']}
Pending Amount: ₹{sale['pending_amount']:,.2f}

Please make the payment at your earliest convenience.

Thank you for your cooperation!

Best regards,
Sales Team"""
                
                whatsapp_manager.send_message(sale['mobile'], message)
        
    except Exception as e:
        st.error(f"Error sending reminders: {e}")

def show_payment_analytics_tab(db):
    """Show payment analytics and trends"""
    st.subheader("📊 Payment Analytics")
    
    try:
        # Get payments data for analytics
        payments_data = db.get_dataframe('payments', '''
        SELECT p.*, s.invoice_no, c.name as customer_name
        FROM payments p
        LEFT JOIN sales s ON p.sale_id = s.sale_id
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        WHERE p.status = 'Completed'
        ORDER BY p.payment_date DESC
        ''')
        
        if not payments_data.empty:
            # Payment method distribution
            st.subheader("💳 Payment Methods Distribution")
            method_stats = payments_data['payment_method'].value_counts()
            
            if not method_stats.empty:
                fig = px.pie(values=method_stats.values, names=method_stats.index,
                           title='Payment Methods Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            # Monthly payment trend
            st.subheader("📈 Monthly Payment Trend")
            try:
                payments_data['payment_date'] = pd.to_datetime(payments_data['payment_date'])
                monthly_payments = payments_data.groupby(payments_data['payment_date'].dt.to_period('M')).agg({
                    'amount': 'sum',
                    'payment_id': 'count'
                }).reset_index()
                monthly_payments['payment_date'] = monthly_payments['payment_date'].astype(str)
                
                if not monthly_payments.empty:
                    fig = px.line(monthly_payments, x='payment_date', y='amount',
                                title='Monthly Payment Amount Trend',
                                labels={'payment_date': 'Month', 'amount': 'Amount (₹)'})
                    st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("Could not generate monthly trend chart")
            
            # Top customers by payments
            st.subheader("🏆 Top Customers by Payments")
            customer_stats = payments_data.groupby('customer_name').agg({
                'amount': 'sum',
                'payment_id': 'count'
            }).reset_index()
            customer_stats.columns = ['Customer', 'Total Paid', 'Payment Count']
            customer_stats = customer_stats.sort_values('Total Paid', ascending=False).head(10)
            
            st.dataframe(customer_stats, use_container_width=True)
        
        else:
            st.info("No payment data available for analytics.")
            
    except Exception as e:
        st.error(f"Error loading payment analytics: {e}")