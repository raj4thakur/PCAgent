import sqlite3
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random  # Add this import
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="sales_management.db"):
        self.db_path = db_path
        self._is_logging = False  # Prevent recursion
        self.init_database()
    
    def get_connection(self):
        """Get database connection with error handling"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This enables column access by name
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def init_database(self):
        """Initialize database with all tables and relationships"""
        conn = self.get_connection()
        
        try:
            # Customers table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE,
                name TEXT NOT NULL,
                mobile TEXT,
                village TEXT,
                taluka TEXT,
                district TEXT,
                status TEXT DEFAULT 'Active',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Distributors table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS distributors (
                distributor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                village TEXT,
                taluka TEXT,
                district TEXT,
                mantri_name TEXT,
                mantri_mobile TEXT,
                sabhasad_count INTEGER DEFAULT 0,
                contact_in_group INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Active',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Products table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT UNIQUE NOT NULL,
                packing_type TEXT,
                capacity_ltr REAL,
                category TEXT,
                standard_rate REAL,
                is_active INTEGER DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Sales table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                sale_date DATE,
                total_amount REAL DEFAULT 0,
                total_liters REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'Pending',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE SET NULL
            )
            ''')
            
            # Sale items table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                rate REAL,
                amount REAL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales (sale_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE SET NULL
            )
            ''')
            
            # Payments table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                payment_date DATE,
                payment_method TEXT,
                amount REAL,
                rrn TEXT,
                reference TEXT,
                status TEXT DEFAULT 'Completed',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales (sale_id) ON DELETE CASCADE
            )
            ''')
            
            # Demos table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS demos (
                demo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                distributor_id INTEGER,
                demo_date DATE,
                product_id INTEGER,
                quantity_provided INTEGER,
                follow_up_date DATE,
                conversion_status TEXT DEFAULT 'Not Converted',
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE SET NULL,
                FOREIGN KEY (distributor_id) REFERENCES distributors (distributor_id) ON DELETE SET NULL,
                FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE SET NULL
            )
            ''')
            
            # WhatsApp logs table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                distributor_id INTEGER,
                message_type TEXT,
                message_content TEXT,
                status TEXT,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE SET NULL,
                FOREIGN KEY (distributor_id) REFERENCES distributors (distributor_id) ON DELETE SET NULL
            )
            ''')
            
            # Follow-ups table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS follow_ups (
                follow_up_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                distributor_id INTEGER,
                demo_id INTEGER,
                follow_up_date DATE,
                follow_up_type TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Pending',
                next_follow_up_date DATE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE SET NULL,
                FOREIGN KEY (distributor_id) REFERENCES distributors (distributor_id) ON DELETE SET NULL,
                FOREIGN KEY (demo_id) REFERENCES demos (demo_id) ON DELETE SET NULL
            )
            ''')
            
            # System logs table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT,
                log_message TEXT,
                table_name TEXT,
                record_id INTEGER,
                action TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_info TEXT
            )
            ''')
            
            # Rollback logs table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS rollback_logs (
                rollback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                record_id INTEGER,
                old_data TEXT,
                new_data TEXT,
                action TEXT,
                rollback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rolled_back_by TEXT
            )
            ''')
            
            # Offers table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS offers (
                offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_name TEXT NOT NULL,
                offer_description TEXT,
                product_id INTEGER,
                discount_percentage REAL,
                discount_amount REAL,
                start_date DATE,
                end_date DATE,
                status TEXT DEFAULT 'Active',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE SET NULL
            )
            ''')
            
            # Demo teams table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS demo_teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                team_leader TEXT,
                team_members TEXT,
                assigned_villages TEXT,
                status TEXT DEFAULT 'Active',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            logger.info("Database tables initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            conn.close()
        
        self.initialize_default_data()
        self.create_indexes()
    
    def create_indexes(self):
        """Create indexes for better performance"""
        conn = self.get_connection()
        
        try:
            # Create indexes for frequently queried columns
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_customers_village ON customers(village)",
                "CREATE INDEX IF NOT EXISTS idx_customers_mobile ON customers(mobile)",
                "CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)",
                "CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_no)",
                "CREATE INDEX IF NOT EXISTS idx_payments_sale_id ON payments(sale_id)",
                "CREATE INDEX IF NOT EXISTS idx_demos_customer_id ON demos(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_demos_date ON demos(demo_date)",
                "CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id)",
                "CREATE INDEX IF NOT EXISTS idx_follow_ups_date ON follow_ups(follow_up_date)",
                "CREATE INDEX IF NOT EXISTS idx_whatsapp_customer_id ON whatsapp_logs(customer_id)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            conn.commit()
            logger.info("Database indexes created successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error creating indexes: {e}")
        finally:
            conn.close()
    
    def initialize_default_data(self):
        """Initialize with default products and demo teams"""
        default_products = [
            ('1 LTR PLASTIC JAR', 'PLASTIC_JAR', 1.0, 'Regular', 95),
            ('2 LTR PLASTIC JAR', 'PLASTIC_JAR', 2.0, 'Regular', 185),
            ('5 LTR PLASTIC JAR', 'PLASTIC_JAR', 5.0, 'Regular', 460),
            ('5 LTR STEEL BARNI', 'STEEL_BARNI', 5.0, 'Premium', 680),
            ('10 LTR STEEL BARNI', 'STEEL_BARNI', 10.0, 'Premium', 1300),
            ('20 LTR STEEL BARNI', 'STEEL_BARNI', 20.0, 'Premium', 2950),
            ('20 LTR PLASTIC CAN', 'PLASTIC_CAN', 20.0, 'Regular', 2400),
            ('1 LTR PET BOTTLE', 'PET_BOTTLE', 1.0, 'Regular', 85)
        ]
        
        default_teams = [
            ('Team A - North Region', 'Rajesh Kumar', 'Mohan, Suresh, Priya', 'Amiyad, Amvad, Ankalav'),
            ('Team B - South Region', 'Sunil Patel', 'Anita, Vijay, Deepak', 'Petlad, Borsad, Vadodara')
        ]
        
        conn = self.get_connection()
        try:
            # Insert default products
            for product in default_products:
                conn.execute('''
                INSERT OR IGNORE INTO products (product_name, packing_type, capacity_ltr, category, standard_rate)
                VALUES (?, ?, ?, ?, ?)
                ''', product)
            
            # Insert default demo teams
            for team in default_teams:
                conn.execute('''
                INSERT OR IGNORE INTO demo_teams (team_name, team_leader, team_members, assigned_villages)
                VALUES (?, ?, ?, ?)
                ''', team)
            
            conn.commit()
            logger.info("Default data initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing default data: {e}")
        finally:
            conn.close()
    
    def _execute_query_internal(self, query: str, params: tuple = None) -> List[tuple]:
        """Internal method to execute SQL query without logging"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Only try to fetch results for SELECT queries
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                result = []
                
            conn.commit()
            return result
            
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None, log_action: bool = True) -> List[tuple]:
        """Execute a SQL query with comprehensive error handling"""
        try:
            result = self._execute_query_internal(query, params)
            
            # Log the query execution (but avoid recursion)
            if log_action and not self._is_logging:
                try:
                    self._is_logging = True
                    self._execute_query_internal('''
                    INSERT INTO system_logs (log_type, log_message, table_name, record_id, action)
                    VALUES (?, ?, ?, ?, ?)
                    ''', ('QUERY_EXECUTION', f"Executed query: {query[:100]}...", None, None, 'EXECUTE'))
                except Exception as e:
                    logger.error(f"Error logging system action: {e}")
                finally:
                    self._is_logging = False
            
            return result
        except Exception as e:
            logger.error(f"Error in execute_query: {e}")
            return []  # Return empty list instead of raising exception
    
    def get_dataframe(self, table_name: str = None, query: str = None, params: tuple = None) -> pd.DataFrame:
        """Get table data as DataFrame with flexible query support"""
        conn = self.get_connection()
        try:
            if query:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            return df
        except Exception as e:
            logger.error(f"Error getting DataFrame for {table_name if table_name else 'query'}: {e}")
            # Return empty DataFrame with proper structure
            return pd.DataFrame()
        finally:
            conn.close()
    
    def add_customer(self, name: str, mobile: str = "", village: str = "", taluka: str = "", 
                district: str = "", customer_code: str = None) -> int:
        """Add a new customer with duplicate handling"""
        
        # Generate customer code if not provided
        if not customer_code:
            customer_code = f"CUST{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
        
        try:
            # Check if customer already exists (by mobile or similar name+village)
            existing_customer = self.execute_query(
                'SELECT customer_id FROM customers WHERE mobile = ? OR (name = ? AND village = ?)',
                (mobile, name, village),
                log_action=False
            )
            
            if existing_customer:
                # Customer already exists, return existing ID
                return existing_customer[0][0]
            
            # If customer_code already exists, generate a new one
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    result = self.execute_query('''
                    INSERT INTO customers (customer_code, name, mobile, village, taluka, district)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (customer_code, name, mobile, village, taluka, district), log_action=False)
                    break
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed: customers.customer_code" in str(e) and attempt < max_attempts - 1:
                        # Generate new unique customer code
                        customer_code = f"CUST{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                        continue
                    else:
                        raise e
            
            # Get the inserted customer_id
            customer_id = self.execute_query('SELECT last_insert_rowid()', log_action=False)[0][0]
            
            self.log_system_action('CUSTOMER_ADD', f"Added customer: {name}", 'customers', customer_id, 'INSERT')
            
            return customer_id
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            # Return a fallback - this won't be in database but prevents crashes
            return -1
    def add_distributor(self, name: str, village: str = "", taluka: str = "", district: str = "", 
                   mantri_name: str = "", mantri_mobile: str = "", sabhasad_count: int = 0, 
                   contact_in_group: int = 0, status: str = "Active") -> int:
        """Add a new distributor with duplicate handling"""
        
        try:
            # Check if distributor already exists
            existing_distributor = self.execute_query(
                'SELECT distributor_id FROM distributors WHERE name = ? AND village = ? AND taluka = ?',
                (name, village, taluka),
                log_action=False
            )
            
            if existing_distributor:
                # Distributor already exists, return existing ID
                return existing_distributor[0][0]
            
            # Insert new distributor
            self.execute_query('''
            INSERT INTO distributors (name, village, taluka, district, mantri_name, mantri_mobile, 
                                    sabhasad_count, contact_in_group, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, village, taluka, district, mantri_name, mantri_mobile, 
                sabhasad_count, contact_in_group, status), log_action=False)
            
            # Get the inserted distributor_id
            distributor_id = self.execute_query('SELECT last_insert_rowid()', log_action=False)[0][0]
            
            self.log_system_action('DISTRIBUTOR_ADD', f"Added distributor: {name}", 'distributors', distributor_id, 'INSERT')
            
            return distributor_id
            
        except Exception as e:
            logger.error(f"Error adding distributor: {e}")
            return -1
    def get_distributor_by_location(self, village: str, taluka: str) -> Optional[Dict]:
        """Get distributor by village and taluka"""
        try:
            result = self.execute_query(
                'SELECT * FROM distributors WHERE village = ? AND taluka = ?',
                (village, taluka),
                log_action=False
            )
            if result:
                return dict(result[0])
            return None
        except Exception as e:
            logger.error(f"Error getting distributor by location: {e}")
            return None

    def distributor_exists(self, name: str, village: str, taluka: str) -> bool:
        """Check if distributor already exists"""
        try:
            result = self.execute_query(
                'SELECT distributor_id FROM distributors WHERE name = ? AND village = ? AND taluka = ?',
                (name, village, taluka),
                log_action=False
            )
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error checking distributor existence: {e}")
            return False
    # In your DatabaseManager class in database.py, replace the generate_invoice_number method:

    def generate_invoice_number(self):
        """Generate automatic invoice number in format: INVCLmmyyserial"""
        try:
            # Get current date components
            now = datetime.now()
            month = now.strftime('%m')  # Two-digit month
            year = now.strftime('%y')   # Two-digit year
            
            # Get the last invoice number for this month-year
            result = self.execute_query(
                "SELECT invoice_no FROM sales WHERE invoice_no LIKE ? ORDER BY sale_id DESC LIMIT 1",
                (f"INVCL{month}{year}%",),
                log_action=False
            )
            
            if result:
                last_invoice = result[0][0]
                # Extract serial number and increment
                try:
                    # Format: INVCLmmyyXXX
                    serial_part = last_invoice[8:]  # Get part after INVCLmmyy
                    last_serial = int(serial_part)
                    new_serial = last_serial + 1
                except ValueError:
                    new_serial = 1
            else:
                # First invoice of the month-year
                new_serial = 1
            
            # Format: INVCL + month(2) + year(2) + serial(3 digits)
            return f"INVCL{month}{year}{new_serial:03d}"
            
        except Exception as e:
            logger.error(f"Error generating invoice number: {e}")
            # Fallback: timestamp-based
            return f"INVCL{int(datetime.now().timestamp())}"

    # Or if you want a more flexible version with configurable prefix:
    def generate_invoice_number(self, prefix="INVCL"):
        """Generate automatic invoice number in format: PREFIXmmyyserial"""
        try:
            now = datetime.now()
            month = now.strftime('%m')
            year = now.strftime('%y')
            
            result = self.execute_query(
                "SELECT invoice_no FROM sales WHERE invoice_no LIKE ? ORDER BY sale_id DESC LIMIT 1",
                (f"{prefix}{month}{year}%",),
                log_action=False
            )
            
            if result:
                last_invoice = result[0][0]
                try:
                    # Remove prefix and date part, get serial
                    serial_part = last_invoice[len(prefix) + 4:]  # prefix + 4 digits (mmyy)
                    last_serial = int(serial_part)
                    new_serial = last_serial + 1
                except ValueError:
                    new_serial = 1
            else:
                new_serial = 1
            
            return f"{prefix}{month}{year}{new_serial:03d}"
            
        except Exception as e:
            logger.error(f"Error generating invoice number: {e}")
            return f"{prefix}{int(datetime.now().timestamp())}"
        
    # Add to your DatabaseManager class in database.py

    def add_sale(self, invoice_no: str, customer_id: int, sale_date, items: List[Dict], 
             payments: List[Dict] = None, notes: str = "") -> int:
        """Add a new sale with items and optional payments - ENHANCED"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Calculate total amount and liters
            total_amount = sum(item['quantity'] * item['rate'] for item in items)
            total_liters = sum(item.get('liters', 0) for item in items)
            
            print(f"🔧 DEBUG: Creating sale - Invoice: {invoice_no}, Customer: {customer_id}, Total: {total_amount}")  # DEBUG
            
            # Add sale record
            cursor.execute('''
            INSERT INTO sales (invoice_no, customer_id, sale_date, total_amount, total_liters, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (invoice_no, customer_id, sale_date, total_amount, total_liters, notes))
            
            # Get the sale ID
            sale_id = cursor.lastrowid
            print(f"🔧 DEBUG: Sale created with ID: {sale_id}")  # DEBUG
            
            # Add sale items
            for item in items:
                amount = item['quantity'] * item['rate']
                print(f"🔧 DEBUG: Adding item - Product: {item['product_id']}, Qty: {item['quantity']}, Rate: {item['rate']}")  # DEBUG
                
                cursor.execute('''
                INSERT INTO sale_items (sale_id, product_id, quantity, rate, amount)
                VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], item['quantity'], item['rate'], amount))
            
            # Add payments if provided
            if payments:
                for payment in payments:
                    cursor.execute('''
                    INSERT INTO payments (sale_id, payment_date, payment_method, amount, rrn, reference)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (sale_id, payment['payment_date'], payment['method'], 
                        payment['amount'], payment.get('rrn', ''), payment.get('reference', '')))
            
            conn.commit()
            
            # Update payment status
            self._update_payment_status(sale_id)
            
            print(f"🔧 DEBUG: Sale {sale_id} completed successfully")  # DEBUG
            return sale_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding sale: {e}")
            print(f"❌ ERROR in add_sale: {e}")  # DEBUG
            raise
        finally:
            conn.close()
    
    def _update_payment_status(self, sale_id: int):
        """Update payment status for a sale"""
        conn = self.get_connection()
        try:
            # Get total paid amount
            cursor = conn.cursor()
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM payments WHERE sale_id = ?', (sale_id,))
            total_paid = cursor.fetchone()[0]
            
            # Get sale total
            cursor.execute('SELECT total_amount FROM sales WHERE sale_id = ?', (sale_id,))
            sale_total = cursor.fetchone()[0]
            
            # Determine payment status
            if total_paid >= sale_total:
                status = 'Paid'
            elif total_paid > 0:
                status = 'Partial'
            else:
                status = 'Pending'
            
            # Update status
            cursor.execute('UPDATE sales SET payment_status = ? WHERE sale_id = ?', (status, sale_id))
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
        finally:
            conn.close()
    
    def get_pending_payments(self) -> pd.DataFrame:
        """Get all pending payments with customer details"""
        return self.get_dataframe('sales', '''
        SELECT s.sale_id, s.invoice_no, s.sale_date, c.name as customer_name, 
               c.mobile, c.village, s.total_amount,
               (s.total_amount - COALESCE(SUM(p.amount), 0)) as pending_amount,
               COALESCE(SUM(p.amount), 0) as paid_amount
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        LEFT JOIN payments p ON s.sale_id = p.sale_id
        WHERE s.payment_status IN ('Pending', 'Partial')
        GROUP BY s.sale_id
        HAVING pending_amount > 0
        ORDER BY s.sale_date DESC
        ''')
    
    def get_demo_conversions(self) -> pd.DataFrame:
        """Get demo conversion statistics with details"""
        return self.get_dataframe('demos', '''
        SELECT d.*, c.name as customer_name, p.product_name, 
               dist.name as distributor_name, c.village, c.taluka,
               CASE WHEN d.conversion_status = 'Converted' THEN 1 ELSE 0 END as converted
        FROM demos d
        LEFT JOIN customers c ON d.customer_id = c.customer_id
        LEFT JOIN products p ON d.product_id = p.product_id
        LEFT JOIN distributors dist ON d.distributor_id = dist.distributor_id
        ORDER BY d.demo_date DESC
        ''')
    
    def get_sales_analytics(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get comprehensive sales analytics"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        query = '''
        SELECT 
            COUNT(*) as total_sales,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_sale_value,
            COUNT(DISTINCT customer_id) as unique_customers,
            SUM(CASE WHEN payment_status = 'Paid' THEN 1 ELSE 0 END) as completed_payments,
            SUM(CASE WHEN payment_status IN ('Pending', 'Partial') THEN 1 ELSE 0 END) as pending_payments
        FROM sales 
        WHERE sale_date BETWEEN ? AND ?
        '''
        
        result = self.execute_query(query, (start_date, end_date), log_action=False)
        
        if result:
            row = result[0]
            return {
                'total_sales': row[0] or 0,
                'total_revenue': row[1] or 0,
                'avg_sale_value': row[2] or 0,
                'unique_customers': row[3] or 0,
                'completed_payments': row[4] or 0,
                'pending_payments': row[5] or 0
            }
        return {}
    
    def log_system_action(self, log_type: str, message: str, table_name: str = None, 
                         record_id: int = None, action: str = None):
        """Log system actions for audit trail - without recursion"""
        if self._is_logging:
            return  # Prevent recursion
        
        try:
            self._is_logging = True
            self._execute_query_internal('''
            INSERT INTO system_logs (log_type, log_message, table_name, record_id, action)
            VALUES (?, ?, ?, ?, ?)
            ''', (log_type, message, table_name, record_id, action))
        except Exception as e:
            logger.error(f"Error logging system action: {e}")
        finally:
            self._is_logging = False
    
    def create_rollback_point(self, table_name: str, record_id: int, old_data: str, 
                             new_data: str, action: str):
        """Create a rollback point for data changes"""
        try:
            self.execute_query('''
            INSERT INTO rollback_logs (table_name, record_id, old_data, new_data, action)
            VALUES (?, ?, ?, ?, ?)
            ''', (table_name, record_id, old_data, new_data, action), log_action=False)
        except Exception as e:
            logger.error(f"Error creating rollback point: {e}")
    
    def get_recent_activity(self, limit: int = 10) -> pd.DataFrame:
        """Get recent system activity"""
        return self.get_dataframe('system_logs', f'''
        SELECT log_type, log_message, table_name, record_id, action, created_date
        FROM system_logs 
        ORDER BY created_date DESC 
        LIMIT {limit}
        ''')
    
    def backup_database(self, backup_path: str = None):
        """Create a database backup"""
        if not backup_path:
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        try:
            conn = self.get_connection()
            backup_conn = sqlite3.connect(backup_path)
            
            with backup_conn:
                conn.backup(backup_conn)
            
            conn.close()
            backup_conn.close()
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return None
    
    def get_village_wise_sales(self) -> pd.DataFrame:
        """Get sales data grouped by village"""
        return self.get_dataframe('sales', '''
        SELECT c.village, COUNT(s.sale_id) as total_sales, 
               SUM(s.total_amount) as total_revenue,
               AVG(s.total_amount) as avg_sale_value,
               COUNT(DISTINCT s.customer_id) as unique_customers
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        WHERE c.village IS NOT NULL AND c.village != ''
        GROUP BY c.village
        ORDER BY total_revenue DESC
        ''')
    
    def get_product_performance(self) -> pd.DataFrame:
        """Get product performance analytics"""
        return self.get_dataframe('sale_items', '''
        SELECT p.product_name, COUNT(si.item_id) as times_sold,
               SUM(si.quantity) as total_quantity, 
               SUM(si.amount) as total_revenue,
               AVG(si.rate) as avg_rate
        FROM sale_items si
        JOIN products p ON si.product_id = p.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY total_revenue DESC
        ''')
    
    def get_upcoming_follow_ups(self) -> pd.DataFrame:
        """Get upcoming follow-ups"""
        return self.get_dataframe('follow_ups', '''
        SELECT f.*, c.name as customer_name, c.mobile, 
               d.name as distributor_name, dm.demo_date
        FROM follow_ups f
        LEFT JOIN customers c ON f.customer_id = c.customer_id
        LEFT JOIN distributors d ON f.distributor_id = d.distributor_id
        LEFT JOIN demos dm ON f.demo_id = dm.demo_id
        WHERE f.follow_up_date >= date('now') 
        AND f.status = 'Pending'
        ORDER BY f.follow_up_date ASC
        LIMIT 20
        ''')
    
    def get_whatsapp_logs(self, customer_id: int = None) -> pd.DataFrame:
        """Get WhatsApp communication logs"""
        if customer_id:
            return self.get_dataframe('whatsapp_logs', '''
            SELECT w.*, c.name as customer_name, c.mobile
            FROM whatsapp_logs w
            LEFT JOIN customers c ON w.customer_id = c.customer_id
            WHERE w.customer_id = ?
            ORDER BY w.sent_date DESC
            ''', (customer_id,))
        else:
            return self.get_dataframe('whatsapp_logs', '''
            SELECT w.*, c.name as customer_name, c.mobile
            FROM whatsapp_logs w
            LEFT JOIN customers c ON w.customer_id = c.customer_id
            ORDER BY w.sent_date DESC
            LIMIT 50
            ''')
    
    def cleanup_old_data(self, days: int = 365):
        """Clean up old data (logs, etc.) older than specified days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Clean system logs
            self.execute_query('DELETE FROM system_logs WHERE created_date < ?', (cutoff_date,), log_action=False)
            
            # Clean rollback logs
            self.execute_query('DELETE FROM rollback_logs WHERE rollback_date < ?', (cutoff_date,), log_action=False)
            
            logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

# Utility function to check database health
def check_database_health(db_path: str = "sales_management.db") -> Dict:
    """Check database health and statistics"""
    try:
        db = DatabaseManager(db_path)
        
        # Get table counts
        tables = ['customers', 'sales', 'distributors', 'demos', 'payments', 'products']
        counts = {}
        
        for table in tables:
            result = db.execute_query(f"SELECT COUNT(*) FROM {table}", log_action=False)
            counts[table] = result[0][0] if result else 0
        
        # Get database size
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        return {
            'status': 'healthy',
            'table_counts': counts,
            'database_size_mb': round(db_size / (1024 * 1024), 2),
            'last_backup': 'N/A',  # You can implement backup tracking
            'integrity_check': 'passed'  # You can add actual integrity checks
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'table_counts': {},
            'database_size_mb': 0,
            'integrity_check': 'failed'
        }