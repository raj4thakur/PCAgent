# pages/file_viewer.py
import streamlit as st
import pandas as pd
import os
import glob
import chardet
from datetime import datetime
import re

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

def show_file_viewer_page(db=None, data_processor=None):
    """Universal file viewer for any Excel/CSV file with advanced Gujarati to English conversion"""
    st.title("🔍 Universal File Viewer")
    st.markdown("View and analyze any Excel or CSV file, with advanced Gujarati to English conversion using AI translation")
    
    if not TRANSLATOR_AVAILABLE:
        st.error("""
        **Translation features require deep-translator**
        Install with: `pip install deep-translator`
        
        Without this, only basic number conversion will work.
        """)
    
    # File selection options
    tab1, tab2 = st.tabs(["📁 Browse Data Folder", "📤 Upload New File"])
    
    with tab1:
        show_data_folder_browser()
    
    with tab2:
        show_file_uploader()

def show_data_folder_browser():
    """Browse and view files from the data folder"""
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        st.info("Data folder created. Upload files to get started.")
        return
    
    # Get all supported files
    excel_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.xls"))
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    all_files = excel_files + csv_files
    
    if not all_files:
        st.info("No Excel or CSV files found in the data folder.")
        return
    
    # File selection
    st.subheader("📂 Select File to View")
    
    file_options = {os.path.basename(f): f for f in all_files}
    selected_file_name = st.selectbox("Choose a file", options=list(file_options.keys()))
    
    if selected_file_name:
        file_path = file_options[selected_file_name]
        display_file_content(file_path, selected_file_name)

def show_file_uploader():
    """Upload and view new files"""
    st.subheader("📤 Upload New File")
    
    uploaded_file = st.file_uploader(
        "Choose Excel or CSV file", 
        type=['xlsx', 'xls', 'csv'],
        help="Upload Excel (.xlsx, .xls) or CSV files for viewing"
    )
    
    if uploaded_file:
        # Save to data folder for processing
        file_path = os.path.join("data", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        display_file_content(file_path, uploaded_file.name)

def display_file_content(file_path, file_name):
    """Display file content with conversion options"""
    try:
        # File info
        file_size = os.path.getsize(file_path) / 1024
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File", file_name)
        with col2:
            st.metric("Size", f"{file_size:.1f} KB")
        with col3:
            st.metric("Modified", file_mtime.strftime('%Y-%m-%d %H:%M'))
        
        # Conversion options
        st.subheader("🔄 Conversion Options")
        
        col1, col2 = st.columns(2)
        with col1:
            convert_gujarati = st.checkbox("Convert Gujarati to English", value=True)
        with col2:
            use_ai_translation = st.checkbox("Use AI Translation", 
                                           value=TRANSLATOR_AVAILABLE,
                                           disabled=not TRANSLATOR_AVAILABLE)
        
        # Read file
        if file_path.endswith('.csv'):
            df = read_csv_file(file_path)
        else:
            df = read_excel_file(file_path)
        
        if df is None or df.empty:
            st.warning("No data found in the file.")
            return
        
        # Show original data
        st.subheader("📝 Original Data")
        display_dataframe_info(df, "Original")
        
        # Apply conversion if requested
        if convert_gujarati:
            with st.spinner("Converting Gujarati content..."):
                df_converted = convert_gujarati_data_advanced(df, use_ai_translation)
            
            st.subheader("🔤 Converted Data (Gujarati → English)")
            display_dataframe_info(df_converted, "Converted")
            
            # Show conversion summary
            show_conversion_summary(df, df_converted)
        
        # Data analysis tools
        st.subheader("🔧 Data Analysis Tools")
        show_data_analysis_tools(df_converted if convert_gujarati else df)
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

def show_conversion_summary(original_df, converted_df):
    """Show summary of Gujarati to English conversion"""
    st.subheader("📊 Conversion Summary")
    
    changes_detected = False
    conversion_examples = []
    
    # Check for changes
    for i in range(min(3, len(original_df))):
        for col in original_df.columns[:3]:
            if i < len(original_df):
                orig_val = str(original_df.iloc[i][col])
                conv_val = str(converted_df.iloc[i][col])
                if orig_val != conv_val and contains_gujarati(orig_val):
                    changes_detected = True
                    conversion_examples.append(f"`{orig_val}` → `{conv_val}`")
                    break
    
    if changes_detected:
        st.success("✅ Gujarati content was detected and converted to English")
        if conversion_examples:
            st.write("**Conversion Examples:**")
            for example in conversion_examples:
                st.write(example)
    else:
        st.info("ℹ️ No Gujarati content detected - data is already in English")

# Helper functions for file reading and conversion
def read_csv_file(file_path):
    """Read CSV file with automatic encoding detection"""
    try:
        # Try reading with different encodings
        for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                return pd.read_csv(file_path, encoding=enc)
            except:
                continue
        
        # Last resort
        return pd.read_csv(file_path, encoding='utf-8', errors='ignore')
    except Exception as e:
        st.error(f"Error reading CSV: {str(e)}")
        return pd.DataFrame()

def read_excel_file(file_path):
    """Read Excel file with all sheets"""
    try:
        excel_file = pd.ExcelFile(file_path)
        
        if len(excel_file.sheet_names) == 1:
            return pd.read_excel(file_path)
        else:
            sheet_name = st.selectbox(
                "Select Sheet to View", 
                options=excel_file.sheet_names,
                key=f"sheet_select_{file_path}"
            )
            return pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return pd.DataFrame()

def convert_gujarati_data_advanced(df, use_ai_translation=False):
    """Convert Gujarati content to English using advanced methods"""
    try:
        df_converted = df.copy()
        
        # Convert column names
        df_converted.columns = [convert_gujarati_text(col, use_ai_translation) for col in df_converted.columns]
        
        # Convert data in each column
        for col in df_converted.columns:
            df_converted[col] = df_converted[col].astype(str)
            df_converted[col] = df_converted[col].apply(
                lambda x: convert_gujarati_text(x, use_ai_translation)
            )
        
        return df_converted
    except Exception as e:
        st.warning(f"Conversion issues: {str(e)}")
        return df

def convert_gujarati_text(text, use_ai_translation=False):
    """Convert Gujarati text to English using multiple methods"""
    if not isinstance(text, str) or not text.strip():
        return text
    
    # Step 1: Always convert Gujarati numbers
    text = gujarati_to_english_digits(text)
    
    # Step 2: Check if text contains Gujarati characters
    if contains_gujarati(text):
        if use_ai_translation and TRANSLATOR_AVAILABLE:
            try:
                return GoogleTranslator(source='gu', target='en').translate(text)
            except Exception as e:
                st.warning(f"Translation failed for '{text}': {str(e)}")
                return apply_basic_gujarati_conversion(text)
        else:
            return apply_basic_gujarati_conversion(text)
    else:
        return text

def gujarati_to_english_digits(text):
    """Convert Gujarati numbers to English digits"""
    gujarati_to_english_numbers = {
        '૦': '0', '૧': '1', '૨': '2', '૩': '3', '૪': '4',
        '૫': '5', '૬': '6', '૭': '7', '૮': '8', '૯': '9'
    }
    
    converted_text = text
    for guj, eng in gujarati_to_english_numbers.items():
        converted_text = converted_text.replace(guj, eng)
    
    return converted_text

def contains_gujarati(text):
    """Check if text contains Gujarati characters"""
    gujarati_pattern = re.compile(r'[\u0A80-\u0AFF]')
    return bool(gujarati_pattern.search(text))

def apply_basic_gujarati_conversion(text):
    """Apply basic Gujarati to English conversion for common words"""
    gujarati_to_english_words = {
        'ગ્રાહક': 'Customer', 'નામ': 'Name', 'મોબાઈલ': 'Mobile', 'ફોન': 'Phone',
        'ગામ': 'Village', 'તાલુકો': 'Taluka', 'જિલ્લો': 'District', 'શહેર': 'City',
        'બીલ': 'Bill', 'ચલણ': 'Invoice', 'રકમ': 'Amount', 'પ્રમાણ': 'Quantity',
        'ઉત્પાદન': 'Product', 'તારીખ': 'Date', 'ચુકવણી': 'Payment'
    }
    
    converted_text = text
    for guj, eng in gujarati_to_english_words.items():
        converted_text = converted_text.replace(guj, eng)
    
    return converted_text

def display_dataframe_info(df, title):
    """Display dataframe with comprehensive information"""
    st.write(f"**{title} Data Summary**")
    
    # Basic info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        non_empty = len(df.dropna(how='all'))
        st.metric("Non-empty Rows", non_empty)
    with col4:
        empty_cells = df.isna().sum().sum()
        st.metric("Empty Cells", empty_cells)
    
    # Column information
    st.subheader("📋 Column Details")
    col_info = []
    for col in df.columns:
        col_info.append({
            'Column Name': col,
            'Data Type': str(df[col].dtype),
            'Non-Null Count': df[col].count(),
            'Null Count': df[col].isna().sum(),
            'Unique Values': df[col].nunique()
        })
    
    col_info_df = pd.DataFrame(col_info)
    st.dataframe(col_info_df, use_container_width=True)
    
    # Data preview
    st.subheader("👀 Data Preview")
    show_rows = st.slider("Number of rows to show", 5, 100, 10, key=f"rows_{title}")
    st.dataframe(df.head(show_rows), use_container_width=True)

def show_data_analysis_tools(df):
    """Show basic data analysis tools"""
    tab1, tab2, tab3 = st.tabs(["📈 Basic Stats", "🔍 Search & Filter", "💾 Export"])
    
    with tab1:
        show_basic_stats(df)
    
    with tab2:
        show_search_filter(df)
    
    with tab3:
        show_export_options(df)

def show_basic_stats(df):
    """Show basic statistical analysis"""
    st.write("**Numerical Columns Statistics**")
    
    numerical_cols = df.select_dtypes(include=['number']).columns
    if len(numerical_cols) > 0:
        st.dataframe(df[numerical_cols].describe(), use_container_width=True)
    else:
        st.info("No numerical columns found for statistical analysis")

def show_search_filter(df):
    """Show search and filter options"""
    st.write("**Search in Data**")
    
    search_term = st.text_input("Search term")
    if search_term:
        # Search across all string columns
        mask = pd.Series([False] * len(df))
        for col in df.columns:
            if df[col].dtype == 'object':
                mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
        
        filtered_df = df[mask]
        st.write(f"Found {len(filtered_df)} matching rows")
        st.dataframe(filtered_df.head(20), use_container_width=True)

def show_export_options(df):
    """Show data export options"""
    st.write("**Export Processed Data**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="converted_data.csv",
            mime="text/csv"
        )
    
    with col2:
        # For Excel, we need to save to a file first
        excel_file = "converted_data.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as f:
            st.download_button(
                label="📊 Download as Excel",
                data=f,
                file_name=excel_file,
                mime="application/vnd.ms-excel"
            )
        # Clean up
        if os.path.exists(excel_file):
            os.remove(excel_file)