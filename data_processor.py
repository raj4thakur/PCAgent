import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
        self.product_mapping = self._create_product_mapping()
    
    def _create_product_mapping(self):
        """Create product mapping from database"""
        try:
            products_df = self.db.get_dataframe('products')
            return {row['product_name'].upper(): row['product_id'] for _, row in products_df.iterrows()}
        except Exception as e:
            logger.error(f"Error creating product mapping: {e}")
            return {}
    
    def process_excel_file(self, file_path):
        """Enhanced file processing with all data types"""
        try:
            file_name = os.path.basename(file_path)
            print(f"🚀 Processing file: {file_name}")
            
            excel_file = pd.ExcelFile(file_path)
            processed_sheets = 0
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df_clean = self._clean_dataframe(df)
                
                print(f"\n📊 Sheet: {sheet_name}")
                print(f"   Columns: {df_clean.columns.tolist()}")
                
                # Check all types with priority
                is_payment = self._is_payment_sheet(df_clean)
                is_sales = self._is_sales_sheet(df_clean)
                is_customer = self._is_customer_sheet(df_clean)
                is_distributor = self._is_distributor_sheet(df_clean)
                
                print(f"   Detection - Payment: {is_payment}, Sales: {is_sales}, Customer: {is_customer}, Distributor: {is_distributor}")
                
                processed = False
                if is_payment:
                    processed = self.process_payment_sheet(df_clean, file_name, sheet_name)
                elif is_sales:
                    processed = self.process_sales_sheet(df_clean, file_name, sheet_name)
                elif is_distributor:
                    processed = self.process_distributor_sheet(df_clean, file_name, sheet_name)
                elif is_customer:
                    processed = self.process_customer_sheet(df_clean, file_name, sheet_name)
                
                if processed:
                    processed_sheets += 1
                    print(f"   ✅ Successfully processed as detected type")
                else:
                    print(f"   ❌ Failed to process")
            
            print(f"\n🎉 File processing complete: {processed_sheets}/{len(excel_file.sheet_names)} sheets processed")
            return processed_sheets > 0
            
        except Exception as e:
            print(f"💥 Error processing file {file_path}: {e}")
            return False
    
    def _clean_dataframe(self, df):
        """Clean and prepare dataframe for processing"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Convert column names to string and clean them
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        return df
    
    def _is_sales_sheet(self, df):
        """Check if sheet contains sales data"""
        required_columns = ['INVOICE', 'CUSTOMER', 'PRODUCT', 'QUANTITY', 'AMOUNT']
        existing_columns = [col for col in df.columns if any(req in col for req in required_columns)]
        return len(existing_columns) >= 3
    
    def _is_customer_sheet(self, df):
        """Check if sheet contains customer data"""
        required_columns = ['CUSTOMER', 'NAME', 'MOBILE', 'VILLAGE']
        existing_columns = [col for col in df.columns if any(req in col for req in required_columns)]
        return len(existing_columns) >= 2
    
    def _is_distributor_sheet(self, df):
        """Check if sheet contains distributor data"""
        required_columns = ['DISTRIBUTOR', 'MANTRI', 'SABHASAD']
        existing_columns = [col for col in df.columns if any(req in col for req in required_columns)]
        return len(existing_columns) >= 2
    
    def process_sales_sheet(self, df, file_name, sheet_name):
        """Process sales data from sheet"""
        try:
            processed_rows = 0
            
            for index, row in df.iterrows():
                try:
                    # Skip header rows and empty rows
                    if self._is_header_row(row) or pd.isna(row.iloc[0]):
                        continue
                    
                    # Extract sales data (adjust column indices based on your Excel structure)
                    invoice_no = str(row.iloc[0]) if len(row) > 0 else f"INV_{datetime.now().strftime('%Y%m%d%H%M%S')}_{index}"
                    customer_name = str(row.iloc[1]) if len(row) > 1 else "Unknown Customer"
                    product_name = str(row.iloc[2]) if len(row) > 2 else "Unknown Product"
                    quantity = self._safe_float(row.iloc[3]) if len(row) > 3 else 0
                    amount = self._safe_float(row.iloc[4]) if len(row) > 4 else 0
                    
                    # Get or create customer
                    customer_id = self._get_or_create_customer(customer_name, "", "", "", "")
                    
                    # Get product ID
                    product_id = self._get_product_id(product_name)
                    
                    if customer_id and product_id and quantity > 0:
                        # Create sale
                        sale_date = datetime.now().date()
                        sale_items = [{
                            'product_id': product_id,
                            'quantity': quantity,
                            'rate': amount / quantity if quantity > 0 else 0
                        }]
                        
                        self.db.add_sale(invoice_no, customer_id, sale_date, sale_items)
                        processed_rows += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing row {index} in sales sheet: {e}")
                    continue
            
            logger.info(f"Processed {processed_rows} sales from {sheet_name}")
            return processed_rows > 0
            
        except Exception as e:
            logger.error(f"Error processing sales sheet: {e}")
            return False
    
    def process_customer_sheet(self, df, file_name, sheet_name):
        """Process customer data from sheet with duplicate handling"""
        try:
            processed_rows = 0
            duplicate_rows = 0
            error_rows = 0
            
            print(f"🔄 Processing customer sheet: {sheet_name} with {len(df)} rows")
            
            for index, row in df.iterrows():
                try:
                    # Skip header rows and empty rows
                    if self._is_header_row(row) or pd.isna(row.iloc[0]):
                        continue
                    
                    # Extract customer data
                    customer_code = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else None
                    name = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else "Unknown"
                    mobile = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                    
                    # Extract location - adjust indices based on your Excel structure
                    village = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                    taluka = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                    district = str(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else ""
                    
                    # If village is combined with name, split them
                    if not village and "(" in name:
                        name_parts = name.split("(")
                        if len(name_parts) > 1:
                            name = name_parts[0].strip()
                            village = name_parts[1].replace(")", "").strip()
                    
                    # Skip if no name
                    if not name or name == "Unknown":
                        continue
                    
                    # Add customer to database (method now handles duplicates)
                    customer_id = self.db.add_customer(name, mobile, village, taluka, district, customer_code)
                    
                    if customer_id and customer_id != -1:
                        processed_rows += 1
                        if processed_rows % 50 == 0:  # Progress update
                            print(f"📊 Processed {processed_rows} customers...")
                    else:
                        duplicate_rows += 1
                        
                except Exception as e:
                    error_rows += 1
                    if error_rows <= 5:  # Only log first few errors
                        print(f"❌ Error in row {index}: {e}")
                    continue
            
            print(f"🎉 Customer processing complete: {processed_rows} added, {duplicate_rows} duplicates, {error_rows} errors")
            return processed_rows > 0
            
        except Exception as e:
            print(f"💥 Error processing customer sheet: {e}")
            return False
    
    def process_distributor_sheet(self, df, file_name, sheet_name):
        """Process distributor data from sheet"""
        try:
            processed_rows = 0
            
            # Clean the dataframe - convert column names to consistent format
            df.columns = [str(col).strip().upper() for col in df.columns]
            print(f"DEBUG: Processing distributor sheet with columns: {df.columns.tolist()}")
            
            for index, row in df.iterrows():
                try:
                    # Skip header rows and empty rows
                    if self._is_header_row(row) or pd.isna(row.iloc[0]):
                        print(f"DEBUG: Skipping row {index} - header or empty")
                        continue
                    
                    print(f"DEBUG: Processing row {index}")
                    
                    # Extract distributor data based on YOUR ACTUAL COLUMNS
                    # Map your Excel columns to database fields
                    name = self._extract_distributor_name(row)  # We'll use Village + Taluka as name
                    village = self._safe_get(row, 'Village', 1)
                    taluka = self._safe_get(row, 'Taluka', 2) 
                    district = self._safe_get(row, 'District', 3)
                    mantri_name = self._safe_get(row, 'Mantri_Name', 4)
                    mantri_mobile = self._safe_get(row, 'Mantri_Mobile', 5)
                    sabhasad_count = self._safe_get_int(row, 'Sabhasad', 6)
                    contact_in_group = self._safe_get_int(row, 'Contact_In_Group', 7)
                    
                    print(f"DEBUG: Extracted - Village: {village}, Taluka: {taluka}, Mantri: {mantri_name}")
                    
                    # Validate we have essential data
                    if not village or not taluka:
                        print(f"DEBUG: Skipping - missing village or taluka")
                        continue
                    
                    # Create distributor name from village + taluka
                    if not name:
                        name = f"{village} - {taluka}"
                    
                    # Add distributor to database with ALL fields
                    self.db.execute_query('''
                    INSERT OR REPLACE INTO distributors 
                    (name, village, taluka, district, mantri_name, mantri_mobile, sabhasad_count, contact_in_group)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, village, taluka, district, mantri_name, mantri_mobile, sabhasad_count, contact_in_group))
                    
                    processed_rows += 1
                    print(f"DEBUG: Successfully added distributor: {name}")
                    
                except Exception as e:
                    logger.warning(f"Error processing row {index} in distributor sheet: {e}")
                    continue
            
            logger.info(f"Processed {processed_rows} distributors from {sheet_name}")
            return processed_rows > 0
            
        except Exception as e:
            logger.error(f"Error processing distributor sheet: {e}")
            return False

    def _extract_distributor_name(self, row):
        """Extract distributor name from village and taluka"""
        village = self._safe_get(row, 'Village', 1)
        taluka = self._safe_get(row, 'Taluka', 2)
        
        if village and taluka:
            return f"{village} - {taluka}"
        elif village:
            return village
        elif taluka:
            return taluka
        else:
            return "Unknown Distributor"

    def _safe_get(self, row, column_name, default_index):
        """Safely get value from row by column name or index"""
        try:
            # Try by column name first
            if column_name in row.index:
                value = row[column_name]
                if pd.isna(value):
                    return ""
                return str(value).strip()
            
            # Fallback to index
            if len(row) > default_index:
                value = row.iloc[default_index]
                if pd.isna(value):
                    return ""
                return str(value).strip()
            
            return ""
        except Exception:
            return ""

    def _safe_get_int(self, row, column_name, default_index):
        """Safely get integer value from row"""
        try:
            str_value = self._safe_get(row, column_name, default_index)
            if str_value and str_value.strip():
                return int(float(str_value))  # Handle both int and float strings
            return 0
        except (ValueError, TypeError):
            return 0
    
    def _is_header_row(self, row):
        """Check if row is a header row - updated for your data"""
        if len(row) == 0:
            return True
            
        first_value = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        first_value_upper = first_value.upper()
        
        # Header indicators for YOUR data
        header_indicators = [
            'DATE', 'VILLAGE', 'TALUKA', 'DISTRICT', 'MANTRI', 
            'SABHASAD', 'CONTACT', 'TOTAL', 'SR', 'NO', 'NAME'
        ]
        
        # If first value contains any header indicator, it's likely a header
        return any(indicator in first_value_upper for indicator in header_indicators)
        
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            if pd.isna(value):
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _get_or_create_customer(self, name, mobile, village, taluka, district):
        """Get existing customer or create new one"""
        try:
            # Check if customer exists
            result = self.db.execute_query(
                'SELECT customer_id FROM customers WHERE name = ? AND mobile = ?', 
                (name, mobile)
            )
            
            if result:
                return result[0][0]
            else:
                # Create new customer
                customer_code = f"CUST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.db.add_customer(name, mobile, village, taluka, district, customer_code)
                
                # Get the new customer ID
                result = self.db.execute_query(
                    'SELECT customer_id FROM customers WHERE customer_code = ?', 
                    (customer_code,)
                )
                return result[0][0] if result else None
                
        except Exception as e:
            logger.error(f"Error getting/creating customer: {e}")
            return None
    
    def _get_product_id(self, product_name):
        """Get product ID from product name"""
        clean_name = product_name.upper().strip()
        return self.product_mapping.get(clean_name, None)
    
    def _extract_location_from_name(self, name):
        """Extract village and taluka from customer name"""
        name_upper = name.upper()
        
        locations = {
            'AMIYAD': ('Amiyad', ''),
            'AMVAD': ('Amvad', ''),
            'ANKALAV': ('', 'Ankalav'),
            'PETLAD': ('', 'Petlad'),
            'BORSAD': ('', 'Borsad'),
            'VADODARA': ('', 'Vadodara'),
            'ANAND': ('', 'Anand'),
            'NADIAD': ('', 'Nadiad')
        }
        
        village, taluka = "", ""
        for location, (v, t) in locations.items():
            if location in name_upper:
                if v: 
                    village = v
                if t: 
                    taluka = t
                break
        
        return village, taluka
    


    # Add to DataProcessor class in data_processor.py

    def _is_sales_sheet(self, df):
        """Enhanced sales sheet detection with better logging"""
        columns_lower = [str(col).lower() for col in df.columns]
        
        print(f"\n🔍 ENHANCED SALES DETECTION:")
        print(f"   All columns: {columns_lower}")
        
        sales_indicators = [
            'invoice', 'sale', 'amount', 'product', 'quantity', 'rate', 
            'total', 'price', 'bill', 'payment', 'item', 'qty'
        ]
        
        found_indicators = []
        for indicator in sales_indicators:
            matching_cols = [col for col in columns_lower if indicator in col]
            if matching_cols:
                found_indicators.append((indicator, matching_cols))
        
        print(f"   Found sales indicators: {found_indicators}")
        
        score = len(found_indicators)
        print(f"   Sales detection score: {score}")
        
        return score >= 2

    def process_sales_sheet(self, df, file_name, sheet_name):
        """Enhanced sales data processing with better logging"""
        try:
            processed_rows = 0
            print(f"🔄 Processing sales sheet: {sheet_name} with {len(df)} rows")
            
            for index, row in df.iterrows():
                try:
                    # Skip header rows and empty rows
                    if self._is_header_row(row) or pd.isna(row.iloc[0]):
                        continue
                    
                    print(f"🔧 Processing row {index}")
                    
                    # Extract sales data with flexible column mapping
                    invoice_no = self._extract_sales_value(row, 'invoice', 0, f"INV_{datetime.now().strftime('%Y%m%d%H%M%S')}_{index}")
                    customer_name = self._extract_sales_value(row, 'customer', 1, "Unknown Customer")
                    product_name = self._extract_sales_value(row, 'product', 2, "Unknown Product")
                    quantity = self._safe_float(self._extract_sales_value(row, 'quantity', 3, 0))
                    amount = self._safe_float(self._extract_sales_value(row, 'amount', 4, 0))
                    
                    print(f"   Extracted - Invoice: '{invoice_no}', Customer: '{customer_name}', Product: '{product_name}', Qty: {quantity}, Amount: {amount}")
                    
                    # Validate essential data
                    if not customer_name or customer_name == "Unknown Customer":
                        print(f"   ⚠️ Skipping - invalid customer name")
                        continue
                    
                    if quantity <= 0:
                        print(f"   ⚠️ Skipping - invalid quantity: {quantity}")
                        continue
                    
                    if amount <= 0:
                        print(f"   ⚠️ Skipping - invalid amount: {amount}")
                        continue
                    
                    # Get or create customer
                    customer_id = self._get_or_create_customer(customer_name, "", "", "", "")
                    if not customer_id:
                        print(f"   ⚠️ Skipping - could not get/create customer")
                        continue
                    
                    # Get product ID
                    product_id = self._get_product_id(product_name)
                    if not product_id:
                        print(f"   ⚠️ Skipping - product not found: '{product_name}'")
                        print(f"   Available products: {list(self.product_mapping.keys())}")
                        continue
                    
                    # Calculate rate
                    rate = amount / quantity if quantity > 0 else 0
                    
                    # Create sale items
                    sale_date = datetime.now().date()
                    sale_items = [{
                        'product_id': product_id,
                        'quantity': quantity,
                        'rate': rate
                    }]
                    
                    # Generate proper invoice number
                    if not invoice_no or invoice_no.startswith('INV_'):
                        invoice_no = self.db.generate_invoice_number()
                    
                    print(f"   Creating sale - Customer ID: {customer_id}, Product ID: {product_id}")
                    
                    # Add sale to database
                    sale_id = self.db.add_sale(invoice_no, customer_id, sale_date, sale_items)
                    
                    if sale_id and sale_id > 0:
                        processed_rows += 1
                        print(f"   ✅ Successfully created sale ID: {sale_id}")
                    else:
                        print(f"   ❌ Failed to create sale")
                        
                except Exception as e:
                    print(f"   ❌ Error in row {index}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"🎉 Processed {processed_rows} sales from {sheet_name}")
            return processed_rows > 0
            
        except Exception as e:
            print(f"💥 Error processing sales sheet: {e}")
            import traceback
            traceback.print_exc()
            return False
    def _extract_sales_value(self, row, field_name, default_index, default_value):
        """Extract sales values with flexible column matching"""
        # Try to find column by name
        for col_name in row.index:
            if field_name in str(col_name).lower():
                value = row[col_name]
                if pd.notna(value):
                    return str(value).strip()
        
        # Fallback to index
        if len(row) > default_index:
            value = row.iloc[default_index]
            if pd.notna(value):
                return str(value).strip()
        
        return default_value

    # Add to DataProcessor class

    def _is_payment_sheet(self, df):
        """Detect payment sheets"""
        columns_lower = [str(col).lower() for col in df.columns]
        
        payment_indicators = [
            'payment', 'paid', 'amount', 'invoice', 'date', 'method',
            'cash', 'gpay', 'cheque', 'bank', 'rrn', 'reference'
        ]
        
        score = sum(1 for indicator in payment_indicators 
                    if any(indicator in col for col in columns_lower))
        
        print(f"🔍 Payment detection - Score: {score}, Columns: {columns_lower}")
        return score >= 2

    def process_payment_sheet(self, df, file_name, sheet_name):
        """Process payment data from sheet"""
        try:
            processed_rows = 0
            print(f"🔄 Processing payment sheet: {sheet_name}")
            
            for index, row in df.iterrows():
                try:
                    if self._is_header_row(row) or pd.isna(row.iloc[0]):
                        continue
                    
                    # Extract payment data
                    invoice_no = self._extract_sales_value(row, 'invoice', 0, "")
                    amount = self._safe_float(self._extract_sales_value(row, 'amount', 1, 0))
                    payment_date = self._extract_sales_value(row, 'date', 2, datetime.now().date())
                    payment_method = self._extract_sales_value(row, 'method', 3, "Cash")
                    
                    if invoice_no and amount > 0:
                        # Find sale by invoice number
                        sale_result = self.db.execute_query(
                            'SELECT sale_id FROM sales WHERE invoice_no = ?',
                            (invoice_no,),
                            log_action=False
                        )
                        
                        if sale_result:
                            sale_id = sale_result[0][0]
                            
                            # Add payment
                            self.db.execute_query('''
                            INSERT INTO payments (sale_id, payment_date, payment_method, amount)
                            VALUES (?, ?, ?, ?)
                            ''', (sale_id, payment_date, payment_method, amount))
                            
                            processed_rows += 1
                            print(f"✅ Processed payment for invoice {invoice_no}")
                    
                except Exception as e:
                    print(f"❌ Error processing payment row {index}: {e}")
                    continue
            
            print(f"🎉 Processed {processed_rows} payments from {sheet_name}")
            return processed_rows > 0
            
        except Exception as e:
            print(f"💥 Error processing payment sheet: {e}")
            return False


    def _is_customer_sheet(self, df):
        """Check if sheet contains customer data - IMPROVED"""
        columns_lower = [str(col).lower() for col in df.columns]
        
        customer_indicators = [
            'customer', 'name', 'mobile', 'phone', 'village', 'taluka', 
            'district', 'code', 'contact'
        ]
        
        score = sum(1 for indicator in customer_indicators 
                if any(indicator in col for col in columns_lower))
        
        print(f"🔍 Customer sheet detection - Score: {score}, Columns: {columns_lower}")
        return score >= 2

    def _is_distributor_sheet(self, df):
        """Enhanced distributor sheet detection with better logging"""
        columns_lower = [str(col).lower() for col in df.columns]
        
        print(f"\n🔍 ENHANCED DISTRIBUTOR DETECTION:")
        print(f"   All columns: {columns_lower}")
        
        distributor_indicators = [
            'distributor', 'mantri', 'sabhasad', 'contact_in_group',
            'village', 'taluka', 'district', 'leader', 'team', 'sabh'
        ]
        
        found_indicators = []
        for indicator in distributor_indicators:
            matching_cols = [col for col in columns_lower if indicator in col]
            if matching_cols:
                found_indicators.append((indicator, matching_cols))
        
        print(f"   Found indicators: {found_indicators}")
        
        score = len(found_indicators)
        print(f"   Detection score: {score}")
        
        # More flexible detection - lower threshold
        return score >= 1  # Even if we find just one indicator, try processing

    def process_single_sheet(self, df, sheet_name, file_name):
        """Process a single sheet with detailed logging"""
        print(f"🔄 Processing sheet: {sheet_name} from {file_name}")
        
        if self._is_sales_sheet(df):
            print("✅ Detected as SALES sheet")
            return self.process_sales_sheet(df, file_name, sheet_name)
        elif self._is_customer_sheet(df):
            print("✅ Detected as CUSTOMER sheet") 
            return self.process_customer_sheet(df, file_name, sheet_name)
        elif self._is_distributor_sheet(df):
            print("✅ Detected as DISTRIBUTOR sheet")
            return self.process_distributor_sheet(df, file_name, sheet_name)
        else:
            print("❓ Unknown sheet type - trying customer processing as fallback")
            return self.process_customer_sheet(df, file_name, sheet_name)
        
    def process_excel_file(self, file_path):
        """Enhanced file processing with all data types"""
        try:
            file_name = os.path.basename(file_path)
            print(f"🚀 Processing file: {file_name}")
            
            excel_file = pd.ExcelFile(file_path)
            processed_sheets = 0
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df_clean = self._clean_dataframe(df)
                
                print(f"\n📊 Sheet: {sheet_name}")
                print(f"   Columns: {df_clean.columns.tolist()}")
                
                # Check all types with priority
                is_payment = self._is_payment_sheet(df_clean)
                is_sales = self._is_sales_sheet(df_clean)
                is_customer = self._is_customer_sheet(df_clean)
                is_distributor = self._is_distributor_sheet(df_clean)
                
                print(f"   Detection - Payment: {is_payment}, Sales: {is_sales}, Customer: {is_customer}, Distributor: {is_distributor}")
                
                processed = False
                if is_payment:
                    print("   💳 Processing as PAYMENT sheet")
                    processed = self.process_payment_sheet(df_clean, file_name, sheet_name)
                elif is_sales:
                    print("   💰 Processing as SALES sheet")
                    processed = self.process_sales_sheet(df_clean, file_name, sheet_name)
                elif is_distributor:
                    print("   🤝 Processing as DISTRIBUTOR sheet")
                    processed = self.process_distributor_sheet(df_clean, file_name, sheet_name)
                elif is_customer:
                    print("   👥 Processing as CUSTOMER sheet")
                    processed = self.process_customer_sheet(df_clean, file_name, sheet_name)
                else:
                    print("   ❓ Unknown sheet type")
                
                if processed:
                    processed_sheets += 1
                    print(f"   ✅ Successfully processed")
                else:
                    print(f"   ❌ Failed to process")
            
            print(f"\n🎉 File processing complete: {processed_sheets}/{len(excel_file.sheet_names)} sheets processed")
            return processed_sheets > 0
            
        except Exception as e:
            print(f"💥 Error processing file {file_path}: {e}")
            return False