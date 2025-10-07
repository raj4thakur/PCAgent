# enhanced_automation.py
import schedule
import time
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime, timedelta

class AutomationManager:
    def __init__(self, db_manager, whatsapp_manager):
        self.db = db_manager
        self.whatsapp = whatsapp_manager
    
    def daily_payment_reminders(self):
        """Send payment reminders for overdue payments"""
        overdue_payments = self.db.get_pending_payments()
        
        for _, payment in overdue_payments.iterrows():
            if payment['pending_amount'] > 0:
                customer = self.db.get_dataframe('customers', 
                    f"SELECT * FROM customers WHERE customer_id = {payment['customer_id']}")
                
                if not customer.empty:
                    customer_data = customer.iloc[0]
                    message = f"""Hello {customer_data['name']},

This is a friendly reminder that your payment of ₹{payment['pending_amount']:,.2f} for invoice {payment['invoice_no']} is overdue.

Please make the payment at your earliest convenience.

Thank you,
Sales Team"""
                    
                    self.whatsapp.send_message(customer_data['mobile'], message)
    
    def demo_followups(self):
        """Send follow-up messages for demos"""
        upcoming_followups = self.db.get_dataframe('demos', '''
        SELECT d.*, c.name as customer_name, c.mobile, p.product_name
        FROM demos d
        JOIN customers c ON d.customer_id = c.customer_id
        JOIN products p ON d.product_id = p.product_id
        WHERE d.follow_up_date = date('now')
        AND d.conversion_status = 'Not Converted'
        ''')
        
        for _, demo in upcoming_followups.iterrows():
            message = f"""Hello {demo['customer_name']},

Following up on your demo of {demo['product_name']} on {demo['demo_date']}. 

How was your experience? Would you like to place an order or need another demo?

Best regards,
Sales Team"""
            
            self.whatsapp.send_message(demo['mobile'], message)
    
    def weekly_performance_report(self):
        """Generate and send weekly performance report"""
        analytics = Analytics(self.db)
        
        sales_summary = analytics.get_sales_summary()
        demo_stats = analytics.get_demo_conversion_rates()
        payment_analysis = analytics.get_payment_analysis()
        
        report = f"""
        📊 WEEKLY PERFORMANCE REPORT
        ----------------------------
        Total Sales: ₹{sales_summary.get('total_sales', 0):,.2f}
        Pending Payments: ₹{sales_summary.get('pending_amount', 0):,.2f}
        Demo Conversion Rate: {demo_stats.get('conversion_rate', 0):.1f}%
        Total Customers: {analytics.get_customer_analysis().get('total_customers', 0)}
        
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        # You can extend this to email the report
        self._save_report(report)
        return report
    
    def _save_report(self, report):
        """Save report to file"""
        filename = f"reports/weekly_report_{datetime.now().strftime('%Y%m%d')}.txt"
        os.makedirs('reports', exist_ok=True)
        
        with open(filename, 'w') as f:
            f.write(report)