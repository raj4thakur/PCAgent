# pages/data_import.py
import streamlit as st
import os
import glob
from datetime import datetime

def show_data_import_page(db, data_processor):
    """Show data import page"""
    st.title("📤 Data Import & Processing")
    
    if not data_processor:
        st.error("Data processor not available. Please check initialization.")
        return
    
    data_dir = "data"
    if os.path.exists(data_dir):
        excel_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.xls"))
        
        if excel_files:
            st.subheader("📁 Existing Files in Data Folder")
            
            for file_path in excel_files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) / 1024
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{file_name}**")
                    st.write(f"Size: {file_size:.1f} KB | Modified: {file_mtime.strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if st.button(f"🔄 Process", key=f"process_{file_name}"):
                        try:
                            if data_processor.process_excel_file(file_path):
                                st.success(f"✅ Processed: {file_name}")
                                st.rerun()
                            else:
                                st.warning(f"⚠️ No data processed from: {file_name}")
                        except Exception as e:
                            st.error(f"❌ Error processing {file_name}: {str(e)}")
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{file_name}"):
                        try:
                            os.remove(file_path)
                            st.success(f"✅ Deleted: {file_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting file: {e}")
            
            if st.button("🔄 Process All Files", type="primary"):
                success_count = 0
                for file_path in excel_files:
                    try:
                        if data_processor.process_excel_file(file_path):
                            success_count += 1
                    except Exception as e:
                        st.error(f"Error processing {os.path.basename(file_path)}: {str(e)}")
                st.success(f"✅ Processed {success_count}/{len(excel_files)} files successfully!")
                if success_count > 0:
                    st.rerun()
        else:
            st.info("No Excel files found in the data folder.")
    else:
        os.makedirs(data_dir, exist_ok=True)
        st.info("Data folder created. Upload Excel files to get started.")
    
    st.subheader("📤 Upload New Excel File")
    uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file:
        file_path = os.path.join("data", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ File saved: {uploaded_file.name}")
        
        if st.button(f"🔄 Process {uploaded_file.name}"):
            try:
                if data_processor.process_excel_file(file_path):
                    st.success(f"✅ Processed: {uploaded_file.name}")
                    
                    # Show data preview
                    st.subheader("📊 Imported Data Preview")
                    try:
                        customers = db.get_dataframe('customers')
                        sales = db.get_dataframe('sales')
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Customers", len(customers))
                            if not customers.empty:
                                st.dataframe(customers.tail(3), use_container_width=True)
                        with col2:
                            st.metric("Sales", len(sales))
                            if not sales.empty:
                                st.dataframe(sales.tail(3), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error loading preview data: {e}")
                    
                    st.rerun()
                else:
                    st.warning(f"⚠️ No data processed from: {uploaded_file.name}")
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")