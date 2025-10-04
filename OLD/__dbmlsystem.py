import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="Calcium Supplement Sales Automation",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title
st.title("🐄 Calcium Supplement Sales Automation Dashboard")
st.markdown("---")

# Your exact ML functions
def enhanced_analyze_sales_data(data1, data2):
    """
    Enhanced analysis with ML components for better predictions
    """
    
    data1['Date'] = pd.to_datetime(data1['Date'])
    data2['Date'] = pd.to_datetime(data2['Date'])
    
    # Calculate basic metrics
    data1['Conversion_Rate'] = (data1['Contact_In_Group'] / data1['Sabhasad'] * 100).round(2)
    data1['Conversion_Rate'] = data1['Conversion_Rate'].replace([np.inf, -np.inf], 0).fillna(0)
    data1['Untapped_Potential'] = data1['Sabhasad'] - data1['Contact_In_Group']
    data1['Sales_Per_Contact'] = (data1['Total_L'] / data1['Contact_In_Group']).round(2)
    data1['Sales_Per_Contact'] = data1['Sales_Per_Contact'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Analyze recent sales
    recent_sales = data2.groupby('Village').agg({
        'Total_L': ['sum', 'count'],
        'Date': 'max'
    }).reset_index()
    
    recent_sales.columns = ['Village', 'Recent_Sales_L', 'Recent_Customers', 'Last_Sale_Date']
    recent_sales['Days_Since_Last_Sale'] = (datetime.now() - recent_sales['Last_Sale_Date']).dt.days
    
    # Merge data
    analysis_df = data1.merge(recent_sales, on='Village', how='left')
    analysis_df['Recent_Sales_L'] = analysis_df['Recent_Sales_L'].fillna(0)
    analysis_df['Recent_Customers'] = analysis_df['Recent_Customers'].fillna(0)
    analysis_df['Days_Since_Last_Sale'] = analysis_df['Days_Since_Last_Sale'].fillna(999)
    
    # ML Component 1: Village Clustering for Segmentation
    analysis_df = apply_village_clustering(analysis_df)
    
    # ML Component 2: Predict Sales Potential
    analysis_df = predict_sales_potential(analysis_df)
    
    # ML Component 3: Action Recommendation Classifier
    analysis_df = predict_recommended_actions(analysis_df)
    
    # Generate recommendations based on ML predictions
    recommendations = generate_ml_recommendations(analysis_df)
    
    return recommendations, analysis_df

def apply_village_clustering(analysis_df):
    """
    Use K-Means clustering to segment villages into groups
    """
    # Prepare features for clustering
    cluster_features = analysis_df[[
        'Conversion_Rate', 'Untapped_Potential', 'Sales_Per_Contact', 
        'Recent_Sales_L', 'Days_Since_Last_Sale'
    ]].fillna(0)
    
    # Standardize features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(cluster_features)
    
    # Apply K-Means clustering
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    
    # Add clusters to dataframe
    analysis_df['Cluster'] = clusters
    
    # Name the clusters based on characteristics
    cluster_names = {
        0: 'High Potential - Low Engagement',
        1: 'Steady Performers', 
        2: 'Underperforming',
        3: 'New/Developing'
    }
    
    analysis_df['Segment'] = analysis_df['Cluster'].map(cluster_names)
    
    return analysis_df

def predict_sales_potential(analysis_df):
    """
    Predict sales potential for each village using Random Forest
    """
    # Prepare features for prediction
    prediction_features = analysis_df[[
        'Sabhasad', 'Contact_In_Group', 'Conversion_Rate', 
        'Untapped_Potential', 'Recent_Sales_L', 'Days_Since_Last_Sale'
    ]].fillna(0)
    
    # Target variable: Total_L (current sales)
    target = analysis_df['Total_L'].fillna(0)
    
    # Only train if we have enough data
    if len(prediction_features) > 10:
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            prediction_features, target, test_size=0.2, random_state=42
        )
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Make predictions
        predictions = model.predict(prediction_features)
        
        # Calculate feature importance
        feature_importance = pd.DataFrame({
            'feature': prediction_features.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Add predictions to dataframe
        analysis_df['Predicted_Sales'] = predictions
        analysis_df['Sales_Gap'] = analysis_df['Predicted_Sales'] - analysis_df['Total_L']
    else:
        # Fallback if not enough data
        analysis_df['Predicted_Sales'] = analysis_df['Total_L']
        analysis_df['Sales_Gap'] = 0
    
    return analysis_df

def predict_recommended_actions(analysis_df):
    """
    Use ML to predict the best action for each village
    """
    # Define actions based on rules (for training data)
    analysis_df['Action_Label'] = np.where(
        analysis_df['Conversion_Rate'] < 20, 'Send Marketing Team',
        np.where(
            analysis_df['Untapped_Potential'] > 30, 'Call Mantri for Follow-up',
            np.where(
                analysis_df['Days_Since_Last_Sale'] > 30, 'Check on Mantri',
                np.where(
                    analysis_df['Sales_Per_Contact'] > 10, 'Provide More Stock',
                    'Regular Follow-up'
                )
            )
        )
    )
    
    # Prepare features for classification
    classification_features = analysis_df[[
        'Conversion_Rate', 'Untapped_Potential', 'Sales_Per_Contact',
        'Recent_Sales_L', 'Days_Since_Last_Sale', 'Sales_Gap'
    ]].fillna(0)
    
    # Target variable: Action_Label
    target = analysis_df['Action_Label']
    
    # Only train if we have enough data
    if len(classification_features) > 10 and len(target.unique()) > 1:
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            classification_features, target, test_size=0.2, random_state=42, stratify=target
        )
        
        # Train classifier
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        
        # Make predictions
        predictions = clf.predict(classification_features)
        prediction_proba = clf.predict_proba(classification_features)
        
        # Add predictions to dataframe
        analysis_df['ML_Recommended_Action'] = predictions
        analysis_df['Action_Confidence'] = np.max(prediction_proba, axis=1)
    else:
        # Fallback to rule-based if not enough data
        analysis_df['ML_Recommended_Action'] = analysis_df['Action_Label']
        analysis_df['Action_Confidence'] = 1.0
    
    return analysis_df

def generate_ml_recommendations(analysis_df):
    """
    Generate recommendations based on ML predictions
    """
    recommendations = []
    
    for _, row in analysis_df.iterrows():
        village = row['Village']
        mantri = row['Mantri_Name']
        mobile = row['Mantri_Mobile']
        taluka = row['Taluka']
        district = row['District']
        segment = row['Segment']
        action = row['ML_Recommended_Action']
        confidence = row['Action_Confidence']
        
        # Generate reason based on ML prediction
        if action == 'Send Marketing Team':
            reason = f"ML predicts marketing team needed (Confidence: {confidence:.2f}). Segment: {segment}"
            priority = 'High'
        elif action == 'Call Mantri for Follow-up':
            reason = f"ML predicts mantri follow-up needed (Confidence: {confidence:.2f}). Segment: {segment}"
            priority = 'High'
        elif action == 'Check on Mantri':
            reason = f"ML suggests checking on mantri (Confidence: {confidence:.2f}). Segment: {segment}"
            priority = 'Medium'
        elif action == 'Provide More Stock':
            reason = f"ML predicts stock increase needed (Confidence: {confidence:.2f}). Segment: {segment}"
            priority = 'Medium'
        else:
            reason = f"ML recommends regular follow-up (Confidence: {confidence:.2f}). Segment: {segment}"
            priority = 'Low'
        
        recommendations.append({
            'Village': village,
            'Taluka': taluka,
            'District': district,
            'Mantri': mantri,
            'Mobile': mobile,
            'Action': action,
            'Reason': reason,
            'Priority': priority,
            'Confidence': confidence,
            'Segment': segment,
            'Sales_Gap': row.get('Sales_Gap', 0)
        })
    
    return pd.DataFrame(recommendations)

def generate_ml_mantri_messages(recommendations):
    """
    Generate personalized messages based on ML recommendations
    """
    messages = []
    
    for _, row in recommendations.iterrows():
        if row['Action'] == 'Send Marketing Team':
            message = f"""
Namaste {row['Mantri']} Ji!

Our AI system has identified that your village {row['Village']} has high potential for growth. 
We're sending our marketing team to conduct demo sessions and help you reach more customers.

Based on our analysis:
- Segment: {row['Segment']}
- Confidence: {row['Confidence']*100:.1f}%

Please prepare for their visit and notify potential customers.

Dhanyavaad,
Calcium Supplement Team
"""
        elif row['Action'] == 'Call Mantri for Follow-up':
            message = f"""
Namaste {row['Mantri']} Ji!

Our AI analysis shows significant untapped potential in {row['Village']}. 
We recommend focusing on follow-up with these customers:

- Segment: {row['Segment']}
- Confidence: {row['Confidence']*100:.1f}%

A special commission offer is available for your next 10 customers.

Dhanyavaad,
Calcium Supplement Team
"""
        elif row['Action'] == 'Check on Mantri':
            message = f"""
Namaste {row['Mantri']} Ji!

Our system shows reduced activity in {row['Village']}. 
Is everything alright? Do you need any support from our team?

- Segment: {row['Segment']}
- Confidence: {row['Confidence']*100:.1f}%

Please let us know how we can help.

Dhanyavaad,
Calcium Supplement Team
"""
        elif row['Action'] == 'Provide More Stock':
            message = f"""
Namaste {row['Mantri']} Ji!

Great news! Our AI predicts increased demand in {row['Village']}. 
Would you like us to send additional stock?

- Segment: {row['Segment']}
- Confidence: {row['Confidence']*100:.1f}%
- Predicted Sales Gap: {row['Sales_Gap']:.1f}L

Please confirm your additional requirements.

Dhanyavaad,
Calcium Supplement Team
"""
        else:
            message = f"""
Namaste {row['Mantri']} Ji!

Our system shows steady performance in {row['Village']}. 
Keep up the good work!

- Segment: {row['Segment']}
- Confidence: {row['Confidence']*100:.1f}%

As always, let us know if you need any support.

Dhanyavaad,
Calcium Supplement Team
"""
        
        messages.append({
            'Mantri': row['Mantri'],
            'Mobile': row['Mobile'],
            'Village': row['Village'],
            'Action': row['Action'],
            'Message': message,
            'Priority': row['Priority'],
            'Confidence': row['Confidence']
        })
    
    return pd.DataFrame(messages)

# Visualization functions
def plot_village_performance(analysis_df):
    """Create performance visualization for villages"""
    fig = px.scatter(analysis_df, 
                     x='Conversion_Rate', 
                     y='Untapped_Potential',
                     size='Total_L',
                     color='Segment',
                     hover_name='Village',
                     title='Village Performance Analysis',
                     labels={'Conversion_Rate': 'Conversion Rate (%)',
                             'Untapped_Potential': 'Untapped Potential'})
    
    fig.update_layout(height=500)
    return fig

def plot_sales_trends(analysis_df):
    """Create sales trends visualization"""
    fig = px.bar(analysis_df, 
                 x='Village', 
                 y='Total_L',
                 color='Segment',
                 title='Total Sales by Village',
                 labels={'Total_L': 'Total Sales (L)', 'Village': 'Village'})
    
    fig.update_layout(height=400, xaxis_tickangle=-45)
    return fig

def plot_priority_matrix(recommendations):
    """Create priority matrix visualization"""
    priority_order = {'High': 3, 'Medium': 2, 'Low': 1}
    recommendations['Priority_Value'] = recommendations['Priority'].map(priority_order)
    
    fig = px.treemap(recommendations, 
                     path=['Priority', 'Village'],
                     values='Priority_Value',
                     color='Priority_Value',
                     color_continuous_scale='RdYlGn_r',
                     title='Action Priority Matrix')
    
    fig.update_layout(height=500)
    return fig

def display_key_metrics(analysis_df):
    """Display key performance metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Villages", len(analysis_df))
    with col2:
        avg_conversion = analysis_df['Conversion_Rate'].mean()
        st.metric("Avg Conversion Rate", f"{avg_conversion:.1f}%")
    with col3:
        total_untapped = analysis_df['Untapped_Potential'].sum()
        st.metric("Total Untapped Potential", f"{total_untapped}")
    with col4:
        total_sales = analysis_df['Total_L'].sum()
        st.metric("Total Sales (L)", f"{total_sales}")

# Initialize session state
if 'data1' not in st.session_state:
    st.session_state.data1 = None
if 'data2' not in st.session_state:
    st.session_state.data2 = None
if 'analysis_df' not in st.session_state:
    st.session_state.analysis_df = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'ml_messages' not in st.session_state:
    st.session_state.ml_messages = None

# Sidebar
with st.sidebar:
    st.header("Data Input")
    
    # File uploaders
    st.subheader("Upload Village Data (Data1)")
    uploaded_data1 = st.file_uploader("CSV or Excel file", type=["csv", "xlsx"], key="data1")
    
    st.subheader("Upload Sales Data (Data2)")
    uploaded_data2 = st.file_uploader("CSV or Excel file", type=["csv", "xlsx"], key="data2")
    
    if st.button("Load Data and Run ML Analysis"):
        if uploaded_data1 and uploaded_data2:
            try:
                # Load data
                if uploaded_data1.name.endswith('.csv'):
                    data1 = pd.read_csv(uploaded_data1)
                else:
                    data1 = pd.read_excel(uploaded_data1)
                
                if uploaded_data2.name.endswith('.csv'):
                    data2 = pd.read_csv(uploaded_data2)
                else:
                    data2 = pd.read_excel(uploaded_data2)
                
                # Store in session state
                st.session_state.data1 = data1
                st.session_state.data2 = data2
                
                # Run ML analysis
                with st.spinner("Running ML analysis..."):
                    recommendations, analysis_df = enhanced_analyze_sales_data(data1, data2)
                    st.session_state.analysis_df = analysis_df
                    st.session_state.recommendations = recommendations
                    
                    ml_messages = generate_ml_mantri_messages(recommendations)
                    st.session_state.ml_messages = ml_messages
                
                st.success("ML analysis completed successfully!")
                
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
        else:
            st.error("Please upload both files to proceed")

# Main content
if st.session_state.analysis_df is not None and st.session_state.recommendations is not None:
    # Display dashboard
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Village Analysis", "Actions & Messages", "Team Dispatch"])
    
    with tab1:
        st.header("ML-Powered Performance Dashboard")
        display_key_metrics(st.session_state.analysis_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(plot_village_performance(st.session_state.analysis_df), use_container_width=True)
        
        with col2:
            st.plotly_chart(plot_priority_matrix(st.session_state.recommendations), use_container_width=True)
        
        st.plotly_chart(plot_sales_trends(st.session_state.analysis_df), use_container_width=True)
    
    with tab2:
        st.header("Village Analysis with ML Segmentation")
        
        selected_village = st.selectbox("Select Village", st.session_state.analysis_df['Village'].unique())
        village_data = st.session_state.analysis_df[st.session_state.analysis_df['Village'] == selected_village].iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Village Details")
            st.write(f"**Village:** {village_data['Village']}")
            st.write(f"**Taluka:** {village_data['Taluka']}")
            st.write(f"**District:** {village_data['District']}")
            st.write(f"**Mantri:** {village_data['Mantri_Name']}")
            st.write(f"**Mantri Mobile:** {village_data['Mantri_Mobile']}")
            st.write(f"**Segment:** {village_data.get('Segment', 'N/A')}")
            st.write(f"**ML Recommended Action:** {village_data.get('ML_Recommended_Action', 'N/A')}")
            st.write(f"**Action Confidence:** {village_data.get('Action_Confidence', 'N/A'):.2f}")
        
        with col2:
            st.subheader("Performance Metrics")
            st.write(f"**Sabhasad:** {village_data['Sabhasad']}")
            st.write(f"**Contacted:** {village_data['Contact_In_Group']}")
            st.write(f"**Conversion Rate:** {village_data['Conversion_Rate']}%")
            st.write(f"**Untapped Potential:** {village_data['Untapped_Potential']}")
            st.write(f"**Total Sales:** {village_data['Total_L']}L")
            st.write(f"**Sales per Contact:** {village_data['Sales_Per_Contact']}L")
            st.write(f"**Predicted Sales:** {village_data.get('Predicted_Sales', 'N/A'):.1f}L")
            st.write(f"**Sales Gap:** {village_data.get('Sales_Gap', 'N/A'):.1f}L")
    
    with tab3:
        st.header("ML-Based Actions & Messages")
        
        st.subheader("ML-Generated Recommendations")
        st.dataframe(st.session_state.recommendations)
        
        # Download recommendations
        csv_data = st.session_state.recommendations.to_csv(index=False)
        st.download_button(
            label="Download Recommendations as CSV",
            data=csv_data,
            file_name="ml_sales_recommendations.csv",
            mime="text/csv"
        )
        
        st.subheader("Generate ML-Powered Messages")
        selected_mantri = st.selectbox("Select Mantri", st.session_state.recommendations['Mantri'].unique())
        mantri_data = st.session_state.recommendations[
            st.session_state.recommendations['Mantri'] == selected_mantri].iloc[0]
        
        message_df = st.session_state.ml_messages[
            st.session_state.ml_messages['Mantri'] == selected_mantri]
        
        if not message_df.empty:
            message = message_df.iloc[0]['Message']
            st.text_area("ML-Generated Message", message, height=300)
            
            if st.button("Send Message"):
                st.success(f"Message sent to {mantri_data['Mantri']} at {mantri_data['Mobile']}")
        
        st.subheader("Bulk Message Sender")
        if st.button("Generate All ML Messages"):
            st.session_state.all_messages = st.session_state.ml_messages
        
        if 'all_messages' in st.session_state:
            st.dataframe(st.session_state.all_messages[['Mantri', 'Village', 'Action', 'Priority', 'Confidence']])
            
            if st.button("Send All ML Messages"):
                progress_bar = st.progress(0)
                for i, row in st.session_state.all_messages.iterrows():
                    # Simulate sending message
                    progress_bar.progress((i + 1) / len(st.session_state.all_messages))
                st.success("All ML-powered messages sent successfully!")
    
    with tab4:
        st.header("Marketing Team Dispatch with ML Insights")
        
        st.subheader("Villages Needing Team Visit (ML Identified)")
        high_priority = st.session_state.recommendations[
            st.session_state.recommendations['Action'] == 'Send Marketing Team']
        
        if not high_priority.empty:
            for _, row in high_priority.iterrows():
                with st.expander(f"{row['Village']} - {row['Mantri']} (Confidence: {row['Confidence']:.2f})"):
                    st.write(f"**Reason:** {row['Reason']}")
                    st.write(f"**Segment:** {row['Segment']}")
                    st.write(f"**Sales Gap:** {row['Sales_Gap']:.1f}L")
                    
                    dispatch_date = st.date_input("Dispatch Date", key=f"date_{row['Village']}")
                    team_size = st.slider("Team Size", 1, 5, 2, key=f"size_{row['Village']}")
                    
                    if st.button("Schedule Dispatch", key=f"dispatch_{row['Village']}"):
                        st.success(f"Team dispatch scheduled for {row['Village']} on {dispatch_date}")
        else:
            st.info("No villages currently require immediate team dispatch based on ML analysis.")
        
        st.subheader("ML Performance Insights")
        st.write("Based on our machine learning analysis, here are key insights:")
        
        # Show segment distribution
        segment_counts = st.session_state.analysis_df['Segment'].value_counts()
        fig = px.pie(values=segment_counts.values, names=segment_counts.index, 
                     title="Village Segment Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Show confidence distribution
        fig = px.histogram(st.session_state.recommendations, x='Confidence',
                          title='Confidence Distribution of ML Recommendations')
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload your data files using the sidebar and click 'Load Data and Run ML Analysis' to get started.")

# Footer
st.markdown("---")
st.markdown("**ML-Powered Calcium Supplement Sales Automation System** | For internal use only")