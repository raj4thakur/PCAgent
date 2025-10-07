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
        """Process a single Excel file and return True if data was processed"""
        try:
            file_name = os.path.basename(file_path)
            logger.info(f"Processing file: {file_name}")
            
            excel_file = pd.ExcelFile(file_path)
            processed_sheets = 0
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Clean the dataframe
                df = self._clean_dataframe(df)
                
                if self._is_sales_sheet(df):
                    processed = self.process_sales_sheet(df, file_name, sheet_name)
                    if processed:
                        processed_sheets += 1
                elif self._is_customer_sheet(df):
                    processed = self.process_customer_sheet(df, file_name, sheet_name)
                    if processed:
                        processed_sheets += 1
                elif self._is_distributor_sheet(df):
                    processed = self.process_distributor_sheet(df, file_name, sheet_name)
                    if processed:
                        processed_sheets += 1
                else:
                    logger.warning(f"Unknown sheet format: {sheet_name} in {file_name}")
            
            return processed_sheets > 0
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
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
        """Process customer data from sheet"""
        try:
            processed_rows = 0
            
            for index, row in df.iterrows():
                try:
                    # Skip header rows and empty rows
                    if self._is_header_row(row) or pd.isna(row.iloc[0]):
                        continue
                    
                    # Extract customer data (adjust based on your Excel structure)
                    customer_code = str(row.iloc[0]) if len(row) > 0 else f"CUST_{datetime.now().strftime('%Y%m%d%H%M%S')}_{index}"
                    name = str(row.iloc[1]) if len(row) > 1 else "Unknown"
                    mobile = str(row.iloc[2]) if len(row) > 2 else ""
                    
                    # Extract location from name or separate columns
                    village, taluka = self._extract_location_from_name(name)
                    
                    if len(row) > 3:
                        village_col = str(row.iloc[3])
                        if village_col and not any(x in village_col.upper() for x in ['VILLAGE', 'CITY', 'TOWN']):
                            village = village_col
                    
                    if len(row) > 4:
                        taluka_col = str(row.iloc[4])
                        if taluka_col and not any(x in taluka_col.upper() for x in ['TALUKA', 'DISTRICT']):
                            taluka = taluka_col
                    
                    # Add customer to database
                    self.db.add_customer(name, mobile, village, taluka, "", customer_code)
                    processed_rows += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing row {index} in customer sheet: {e}")
                    continue
            
            logger.info(f"Processed {processed_rows} customers from {sheet_name}")
            return processed_rows > 0
            
        except Exception as e:
            logger.error(f"Error processing customer sheet: {e}")
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
                    village = self._safe_get(row, 'VILLAGE', 1)
                    taluka = self._safe_get(row, 'TALUKA', 2) 
                    district = self._safe_get(row, 'DISTRICT', 3)
                    mantri_name = self._safe_get(row, 'MANTRI_NAME', 4)
                    mantri_mobile = self._safe_get(row, 'MANTRI_MOBILE', 5)
                    sabhasad_count = self._safe_get_int(row, 'SABHASAD', 6)
                    contact_in_group = self._safe_get_int(row, 'CONTACT_IN_GROUP', 7)
                    
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
        village = self._safe_get(row, 'VILLAGE', 1)
        taluka = self._safe_get(row, 'TALUKA', 2)
        
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