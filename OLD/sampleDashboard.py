import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Set page configuration
st.set_page_config(
    page_title="Calcium Supplement Sales Dashboard",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sample data (replace with your actual data loading)
@st.cache_data
def load_data():
    # Sales data with customer information
    sales_data = pd.DataFrame({
        'Date': ['2025-06-01', '2025-06-01', '2025-06-10', '2025-06-11', '2025-06-12', 
                '2025-07-30', '2025-07-30', '2025-07-31', '2025-07-31', '2025-07-31'],
        'Customer': ['Gopalbhai', 'Ramprasad Khatik', 'Vikramsinh', 'Prahladbhai -Mantry', 'V S Stud Farm',
                    'Hemendrabhai Parmar', 'Sundarbhai', 'Kamleshbhai Vasava -Mantry', 'Kiranbhai -Mantry', 'Kiritbhai'],
        'Village': ['Shilly', 'Rajasthan', 'Mithapura', 'Bhalod Dairy', 'Waghodia',
                   'Panchdevla', 'Siyali', 'Moran', 'Talodara', 'Sindhrot'],
        'Total_L': [35.0, 400.0, 30.0, 7.0, 400.0, 50.0, 13.0, 1.0, 1.0, 30.0]
    })
    
    # Mantri data with village information
    mantri_data = pd.DataFrame({
        'DATE': ['2024-03-08', '2025-06-03', '2025-02-23', '2025-05-28', '2025-05-02',
                '2024-09-21', '2024-10-26', '2024-03-19', '2025-01-30', '2025-07-18'],
        'VILLAGE': ['JILOD', 'MANJIPURA', 'GOTHADA', 'UNTKHARI', 'VEMAR',
                   'KANODA', 'KOTAMBI', 'RASNOL', 'JITPURA', 'BHATPURA'],
        'MANTRY_NAME': ['AJAYBHAI PATEL', 'AJAYBHAI PATEL', 'AJGAR KHAN', 'AMBALAL CHAUHAN', 'AMBALAL GOHIL',
                       'VINUBHAI SOLANKI', 'VISHNUBHAI', 'VITHTHALBHAI', 'YOGESHBHAI', 'YUVRAJSINH'],
        'MOBILE_NO': [7984136988, 9737910554, 9724831903, 9313860902, 9978081739,
                     9998756469, 9909550170, 9924590017, 7990383811, 6353209447],
        'sabhasad': [38, 21, 3, 0, 2, 0, 14, 1183, 8, 6],
        'contact_in_group': [38.0, 16.0, 2.0, 0.0, 0.0, 0.0, 14.0, 268.0, 5.0, 4.0],
        'TOTAL_L': [99.0, 120.0, 19.0, 87.0, 32.0, 60.0, 54.0, 82.0, 25.0, 11.0]
    })
    
    # Convert dates to datetime
    sales_data['Date'] = pd.to_datetime(sales_data['Date'])
    mantri_data['DATE'] = pd.to_datetime(mantri_data['DATE'], errors='coerce')
    
    return sales_data, mantri_data

# Analysis functions
def analyze_mantri_performance(mantri_data, sales_data):
    mantri_data = mantri_data.copy()
    
    # Calculate performance metrics
    mantri_data['Conversion_Rate'] = (mantri_data['contact_in_group'] / mantri_data['sabhasad'] * 100).round(2)
    mantri_data['Conversion_Rate'] = mantri_data['Conversion_Rate'].replace([np.inf, -np.inf], 0).fillna(0)
    mantri_data['Untapped_Potential'] = mantri_data['sabhasad'] - mantri_data['contact_in_group']
    mantri_data['Sales_Efficiency'] = (mantri_data['TOTAL_L'] / mantri_data['contact_in_group']).round(2)
    mantri_data['Sales_Efficiency'] = mantri_data['Sales_Efficiency'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Priority score calculation
    mantri_data['Priority_Score'] = (
        (mantri_data['Untapped_Potential'] / mantri_data['Untapped_Potential'].max() * 50) +
        ((100 - mantri_data['Conversion_Rate']) / 100 * 50)
    ).round(2)
    
    # Add recent sales data
    recent_sales = sales_data.groupby('Village').agg({
        'Total_L': 'sum',
        'Customer': 'count'
    }).reset_index()
    recent_sales.columns = ['VILLAGE', 'Recent_Sales', 'Recent_Customers']
    
    mantri_data = mantri_data.merge(recent_sales, on='VILLAGE', how='left')
    mantri_data['Recent_Sales'] = mantri_data['Recent_Sales'].fillna(0)
    mantri_data['Recent_Customers'] = mantri_data['Recent_Customers'].fillna(0)
    
    return mantri_data

def analyze_village_performance(sales_data, mantri_data):
    # Group sales by village
    village_sales = sales_data.groupby('Village').agg({
        'Total_L': 'sum',
        'Customer': 'count',
        'Date': 'max'
    }).reset_index()
    village_sales.columns = ['Village', 'Total_Sales', 'Customer_Count', 'Last_Sale_Date']
    
    # Calculate days since last sale
    village_sales['Days_Since_Last_Sale'] = (datetime.now() - village_sales['Last_Sale_Date']).dt.days
    
    # Merge with mantri data
    mantri_summary = mantri_data[['VILLAGE', 'MANTRY_NAME', 'MOBILE_NO', 'sabhasad', 'contact_in_group']]
    mantri_summary.columns = ['Village', 'Mantri_Name', 'Mantri_Mobile', 'Sabhasad', 'Contacts']
    
    village_performance = village_sales.merge(mantri_summary, on='Village', how='left')
    
    # Calculate performance metrics
    village_performance['Conversion_Rate'] = (village_performance['Contacts'] / village_performance['Sabhasad'] * 100).round(2)
    village_performance['Conversion_Rate'] = village_performance['Conversion_Rate'].replace([np.inf, -np.inf], 0).fillna(0)
    village_performance['Untapped_Potential'] = village_performance['Sabhasad'] - village_performance['Contacts']
    
    return village_performance

# Message templates
def get_mantri_message_template(mantri_name, village, reason, performance_data):
    templates = {
        'Low Conversion': f"""
Namaste {mantri_name} Ji!

Aapke kshetra {village} mein humare calcium supplement ki conversion rate kam hai ({performance_data['Conversion_Rate']}%). 
Humari marketing team aapke yaha demo dene aayegi. 
Kripya taiyaari rakhein aur sabhi dudh utpadakon ko soochit karein.

Aapke paas abhi bhi {int(performance_data['Untapped_Potential'])} aise farmers hain jo product nahi use kar rahe hain.

Dhanyavaad,
Calcium Supplement Team
""",
        'High Potential': f"""
Namaste {mantri_name} Ji!

Aapke kshetra {village} mein {int(performance_data['Untapped_Potential'])} aise farmers hain jo abhi tak humare product se anabhijit hain. 
Kripya unse sampark karein aur unhe product ke fayde batayein. 
Aapke liye special commission offer hai agle 10 naye customers ke liye.

Dhanyavaad,
Calcium Supplement Team
""",
        'Good Performance': f"""
Namaste {mantri_name} Ji!

Aapke kshetra {village} mein humare product ki demand badh rahi hai. 
Aapki conversion rate {performance_data['Conversion_Rate']}% hai jo bahut achchi hai.

Kripya farmers ko yaad dilaein ki pregnancy ke 3-9 mahine aur delivery ke baad calcium supplement zaroori hai.

Dhanyavaad,
Calcium Supplement Team
"""
    }
    
    return templates.get(reason, "Custom message based on analysis")

# Load data
sales_data, mantri_data = load_data()
mantri_performance = analyze_mantri_performance(mantri_data, sales_data)
village_performance = analyze_village_performance(sales_data, mantri_data)

# Streamlit app
st.title("🐄 Calcium Supplement Sales Automation Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to", ["Dashboard", "Mantri Performance", "Village Analysis", "Message Center", "Team Dispatch"])

# Dashboard
if section == "Dashboard":
    st.header("Sales Performance Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Villages Covered", len(mantri_performance))
    with col2:
        st.metric("Total Mantris", len(mantri_performance['MANTRY_NAME'].unique()))
    with col3:
        st.metric("Total Sales (Liters)", mantri_performance['TOTAL_L'].sum())
    with col4:
        avg_conversion = mantri_performance['Conversion_Rate'].mean()
        st.metric("Avg Conversion Rate", f"{avg_conversion:.2f}%")
    
    st.subheader("Top Priority Mantris")
    priority_mantris = mantri_performance.nlargest(5, 'Priority_Score')[['MANTRY_NAME', 'VILLAGE', 'Conversion_Rate', 'Untapped_Potential', 'Priority_Score']]
    st.dataframe(priority_mantris)
    
    st.subheader("Sales Distribution by Village")
    fig = px.bar(mantri_performance, x='VILLAGE', y='TOTAL_L', title='Total Sales by Village')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Conversion Rate vs Untapped Potential")
    fig = px.scatter(mantri_performance, x='Conversion_Rate', y='Untapped_Potential', 
                    size='TOTAL_L', color='VILLAGE', hover_name='MANTRY_NAME',
                    title='Mantri Performance Analysis')
    st.plotly_chart(fig, use_container_width=True)

# Mantri Performance
elif section == "Mantri Performance":
    st.header("Mantri Performance Analysis")
    
    selected_mantri = st.selectbox("Select Mantri", mantri_performance['MANTRY_NAME'].unique())
    mantri_data = mantri_performance[mantri_performance['MANTRY_NAME'] == selected_mantri].iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mantri", mantri_data['MANTRY_NAME'])
    with col2:
        st.metric("Village", mantri_data['VILLAGE'])
    with col3:
        st.metric("Conversion Rate", f"{mantri_data['Conversion_Rate']}%")
    with col4:
        st.metric("Untapped Potential", int(mantri_data['Untapped_Potential']))
    
    st.subheader("Mantri Details")
    st.dataframe(mantri_data)
    
    st.subheader("Action Recommendations")
    if mantri_data['Conversion_Rate'] < 20:
        st.error(f"**Send Marketing Team**: Conversion rate is low ({mantri_data['Conversion_Rate']}%). Need demos and awareness campaigns.")
    if mantri_data['Untapped_Potential'] > 10:
        st.warning(f"**Call Mantri**: {int(mantri_data['Untapped_Potential'])} farmers still not converted. Push Mantri to contact them.")
    if mantri_data['Conversion_Rate'] > 50:
        st.success(f"**Expand Success**: This mantri is performing well. Consider replicating their strategies.")

# Village Analysis
elif section == "Village Analysis":
    st.header("Village Performance Analysis")
    
    selected_village = st.selectbox("Select Village", village_performance['Village'].unique())
    village_data = village_performance[village_performance['Village'] == selected_village].iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Village", village_data['Village'])
    with col2:
        st.metric("Mantri", village_data['Mantri_Name'])
    with col3:
        st.metric("Total Sales (L)", village_data['Total_Sales'])
    with col4:
        st.metric("Days Since Last Sale", village_data['Days_Since_Last_Sale'])
    
    st.subheader("Village Details")
    st.dataframe(village_data)
    
    st.subheader("Action Recommendations")
    if village_data['Days_Since_Last_Sale'] > 30:
        st.error(f"**Send Marketing Team**: No sales in {village_data['Days_Since_Last_Sale']} days. Need immediate attention.")
    if village_data['Conversion_Rate'] < 25:
        st.warning(f"**Low Conversion**: Only {village_data['Conversion_Rate']}% of potential customers are converted.")
    if village_data['Total_Sales'] > 100:
        st.success(f"**High Performer**: This village has high sales volume. Consider expanding product range.")

# Message Center
elif section == "Message Center":
    st.header("Message Center")
    
    st.subheader("Mantri Communication")
    selected_mantri = st.selectbox("Select Mantri", mantri_performance['MANTRY_NAME'].unique())
    mantri_data = mantri_performance[mantri_performance['MANTRY_NAME'] == selected_mantri].iloc[0]
    
    st.write(f"**Village:** {mantri_data['VILLAGE']}")
    st.write(f"**Conversion Rate:** {mantri_data['Conversion_Rate']}%")
    st.write(f"**Untapped Potential:** {int(mantri_data['Untapped_Potential'])} farmers")
    
    if mantri_data['Conversion_Rate'] < 20:
        reason = "Low Conversion"
    elif mantri_data['Untapped_Potential'] > 10:
        reason = "High Potential"
    else:
        reason = "Good Performance"
        
    message = get_mantri_message_template(
        mantri_data['MANTRY_NAME'], 
        mantri_data['VILLAGE'], 
        reason,
        mantri_data
    )
    
    st.text_area("Generated Message", message, height=200)
    
    if st.button("Send to Mantri"):
        st.success(f"Message sent to {mantri_data['MANTRY_NAME']} at {mantri_data['MOBILE_NO']}")
        # Here you would integrate with WhatsApp API
    
    st.subheader("Bulk Message Sender")
    st.write("Send messages to multiple mantris at once")
    
    options = st.multiselect("Select Mantris", mantri_performance['MANTRY_NAME'].unique())
    message_template = st.text_area("Message Template", height=100)
    
    if st.button("Send to Selected Mantris"):
        progress_bar = st.progress(0)
        for i, mantri in enumerate(options):
            # Simulate sending
            time.sleep(0.5)
            progress_bar.progress((i + 1) / len(options))
        st.success(f"Messages sent to {len(options)} mantris")

# Team Dispatch
elif section == "Team Dispatch":
    st.header("Marketing Team Dispatch Planner")
    
    st.subheader("Villages Needing Immediate Attention")
    
    # Find villages with no recent sales or low conversion
    high_priority = village_performance[
        (village_performance['Days_Since_Last_Sale'] > 30) | 
        (village_performance['Conversion_Rate'] < 20)
    ]
    
    if not high_priority.empty:
        for _, village in high_priority.iterrows():
            with st.expander(f"{village['Village']} (Last sale: {village['Days_Since_Last_Sale']} days ago)"):
                st.write(f"**Mantri:** {village['Mantri_Name']} ({village['Mantri_Mobile']})")
                st.write(f"**Conversion Rate:** {village['Conversion_Rate']}%")
                st.write(f"**Recommended Action:** Conduct demo sessions and awareness campaign")
                
                if st.button(f"Dispatch Team to {village['Village']}", key=f"dispatch_{village['Village']}"):
                    st.success(f"Team dispatched to {village['Village']}. Mantri {village['Mantri_Name']} has been notified.")
    else:
        st.info("No villages currently require immediate team dispatch.")
    
    st.subheader("Create New Dispatch Plan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_village = st.selectbox("Select Village for Dispatch", village_performance['Village'].unique())
        village_data = village_performance[village_performance['Village'] == selected_village].iloc[0]
        
        st.write(f"**Mantri:** {village_data['Mantri_Name']}")
        st.write(f"**Last Sale:** {village_data['Days_Since_Last_Sale']} days ago")
        st.write(f"**Conversion Rate:** {village_data['Conversion_Rate']}%")
    
    with col2:
        dispatch_date = st.date_input("Dispatch Date", datetime.now() + timedelta(days=1))
        team_size = st.slider("Team Size", 1, 5, 2)
        duration = st.selectbox("Duration", ["1 day", "2 days", "3 days", "1 week"])
        
        objectives = st.text_area("Objectives", "Conduct demo sessions, educate farmers about benefits, collect feedback")
    
    if st.button("Schedule Dispatch"):
        st.success(f"Dispatch to {selected_village} scheduled for {dispatch_date}")
        st.json({
            "village": selected_village,
            "mantri": village_data['Mantri_Name'],
            "date": str(dispatch_date),
            "team_size": team_size,
            "duration": duration,
            "objectives": objectives
        })

# Footer
st.markdown("---")
st.markdown("**Calcium Supplement Sales Automation System** | For internal use only")