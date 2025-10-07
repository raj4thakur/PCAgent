# whatsapp_manager.py
import pywhatkit
import logging
from datetime import datetime, timedelta

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
                return False
            
            # Schedule message (sends in 2 minutes)
            send_time = datetime.now() + timedelta(minutes=2)
            
            if image_path and os.path.exists(image_path):
                pywhatkit.sendwhats_image(
                    phone_number, 
                    image_path, 
                    message,
                    wait_time=20
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
            return True
            
        except Exception as e:
            self.logger.error(f"WhatsApp sending failed: {e}")
            self._log_message(phone_number, message, "failed", str(e))
            return False
    
    def send_bulk_messages(self, customer_ids, message_template):
        """Send messages to multiple customers"""
        results = []
        for customer_id in customer_ids:
            customer = self.db.get_dataframe('customers', 
                f"SELECT * FROM customers WHERE customer_id = {customer_id}")
            
            if not customer.empty:
                customer_data = customer.iloc[0]
                phone = customer_data['mobile']
                personalized_msg = self._personalize_message(message_template, customer_data)
                
                success = self.send_message(phone, personalized_msg)
                results.append({
                    'customer_id': customer_id,
                    'customer_name': customer_data['name'],
                    'status': 'sent' if success else 'failed'
                })
        
        return results
    
    def _clean_phone_number(self, phone):
        """Clean and validate phone number"""
        if not phone:
            return None
        
        # Remove spaces, hyphens, etc.
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if missing (assuming India)
        if len(clean_phone) == 10:
            clean_phone = '91' + clean_phone
        
        return clean_phone
    
    def _personalize_message(self, template, customer_data):
        """Personalize message with customer data"""
        message = template
        message = message.replace('{name}', customer_data.get('name', 'Customer'))
        message = message.replace('{village}', customer_data.get('village', ''))
        message = message.replace('{taluka}', customer_data.get('taluka', ''))
        return message
    
    def _log_message(self, phone, message, status, error=None):
        """Log WhatsApp message in database"""
        try:
            self.db.execute_query('''
            INSERT INTO whatsapp_logs (phone_number, message_content, status, error_message)
            VALUES (?, ?, ?, ?)
            ''', (phone, message, status, error))
        except Exception as e:
            self.logger.error(f"Failed to log message: {e}")