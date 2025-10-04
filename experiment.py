import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import sqlite3

class RelationalDataStandardizationSystem:
    def __init__(self, data_directory="data", output_directory="standardized_data"):
        self.data_directory = data_directory
        self.output_directory = output_directory
        os.makedirs(output_directory, exist_ok=True)
        
        # Define standardized column names for each entity
        self.standard_columns = {
            'customers': ['customer_id', 'customer_code', 'name', 'mobile', 'village', 'taluka', 'district', 'source_file', 'source_sheet'],
            'products': ['product_id', 'product_name', 'packing_type', 'capacity_ltr', 'category', 'standard_rate'],
            'sales': ['sale_id', 'invoice_no', 'customer_id', 'sale_date', 'dispatch_date', 'total_amount', 
                     'total_liters', 'payment_date', 'gpay_amount', 'cash_amount', 'cheque_amount', 'rrn', 'reference', 'source_file', 'source_sheet'],
            'sale_items': ['item_id', 'sale_id', 'product_id', 'quantity', 'rate', 'amount', 'source_file', 'source_sheet'],
            'distributors': ['distributor_id', 'name', 'village', 'taluka', 'district', 'mantri_name', 
                            'mantri_mobile', 'sabhasad_count', 'contact_in_group', 'total_liters', 'source_file', 'source_sheet']
        }
        
        # Product mapping dictionary
        self.product_mapping = {
            '1 LTR PLASTIC JAR': {'capacity': 1.0, 'type': 'PLASTIC_JAR', 'category': 'Regular', 'rate': 95},
            '2 LTR PLASTIC JAR': {'capacity': 2.0, 'type': 'PLASTIC_JAR', 'category': 'Regular', 'rate': 185},
            '5 LTR PLASTIC JAR': {'capacity': 5.0, 'type': 'PLASTIC_JAR', 'category': 'Regular', 'rate': 460},
            '5 LTR STEEL BARNI': {'capacity': 5.0, 'type': 'STEEL_BARNI', 'category': 'Premium', 'rate': 680},
            '10 LTR STEEL BARNI': {'capacity': 10.0, 'type': 'STEEL_BARNI', 'category': 'Premium', 'rate': 1300},
            '20 LTR STEEL BARNI': {'capacity': 20.0, 'type': 'STEEL_BARNI', 'category': 'Premium', 'rate': 2950},
            '20 LTR PLASTIC CAN': {'capacity': 20.0, 'type': 'PLASTIC_CAN', 'category': 'Regular', 'rate': 2400},
            '1 LTR PET BOTTLE': {'capacity': 1.0, 'type': 'PET_BOTTLE', 'category': 'Regular', 'rate': 85}
        }
        
        # Dictionaries to map names to IDs
        self.customer_name_to_id = {}
        self.product_name_to_id = {}
        self.invoice_to_sale_id = {}

    def process_all_files(self):
        """Process all Excel files in the data directory"""
        print("Starting data standardization process...")
        
        # Initialize empty DataFrames for each entity
        customers_df = pd.DataFrame(columns=self.standard_columns['customers'])
        products_df = pd.DataFrame(columns=self.standard_columns['products'])
        sales_df = pd.DataFrame(columns=self.standard_columns['sales'])
        sale_items_df = pd.DataFrame(columns=self.standard_columns['sale_items'])
        distributors_df = pd.DataFrame(columns=self.standard_columns['distributors'])
        
        # Process each file in the data directory
        for file_name in os.listdir(self.data_directory):
            if file_name.endswith(('.xlsx', '.xls')):
                file_path = os.path.join(self.data_directory, file_name)
                print(f"\nProcessing file: {file_name}")
                
                try:
                    # Read all sheets from the Excel file
                    excel_file = pd.ExcelFile(file_path)
                    print(f"Sheets found: {excel_file.sheet_names}")
                    
                    for sheet_name in excel_file.sheet_names:
                        try:
                            print(f"  Processing sheet: {sheet_name}")
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                            
                            # Display sheet info for debugging
                            print(f"    Shape: {df.shape}")
                            print(f"    Columns: {list(df.columns)}")
                            if not df.empty and len(df) > 0:
                                print(f"    First row sample: {dict(df.iloc[0])}")
                            
                            # Identify sheet type and process accordingly
                            sheet_type = self.identify_sheet_type(df, sheet_name)
                            print(f"    Identified as: {sheet_type}")
                            
                            if sheet_type == 'sales':
                                sales_data, items_data = self.process_sales_data(df, file_name, sheet_name)
                                if not sales_data.empty:
                                    sales_df = pd.concat([sales_df, sales_data], ignore_index=True)
                                if not items_data.empty:
                                    sale_items_df = pd.concat([sale_items_df, items_data], ignore_index=True)
                                    
                            elif sheet_type == 'customers':
                                customer_data = self.process_customer_data(df, file_name, sheet_name)
                                if not customer_data.empty:
                                    customers_df = pd.concat([customers_df, customer_data], ignore_index=True)
                                    # Update customer mapping
                                    for _, row in customer_data.iterrows():
                                        self.customer_name_to_id[row['name']] = row['customer_id']
                                    
                            elif sheet_type == 'distributors':
                                distributor_data = self.process_distributor_data(df, file_name, sheet_name)
                                if not distributor_data.empty:
                                    distributors_df = pd.concat([distributors_df, distributor_data], ignore_index=True)
                                    
                            elif sheet_type == 'unknown':
                                print(f"    Could not identify sheet type: {sheet_name}")
                                
                        except Exception as e:
                            print(f"    Error processing sheet {sheet_name}: {str(e)}")
                            continue
                
                except Exception as e:
                    print(f"Error processing {file_name}: {str(e)}")
        
        # Create products DataFrame from mapping
        products_df = self.create_products_dataframe()
        # Update product mapping
        for _, row in products_df.iterrows():
            self.product_name_to_id[row['product_name']] = row['product_id']
        
        # Add IDs to all DataFrames
        customers_df = self.add_ids(customers_df, 'customer_id')
        sales_df = self.add_ids(sales_df, 'sale_id')
        sale_items_df = self.add_ids(sale_items_df, 'item_id')
        distributors_df = self.add_ids(distributors_df, 'distributor_id')
        
        # Update sales mapping for foreign key relationships
        for _, row in sales_df.iterrows():
            self.invoice_to_sale_id[row['invoice_no']] = row['sale_id']
        
        # Now establish foreign key relationships
        sales_df, sale_items_df, customers_df = self.establish_relationships(sales_df, sale_items_df, customers_df)
        
        # Save all DataFrames to Excel files
        self.save_dataframes({
            'customers': customers_df,
            'products': products_df,
            'sales': sales_df,
            'sale_items': sale_items_df,
            'distributors': distributors_df
        })
        
        # Create SQLite database with proper relationships
        self.create_relational_database(customers_df, products_df, sales_df, sale_items_df, distributors_df)
        
        print("\nData standardization completed successfully!")
        print(f"Customers: {len(customers_df)} records")
        print(f"Products: {len(products_df)} records")
        print(f"Sales: {len(sales_df)} records")
        print(f"Sale Items: {len(sale_items_df)} records")
        print(f"Distributors: {len(distributors_df)} records")
        
        return customers_df, products_df, sales_df, sale_items_df, distributors_df

    def establish_relationships(self, sales_df, sale_items_df, customers_df):
        """Establish foreign key relationships between tables"""
        print("\nEstablishing foreign key relationships...")
        
        # 1. Link sales to customers
        print("Linking sales to customers...")
        customer_name_to_id_map = dict(zip(customers_df['name'], customers_df['customer_id']))
        new_customers = []
        
        for idx, row in sales_df.iterrows():
            customer_name = row.get('customer_name', '')
            if customer_name in customer_name_to_id_map:
                sales_df.at[idx, 'customer_id'] = customer_name_to_id_map[customer_name]
            else:
                # Create a new customer if not found
                new_customer_id = len(customers_df) + len(new_customers) + 1
                sales_df.at[idx, 'customer_id'] = new_customer_id
                # Add to new customers list
                new_customer = {
                    'customer_id': new_customer_id,
                    'customer_code': f"CUST{new_customer_id:04d}",
                    'name': customer_name,
                    'village': row.get('village', ''),
                    'taluka': row.get('taluka', ''),
                    'district': row.get('district', ''),
                    'source_file': row.get('source_file', ''),
                    'source_sheet': row.get('source_sheet', '')
                }
                new_customers.append(new_customer)
                customer_name_to_id_map[customer_name] = new_customer_id
        
        # Add new customers to the customers dataframe using concat instead of append
        if new_customers:
            new_customers_df = pd.DataFrame(new_customers)
            customers_df = pd.concat([customers_df, new_customers_df], ignore_index=True)
        
        # 2. Link sale items to sales and products
        print("Linking sale items to sales and products...")
        invoice_to_sale_id_map = dict(zip(sales_df['invoice_no'], sales_df['sale_id']))
        
        for idx, row in sale_items_df.iterrows():
            invoice_no = row.get('invoice_no', '')
            product_name = row.get('product_name', '')
            
            # Link to sale
            if invoice_no in invoice_to_sale_id_map:
                sale_items_df.at[idx, 'sale_id'] = invoice_to_sale_id_map[invoice_no]
            
            # Link to product
            if product_name in self.product_name_to_id:
                sale_items_df.at[idx, 'product_id'] = self.product_name_to_id[product_name]
        
        return sales_df, sale_items_df, customers_df

    def identify_sheet_type(self, df, sheet_name):
        """Identify the type of data in the sheet"""
        if df.empty:
            return 'empty'
        
        # Convert all column names to strings and uppercase for comparison
        columns_upper = [str(col).upper() for col in df.columns]
        columns_str = ' '.join(columns_upper)
        
        # Check for sales data
        sales_keywords = ['INV', 'DISPATCH', 'QTN', 'RATE', 'AMT', 'FINAL AMT', 'PAYMENT', 'G-PAY', 'CASH', 'CHQ']
        if any(keyword in columns_str for keyword in sales_keywords):
            return 'sales'
        
        # Check for customer data
        customer_keywords = ['NAME', 'MOBILE', 'VILLAGE', 'TALUKA', 'DISTRICT', 'MEMBER', 'CODE']
        if any(keyword in columns_str for keyword in customer_keywords):
            return 'customers'
        
        # Check for distributor data
        distributor_keywords = ['MANTRI', 'SABHASAD', 'CONTACT', 'GROUP', 'TOTAL', 'LTR', 'VILLAGE', 'TALUKA']
        if any(keyword in columns_str for keyword in distributor_keywords):
            return 'distributors'
        
        return 'unknown'

    def process_sales_data(self, df, file_name, sheet_name):
        """Process sales data from a sheet"""
        sales_data = []
        items_data = []
        
        current_invoice = None
        current_customer = None
        current_village = None
        current_taluka = None
        current_district = None
        sale_counter = 0
        
        # Convert all column names to strings
        df.columns = [str(col) for col in df.columns]
        
        for idx, row in df.iterrows():
            # Skip empty rows
            if all(pd.isna(cell) for cell in row):
                continue
                
            # Check if this is a new sales record (has SR NO. or similar)
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip().isdigit():
                sale_counter += 1
                
                # Try to find invoice number
                invoice_no = None
                for i, col in enumerate(df.columns):
                    if 'INV' in col.upper() and pd.notna(row.iloc[i]):
                        invoice_no = row.iloc[i]
                        break
                
                if not invoice_no:
                    invoice_no = f"INV_{file_name}_{sheet_name}_{sale_counter}"
                
                current_invoice = invoice_no
                
                # Try to find customer name
                customer_name = "Unknown Customer"
                for i, col in enumerate(df.columns):
                    if 'NAME' in col.upper() and pd.notna(row.iloc[i]):
                        customer_name = row.iloc[i]
                        break
                
                current_customer = customer_name
                
                # Try to find location information
                for i, col in enumerate(df.columns):
                    col_upper = col.upper()
                    if 'VILLAGE' in col_upper and pd.notna(row.iloc[i]):
                        current_village = row.iloc[i]
                    elif 'TALUKA' in col_upper and pd.notna(row.iloc[i]):
                        current_taluka = row.iloc[i]
                    elif 'DISTRICT' in col_upper and pd.notna(row.iloc[i]):
                        current_district = row.iloc[i]
                
                # Create sales record
                sales_record = {
                    'invoice_no': current_invoice,
                    'customer_name': current_customer,
                    'village': current_village,
                    'taluka': current_taluka,
                    'district': current_district,
                    'sale_date': None,
                    'dispatch_date': None,
                    'total_amount': 0,
                    'total_liters': 0,
                    'payment_date': None,
                    'gpay_amount': 0,
                    'cash_amount': 0,
                    'cheque_amount': 0,
                    'rrn': None,
                    'reference': None,
                    'source_file': file_name,
                    'source_sheet': sheet_name
                }
                
                # Try to extract dates and amounts
                for i, col in enumerate(df.columns):
                    col_upper = col.upper()
                    if 'DATE' in col_upper and pd.notna(row.iloc[i]):
                        if 'DISPATCH' in col_upper:
                            sales_record['dispatch_date'] = row.iloc[i]
                        elif 'PAYMENT' in col_upper:
                            sales_record['payment_date'] = row.iloc[i]
                        else:
                            sales_record['sale_date'] = row.iloc[i]
                    
                    if 'AMT' in col_upper and pd.notna(row.iloc[i]) and 'FINAL' in col_upper:
                        sales_record['total_amount'] = row.iloc[i]
                    
                    if 'LTR' in col_upper and pd.notna(row.iloc[i]) and 'TOTAL' in col_upper:
                        sales_record['total_liters'] = row.iloc[i]
                    
                    if 'G-PAY' in col_upper and pd.notna(row.iloc[i]):
                        sales_record['gpay_amount'] = row.iloc[i]
                    
                    if 'CASH' in col_upper and pd.notna(row.iloc[i]):
                        sales_record['cash_amount'] = row.iloc[i]
                    
                    if 'CHQ' in col_upper and pd.notna(row.iloc[i]):
                        sales_record['cheque_amount'] = row.iloc[i]
                    
                    if 'REF' in col_upper and pd.notna(row.iloc[i]):
                        sales_record['reference'] = row.iloc[i]
                
                sales_data.append(sales_record)
            
            # Process product items (look for packing information)
            packing_col = None
            for i, col in enumerate(df.columns):
                if 'PACKING' in col.upper() and pd.notna(row.iloc[i]):
                    packing_col = i
                    break
            
            if packing_col is not None and pd.notna(row.iloc[packing_col]):
                packing = str(row.iloc[packing_col])
                product_info = self.get_product_info(packing)
                
                if product_info:
                    # Find quantity and rate
                    quantity = 0
                    rate = product_info['rate']
                    amount = 0
                    
                    for i, col in enumerate(df.columns):
                        col_upper = col.upper()
                        if ('QTY' in col_upper or 'QTN' in col_upper) and pd.notna(row.iloc[i]):
                            quantity = row.iloc[i]
                        elif 'RATE' in col_upper and pd.notna(row.iloc[i]):
                            rate = row.iloc[i]
                        elif 'AMT' in col_upper and pd.notna(row.iloc[i]) and 'FINAL' not in col_upper:
                            amount = row.iloc[i]
                    
                    if quantity == 0 and amount > 0 and rate > 0:
                        quantity = amount / rate
                    
                    item_record = {
                        'invoice_no': current_invoice,
                        'product_name': packing,
                        'quantity': quantity,
                        'rate': rate,
                        'amount': amount if amount > 0 else quantity * rate,
                        'source_file': file_name,
                        'source_sheet': sheet_name
                    }
                    items_data.append(item_record)
        
        return pd.DataFrame(sales_data), pd.DataFrame(items_data)

    def process_customer_data(self, df, file_name, sheet_name):
        """Process customer data from a sheet"""
        customer_data = []
        
        # Convert all column names to strings
        df.columns = [str(col) for col in df.columns]
        
        for idx, row in df.iterrows():
            # Skip empty rows and header rows
            if pd.isna(row.iloc[0]) or any('CODE' in str(col).upper() for col in df.columns if str(row.iloc[0]) in str(col)):
                continue
            
            customer_record = {
                'customer_code': '',
                'name': '',
                'mobile': '',
                'village': '',
                'taluka': '',
                'district': '',
                'source_file': file_name,
                'source_sheet': sheet_name
            }
            
            # Map columns to customer fields
            for i, col in enumerate(df.columns):
                col_upper = str(col).upper()
                if 'CODE' in col_upper and pd.notna(row.iloc[i]):
                    customer_record['customer_code'] = str(row.iloc[i]).strip().zfill(4)
                elif 'NAME' in col_upper and pd.notna(row.iloc[i]):
                    customer_record['name'] = row.iloc[i]
                elif 'MOBILE' in col_upper and pd.notna(row.iloc[i]):
                    customer_record['mobile'] = row.iloc[i]
                elif 'VILLAGE' in col_upper and pd.notna(row.iloc[i]):
                    customer_record['village'] = row.iloc[i]
                elif 'TALUKA' in col_upper and pd.notna(row.iloc[i]):
                    customer_record['taluka'] = row.iloc[i]
                elif 'DISTRICT' in col_upper and pd.notna(row.iloc[i]):
                    customer_record['district'] = row.iloc[i]
            
            # Only add if we have at least a name or code
            if customer_record['name'] or customer_record['customer_code']:
                customer_data.append(customer_record)
        
        return pd.DataFrame(customer_data)

    def process_distributor_data(self, df, file_name, sheet_name):
        """Process distributor data from a sheet"""
        distributor_data = []
        
        # Convert all column names to strings
        df.columns = [str(col) for col in df.columns]
        
        for idx, row in df.iterrows():
            # Skip empty rows and header rows
            if pd.isna(row.iloc[0]) or any('NAME' in str(col).upper() for col in df.columns if str(row.iloc[0]) in str(col)):
                continue
            
            distributor_record = {
                'name': '',
                'village': '',
                'taluka': '',
                'district': '',
                'mantri_name': '',
                'mantri_mobile': '',
                'sabhasad_count': 0,
                'contact_in_group': 0,
                'total_liters': 0,
                'source_file': file_name,
                'source_sheet': sheet_name
            }
            
            # Map columns to distributor fields
            for i, col in enumerate(df.columns):
                col_upper = str(col).upper()
                if 'NAME' in col_upper and pd.notna(row.iloc[i]):
                    if 'MANTRI' in col_upper:
                        distributor_record['mantri_name'] = row.iloc[i]
                    else:
                        distributor_record['name'] = row.iloc[i]
                elif 'VILLAGE' in col_upper and pd.notna(row.iloc[i]):
                    distributor_record['village'] = row.iloc[i]
                elif 'TALUKA' in col_upper and pd.notna(row.iloc[i]):
                    distributor_record['taluka'] = row.iloc[i]
                elif 'DISTRICT' in col_upper and pd.notna(row.iloc[i]):
                    distributor_record['district'] = row.iloc[i]
                elif 'MOBILE' in col_upper and pd.notna(row.iloc[i]):
                    distributor_record['mantri_mobile'] = row.iloc[i]
                elif 'SABHASAD' in col_upper and pd.notna(row.iloc[i]):
                    distributor_record['sabhasad_count'] = row.iloc[i]
                elif 'CONTACT' in col_upper and pd.notna(row.iloc[i]):
                    distributor_record['contact_in_group'] = row.iloc[i]
                elif 'LTR' in col_upper and pd.notna(row.iloc[i]):
                    distributor_record['total_liters'] = row.iloc[i]
            
            # Only add if we have at least a name
            if distributor_record['name'] or distributor_record['mantri_name']:
                distributor_data.append(distributor_record)
        
        return pd.DataFrame(distributor_data)

    def get_product_info(self, packing_text):
        """Get product information from packing description"""
        if not isinstance(packing_text, str):
            return None
            
        for product_name, product_info in self.product_mapping.items():
            if product_name.upper() in packing_text.upper():
                return {
                    'product_id': f"PROD_{list(self.product_mapping.keys()).index(product_name)}",
                    'rate': product_info['rate']
                }
        return None

    def create_products_dataframe(self):
        """Create products DataFrame from the product mapping"""
        products_data = []
        
        for i, (product_name, product_info) in enumerate(self.product_mapping.items()):
            product_record = {
                'product_id': f"PROD_{i}",
                'product_name': product_name,
                'packing_type': product_info['type'],
                'capacity_ltr': product_info['capacity'],
                'category': product_info['category'],
                'standard_rate': product_info['rate']
            }
            products_data.append(product_record)
        
        return pd.DataFrame(products_data)

    def add_ids(self, df, id_column):
        """Add ID column to DataFrame"""
        if not df.empty and id_column not in df.columns:
            df[id_column] = range(1, len(df) + 1)
        return df

    def save_dataframes(self, dataframes):
        """Save all DataFrames to Excel files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for name, df in dataframes.items():
            if not df.empty:
                filename = f"{name}_{timestamp}.xlsx"
                filepath = os.path.join(self.output_directory, filename)
                df.to_excel(filepath, index=False)
                print(f"Saved {len(df)} records to {filename}")

    def create_relational_database(self, customers_df, products_df, sales_df, sale_items_df, distributors_df):
        """Create SQLite database with proper foreign key relationships"""
        db_path = os.path.join(self.output_directory, "sales_management.db")
        conn = sqlite3.connect(db_path)
        
        # Create tables with foreign key constraints
        conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            customer_code TEXT,
            name TEXT NOT NULL,
            mobile TEXT,
            village TEXT,
            taluka TEXT,
            district TEXT,
            source_file TEXT,
            source_sheet TEXT
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            packing_type TEXT,
            capacity_ltr REAL,
            category TEXT,
            standard_rate REAL
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY,
            invoice_no TEXT UNIQUE,
            customer_id INTEGER,
            sale_date TEXT,
            dispatch_date TEXT,
            total_amount REAL,
            total_liters REAL,
            payment_date TEXT,
            gpay_amount REAL,
            cash_amount REAL,
            cheque_amount REAL,
            rrn TEXT,
            reference TEXT,
            source_file TEXT,
            source_sheet TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            item_id INTEGER PRIMARY KEY,
            sale_id INTEGER,
            product_id TEXT,
            quantity REAL,
            rate REAL,
            amount REAL,
            source_file TEXT,
            source_sheet TEXT,
            FOREIGN KEY (sale_id) REFERENCES sales (sale_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS distributors (
            distributor_id INTEGER PRIMARY KEY,
            name TEXT,
            village TEXT,
            taluka TEXT,
            district TEXT,
            mantri_name TEXT,
            mantri_mobile TEXT,
            sabhasad_count INTEGER,
            contact_in_group INTEGER,
            total_liters REAL,
            source_file TEXT,
            source_sheet TEXT
        )
        ''')
        
        # Insert data
        customers_df.to_sql('customers', conn, if_exists='replace', index=False)
        products_df.to_sql('products', conn, if_exists='replace', index=False)
        sales_df.to_sql('sales', conn, if_exists='replace', index=False)
        sale_items_df.to_sql('sale_items', conn, if_exists='replace', index=False)
        distributors_df.to_sql('distributors', conn, if_exists='replace', index=False)
        
        conn.close()
        print(f"Created relational database: {db_path}")

# Main execution
if __name__ == "__main__":
    # Initialize the system
    system = RelationalDataStandardizationSystem(data_directory="data", output_directory="standardized_data")
    
    # Process all files
    customers_df, products_df, sales_df, sale_items_df, distributors_df = system.process_all_files()
    
    print("\nProcess completed! Check the 'standardized_data' folder for output files.")