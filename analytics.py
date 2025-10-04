import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class Analytics:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_sales_summary(self):
        """Get comprehensive sales summary statistics"""
        try:
            sales_df = self.db.get_dataframe('sales')
            payments_df = self.db.get_dataframe('payments')
            
            if sales_df.empty:
                return {
                    'total_sales': 0,
                    'total_payments': 0,
                    'pending_amount': 0,
                    'total_transactions': 0,
                    'avg_sale_value': 0
                }
            
            total_sales = sales_df['total_amount'].sum()
            total_payments = payments_df['amount'].sum() if not payments_df.empty else 0
            pending_amount = total_sales - total_payments
            
            return {
                'total_sales': total_sales,
                'total_payments': total_payments,
                'pending_amount': pending_amount,
                'total_transactions': len(sales_df),
                'avg_sale_value': sales_df['total_amount'].mean()
            }
        except Exception as e:
            return {
                'total_sales': 0,
                'total_payments': 0,
                'pending_amount': 0,
                'total_transactions': 0,
                'avg_sale_value': 0
            }
    
    def get_customer_analysis(self):
        """Analyze customer data"""
        try:
            customers_df = self.db.get_dataframe('customers')
            sales_df = self.db.get_dataframe('sales')
            
            if customers_df.empty:
                return {
                    'total_customers': 0,
                    'village_distribution': {},
                    'top_customers': {}
                }
            
            # Customer distribution by village
            village_stats = customers_df['village'].value_counts().head(10)
            
            # Top customers by spending
            if not sales_df.empty:
                customer_sales = sales_df.groupby('customer_id')['total_amount'].sum()
                top_customers = customer_sales.nlargest(10)
            else:
                top_customers = pd.Series(dtype=float)
            
            return {
                'total_customers': len(customers_df),
                'village_distribution': village_stats.to_dict(),
                'top_customers': top_customers.to_dict()
            }
        except Exception as e:
            return {
                'total_customers': 0,
                'village_distribution': {},
                'top_customers': {}
            }
    
    def get_payment_analysis(self):
        """Analyze payment data"""
        try:
            pending_payments = self.db.get_pending_payments()
            payments_df = self.db.get_dataframe('payments')
            
            if pending_payments.empty:
                return {
                    'total_pending': 0,
                    'customer_pending': {},
                    'payment_methods': {}
                }
            
            # Group by customer
            customer_pending = pending_payments.groupby('customer_id')['pending_amount'].sum()
            
            # Payment method distribution
            if not payments_df.empty:
                payment_methods = payments_df['payment_method'].value_counts()
            else:
                payment_methods = pd.Series(dtype=object)
            
            return {
                'total_pending': pending_payments['pending_amount'].sum(),
                'customer_pending': customer_pending.to_dict(),
                'payment_methods': payment_methods.to_dict()
            }
        except Exception as e:
            return {
                'total_pending': 0,
                'customer_pending': {},
                'payment_methods': {}
            }
    
    def get_demo_conversion_rates(self):
        """Calculate demo conversion rates"""
        try:
            demos_df = self.db.get_demo_conversions()
            
            if demos_df.empty:
                return {
                    'total_demos': 0,
                    'converted_demos': 0,
                    'conversion_rate': 0
                }
            
            total_demos = len(demos_df)
            converted_demos = len(demos_df[demos_df['conversion_status'] == 'Converted'])
            conversion_rate = (converted_demos / total_demos) * 100 if total_demos > 0 else 0
            
            return {
                'total_demos': total_demos,
                'converted_demos': converted_demos,
                'conversion_rate': conversion_rate
            }
        except Exception as e:
            return {
                'total_demos': 0,
                'converted_demos': 0,
                'conversion_rate': 0
            }
    
    def get_sales_trend(self):
        """Get sales trend data for charts"""
        try:
            sales_df = self.db.get_dataframe('sales')
            
            if sales_df.empty:
                return pd.DataFrame()
            
            # Convert sale_date to datetime if it's not
            sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date'])
            
            # Group by date
            daily_sales = sales_df.groupby('sale_date')['total_amount'].sum().reset_index()
            daily_sales = daily_sales.sort_values('sale_date')
            
            return daily_sales
        except Exception as e:
            return pd.DataFrame()
    
    def get_payment_distribution(self):
        """Get payment distribution for charts"""
        try:
            payments_df = self.db.get_dataframe('payments')
            
            if payments_df.empty:
                return pd.DataFrame()
            
            payment_dist = payments_df.groupby('payment_method')['amount'].sum().reset_index()
            return payment_dist
        except Exception as e:
            return pd.DataFrame()
    
    def get_product_performance(self):
        """Get product performance data"""
        try:
            sale_items_df = self.db.get_dataframe('sale_items', '''
            SELECT si.*, p.product_name 
            FROM sale_items si 
            JOIN products p ON si.product_id = p.product_id
            ''')
            
            if sale_items_df.empty:
                return pd.DataFrame()
            
            product_perf = sale_items_df.groupby('product_name').agg({
                'quantity': 'sum',
                'amount': 'sum'
            }).reset_index()
            
            return product_perf
        except Exception as e:
            return pd.DataFrame()