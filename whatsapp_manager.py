# whatsapp_manager.py
import pywhatkit
import logging
from datetime import datetime, timedelta
import time
import pandas as pd
import os
import streamlit as st

class WhatsAppManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, phone_number, message, image_path=None):
        """Send WhatsApp message with error handling"""
        try:
            # Clean phone number
            phone_number = self._clean_phone_number(phone_number)
            if not phone_number:
                self._log_message(phone_number, message, "failed", "Invalid phone number")
                return False
            
            st.info(f"📱 Preparing to send WhatsApp message to {phone_number}")
            
            # Schedule message (sends in 2 minutes)
            send_time = datetime.now() + timedelta(minutes=2)
            
            try:
                if image_path and os.path.exists(image_path):
                    pywhatkit.sendwhats_image(
                        phone_number, 
                        image_path, 
                        message,
                        wait_time=20,
                        tab_close=True
                    )
                else:
                    pywhatkit.sendwhatmsg(
                        phone_number,
                        message,
                        send_time.hour,
                        send_time.minute,
                        wait_time=20,
                        tab_close=True
                    )
                
                # Log the message
                self._log_message(phone_number, message, "sent")
                st.success(f"✅ Message sent successfully to {phone_number}")
                return True
                
            except Exception as e:
                error_msg = f"PyWhatKit error: {str(e)}"
                st.error(f"❌ {error_msg}")
                self._log_message(phone_number, message, "failed", error_msg)
                return False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            st.error(f"❌ {error_msg}")
            self._log_message(phone_number, message, "failed", error_msg)
            return False
    
    def send_bulk_messages(self, customer_ids, message_template):
        """Send messages to multiple customers"""
        results = []
        total_customers = len(customer_ids)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, customer_id in enumerate(customer_ids):
            try:
                # Update progress
                progress = (i + 1) / total_customers
                progress_bar.progress(progress)
                status_text.text(f"Processing {i+1}/{total_customers} customers...")
                
                customer = self.db.get_dataframe('customers', 
                    f"SELECT * FROM customers WHERE customer_id = {customer_id}")
                
                if not customer.empty:
                    customer_data = customer.iloc[0]
                    phone = customer_data['mobile']
                    
                    if phone and pd.notna(phone) and str(phone).strip():
                        personalized_msg = self._personalize_message(message_template, customer_data)
                        success = self.send_message(phone, personalized_msg)
                        
                        results.append({
                            'customer_id': customer_id,
                            'customer_name': customer_data['name'],
                            'phone': phone,
                            'status': 'sent' if success else 'failed',
                            'message': personalized_msg[:50] + "..." if len(personalized_msg) > 50 else personalized_msg
                        })
                    else:
                        results.append({
                            'customer_id': customer_id,
                            'customer_name': customer_data['name'],
                            'phone': phone,
                            'status': 'failed',
                            'message': 'No phone number available'
                        })
                else:
                    results.append({
                        'customer_id': customer_id,
                        'customer_name': 'Unknown',
                        'phone': 'N/A',
                        'status': 'failed',
                        'message': 'Customer not found'
                    })
                    
                # Small delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                results.append({
                    'customer_id': customer_id,
                    'customer_name': 'Error',
                    'phone': 'N/A',
                    'status': 'failed',
                    'message': f'Error: {str(e)}'
                })
        
        progress_bar.empty()
        status_text.empty()
        
        return results
    
    def send_distributor_message(self, distributor_id, message):
        """Send message to distributor"""
        try:
            distributor = self.db.get_dataframe('distributors',
                f"SELECT * FROM distributors WHERE distributor_id = {distributor_id}")
            
            if not distributor.empty:
                distributor_data = distributor.iloc[0]
                phone = distributor_data['mantri_mobile']
                
                if phone and pd.notna(phone) and str(phone).strip():
                    personalized_msg = self._personalize_distributor_message(message, distributor_data)
                    return self.send_message(phone, personalized_msg)
                else:
                    st.warning(f"No mobile number found for distributor: {distributor_data['name']}")
                    return False
            else:
                st.error("Distributor not found")
                return False
                
        except Exception as e:
            st.error(f"Error sending distributor message: {e}")
            return False
    
    def _personalize_distributor_message(self, template, distributor_data):
        """Personalize message for distributor"""
        message = template
        message = message.replace('{name}', distributor_data.get('mantri_name', 'Distributor'))
        message = message.replace('{distributor_name}', distributor_data.get('name', ''))
        message = message.replace('{village}', distributor_data.get('village', ''))
        message = message.replace('{taluka}', distributor_data.get('taluka', ''))
        message = message.replace('{sabhasad_count}', str(distributor_data.get('sabhasad_count', 0)))
        return message
    
    def _clean_phone_number(self, phone):
        """Clean and validate phone number"""
        if not phone or pd.isna(phone):
            return None
        
        # Convert to string and remove spaces, hyphens, etc.
        phone_str = str(phone).strip()
        clean_phone = ''.join(filter(str.isdigit, phone_str))
        
        # Validate length
        if len(clean_phone) < 10:
            return None
        
        # Add country code if missing (assuming India)
        if len(clean_phone) == 10:
            clean_phone = '91' + clean_phone
        elif len(clean_phone) == 11 and clean_phone.startswith('0'):
            clean_phone = '91' + clean_phone[1:]
        elif len(clean_phone) == 12 and clean_phone.startswith('91'):
            # Already correct format
            pass
        else:
            # If longer than 12 digits, take last 12
            if len(clean_phone) > 12:
                clean_phone = clean_phone[-12:]
        
        return '+' + clean_phone
    
    def _personalize_message(self, template, customer_data):
        """Personalize message with customer data"""
        message = template
        message = message.replace('{name}', customer_data.get('name', 'Customer'))
        message = message.replace('{village}', customer_data.get('village', ''))
        message = message.replace('{taluka}', customer_data.get('taluka', ''))
        message = message.replace('{district}', customer_data.get('district', ''))
        
        # Add current date
        current_date = datetime.now().strftime('%d-%m-%Y')
        message = message.replace('{date}', current_date)
        
        return message
    
    def _log_message(self, phone, message, status, error=None):
        """Log WhatsApp message in database"""
        try:
            # Ensure whatsapp_logs table exists
            self.db.execute_query('''
            CREATE TABLE IF NOT EXISTS whatsapp_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                distributor_id INTEGER,
                phone_number TEXT,
                message_content TEXT,
                message_type TEXT,
                status TEXT,
                error_message TEXT,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE SET NULL,
                FOREIGN KEY (distributor_id) REFERENCES distributors (distributor_id) ON DELETE SET NULL
            )
            ''', log_action=False)
            
            # Find customer by phone (last 10 digits)
            customer_result = self.db.execute_query(
                'SELECT customer_id FROM customers WHERE mobile LIKE ?',
                (f'%{phone[-10:]}%',),
                log_action=False
            )
            
            customer_id = customer_result[0][0] if customer_result else None
            
            # Find distributor by phone
            distributor_result = self.db.execute_query(
                'SELECT distributor_id FROM distributors WHERE mantri_mobile LIKE ?',
                (f'%{phone[-10:]}%',),
                log_action=False
            )
            
            distributor_id = distributor_result[0][0] if distributor_result else None
            
            # Determine message type
            message_type = 'customer' if customer_id else 'distributor' if distributor_id else 'general'
            
            self.db.execute_query('''
            INSERT INTO whatsapp_logs (customer_id, distributor_id, phone_number, message_content, message_type, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, distributor_id, phone, message, message_type, status, error), log_action=False)
            
        except Exception as e:
            self.logger.error(f"Failed to log message: {e}")
    
    def get_message_stats(self):
        """Get messaging statistics"""
        try:
            stats = self.db.execute_query('''
            SELECT 
                COUNT(*) as total_messages,
                SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent_messages,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_messages,
                MAX(sent_date) as last_message_date
            FROM whatsapp_logs
            ''', log_action=False)
            
            if stats:
                return {
                    'total_messages': stats[0][0] or 0,
                    'sent_messages': stats[0][1] or 0,
                    'failed_messages': stats[0][2] or 0,
                    'last_message_date': stats[0][3]
                }
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting message stats: {e}")
            return {}
    
    def get_recent_messages(self, limit=10):
        """Get recent WhatsApp messages"""
        try:
            messages = self.db.get_dataframe('whatsapp_logs', f'''
            SELECT wl.*, 
                   c.name as customer_name,
                   d.name as distributor_name
            FROM whatsapp_logs wl
            LEFT JOIN customers c ON wl.customer_id = c.customer_id
            LEFT JOIN distributors d ON wl.distributor_id = d.distributor_id
            ORDER BY wl.sent_date DESC
            LIMIT {limit}
            ''')
            return messages
        except Exception as e:
            self.logger.error(f"Error getting recent messages: {e}")
            return pd.DataFrame()
    
    def send_welcome_message(self, phone_number, name, role="customer"):
        """Send welcome message to new customers/distributors"""
        if role == "distributor":
            message = f"""Welcome {name}! 🎉

Thank you for joining our distributor network! 

We're excited to have you on board and look forward to working together to grow your business.

Our team will contact you shortly to discuss:
• Training schedule
• Product information  
• Sales strategies
• Support systems

For any immediate queries, feel free to contact us.

Best regards,
Sales Team"""
        else:
            message = f"""Welcome {name}! 🎉

Thank you for choosing us! 

We're delighted to have you as our customer and look forward to serving you with the best products and service.

Feel free to reach out for any queries or support.

Best regards,
Sales Team"""
        
        return self.send_message(phone_number, message)
    
    def send_payment_reminder(self, customer_id, invoice_no, pending_amount):
        """Send payment reminder to customer"""
        try:
            customer = self.db.get_dataframe('customers',
                f"SELECT * FROM customers WHERE customer_id = {customer_id}")
            
            if not customer.empty:
                customer_data = customer.iloc[0]
                phone = customer_data['mobile']
                
                if phone and pd.notna(phone) and str(phone).strip():
                    message = f"""Hello {customer_data['name']},

This is a friendly reminder regarding your pending payment.

Invoice: {invoice_no}
Pending Amount: ₹{pending_amount:,.2f}

Please make the payment at your earliest convenience.

Thank you for your cooperation!

Best regards,
Sales Team"""
                    
                    return self.send_message(phone, message)
                else:
                    st.warning(f"No mobile number found for customer: {customer_data['name']}")
                    return False
            else:
                st.error("Customer not found")
                return False
                
        except Exception as e:
            st.error(f"Error sending payment reminder: {e}")
            return False

# Utility function to check WhatsApp availability
def check_whatsapp_availability():
    """Check if WhatsApp features are available"""
    try:
        import pywhatkit
        return True
    except ImportError:
        return False

# Example usage and test function
def test_whatsapp_manager(db):
    """Test WhatsApp manager functionality"""
    st.subheader("🧪 WhatsApp Manager Test")
    
    if st.button("Test WhatsApp Connection"):
        try:
            manager = WhatsAppManager(db)
            
            # Test phone number cleaning
            test_numbers = ["9876543210", "09876543210", "919876543210"]
            for num in test_numbers:
                cleaned = manager._clean_phone_number(num)
                st.write(f"Original: {num} → Cleaned: {cleaned}")
            
            # Test message personalization
            test_customer = {'name': 'John Doe', 'village': 'Test Village'}
            personalized = manager._personalize_message("Hello {name} from {village}!", test_customer)
            st.write(f"Personalized message: {personalized}")
            
            st.success("✅ WhatsApp manager test completed successfully!")
            
        except Exception as e:
            st.error(f"❌ WhatsApp manager test failed: {e}")