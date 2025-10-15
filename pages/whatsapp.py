# pages/whatsapp.py
import streamlit as st
import pandas as pd

def show_whatsapp_page(db, whatsapp_manager):
    """Show WhatsApp messaging page"""
    st.title("💬 WhatsApp Messaging")
    
    if not whatsapp_manager:
        st.error("WhatsApp manager not available. Please install pywhatkit: pip install pywhatkit")
        st.info("""
        **To enable WhatsApp messaging:**
        1. Install: `pip install pywhatkit`
        2. Make sure you're logged into WhatsApp Web in your default browser
        3. Ensure phone numbers include country code (e.g., +91 for India)
        """)
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["Single Message", "Bulk Messages", "Templates", "Message History"])
        
        with tab1:
            show_single_message_tab(db, whatsapp_manager)
        
        with tab2:
            show_bulk_messages_tab(db, whatsapp_manager)
        
        with tab3:
            show_templates_tab()
        
        with tab4:
            show_message_history_tab(db)

def show_single_message_tab(db, whatsapp_manager):
    """Show single message tab"""
    st.subheader("📱 Send Single Message")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Option 1: Select from existing customers
        st.write("**Select from Existing Customers**")
        customers = db.get_dataframe('customers')
        if not customers.empty:
            customer_options = {f"{row['name']} ({row['mobile']}) - {row['village']}": row for _, row in customers.iterrows()}
            selected_customer_key = st.selectbox("Choose Customer", options=[""] + list(customer_options.keys()))
            
            if selected_customer_key:
                customer_data = customer_options[selected_customer_key]
                st.write(f"**Selected:** {customer_data['name']}")
                st.write(f"**Mobile:** {customer_data['mobile']}")
                st.write(f"**Village:** {customer_data['village']}")
                
                # Pre-fill message with template
                message_template = st.selectbox("Quick Template", [
                    "Custom Message",
                    "Payment Reminder",
                    "Demo Follow-up", 
                    "New Product Announcement",
                    "Festival Greeting"
                ])
                
    with col2:
        # Option 2: Manual entry
        st.write("**Or Enter Manually**")
        manual_name = st.text_input("Recipient Name")
        manual_mobile = st.text_input("Mobile Number (with country code)", placeholder="+91XXXXXXXXXX")
    
    # Message content and sending logic would continue here...
    # (I'll show the rest in the next message due to length)