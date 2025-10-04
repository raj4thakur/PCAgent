# enhanced_sales_manager.py
from datetime import datetime, timedelta
import pandas as pd
import sqlite3

class EnhancedSalesManager:
    def __init__(self, db_manager, data_processor):
        self.db_manager = db_manager
        self.data_processor = data_processor
    
    def batch_import_data(self, directory_path):
        """Import all data from a directory"""
        return self.data_processor.process_directory(directory_path)
    
    def get_customer_insights(self):
        """Get comprehensive customer insights"""
        conn = self.db_manager.get_connection()
        
        # Top customers by spending
        top_customers = pd.read_sql('''
        SELECT c.name, c.village, SUM(s.total_amount) as total_spent, COUNT(s.sale_id) as purchases
        FROM customers c
        JOIN sales s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id
        ORDER BY total_spent DESC
        LIMIT 20
        ''', conn)
        
        # Village performance
        village_performance = pd.read_sql('''
        SELECT village, COUNT(DISTINCT customer_id) as customers, 
               SUM(total_amount) as total_sales, AVG(total_amount) as avg_sale
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        GROUP BY village
        ORDER BY total_sales DESC
        ''', conn)
        
        return {
            'top_customers': top_customers,
            'village_performance': village_performance
        }
    
    def generate_comprehensive_report(self, start_date=None, end_date=None):
        """Generate detailed business intelligence report"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self.db_manager.get_connection()
        
        reports = {}
        
        # Sales trends
        reports['sales_trends'] = pd.read_sql(f'''
        SELECT DATE(sale_date) as date, SUM(total_amount) as daily_sales,
               SUM(total_liters) as daily_liters, COUNT(*) as transactions
        FROM sales
        WHERE sale_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY DATE(sale_date)
        ORDER BY date
        ''', conn)
        
        # Product performance
        reports['product_performance'] = pd.read_sql(f'''
        SELECT p.packing_type, p.capacity_ltr, SUM(si.quantity) as total_quantity,
               SUM(si.amount) as total_revenue, COUNT(DISTINCT s.sale_id) as transactions
        FROM sale_items si
        JOIN products p ON si.product_id = p.product_id
        JOIN sales s ON si.sale_id = s.sale_id
        WHERE s.sale_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY p.product_id
        ORDER BY total_revenue DESC
        ''', conn)
        
        # Payment analysis
        reports['payment_analysis'] = pd.read_sql(f'''
        SELECT 
            CASE 
                WHEN payment_date IS NOT NULL THEN 'Paid'
                ELSE 'Pending'
            END as payment_status,
            COUNT(*) as transactions,
            SUM(total_amount) as amount,
            AVG(total_amount) as avg_amount
        FROM sales
        WHERE sale_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY payment_status
        ''', conn)
        
        return reports