# pages/distributors.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
# pages/distributors.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def show_distributors_page(db, whatsapp_manager=None):
    """Show intelligent distributors network optimization hub"""
    st.title("🤝 Distributor Network Intelligence")
    
    if not db:
        st.error("Database not available. Please check initialization.")
        return
    
    # Tabs for different distributor functions
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏆 Performance Dashboard", "➕ Add New Distributor", 
                                           "🗺️ Territory Analysis", "📈 Growth Opportunities", 
                                           "👥 Team Management", "🔍 Distributor Directory"])
    
    with tab1:
        show_performance_dashboard_tab(db)
    
    with tab2:
        show_add_distributor_tab(db, whatsapp_manager)
    
    with tab3:
        show_territory_analysis_tab(db)
    
    with tab4:
        show_growth_opportunities_tab(db)
    
    with tab5:
        show_team_management_tab(db, whatsapp_manager)
    
    with tab6:
        show_distributor_directory_tab(db)

def show_add_distributor_tab(db, whatsapp_manager):
    """Show form to add new distributors with comprehensive data collection"""
    st.subheader("➕ Add New Distributor")
    
    with st.form("add_distributor_form", clear_on_submit=True):
        st.markdown("### 📋 Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            distributor_name = st.text_input("Distributor Name*", placeholder="Enter distributor name")
            village = st.text_input("Village*", placeholder="Enter village name")
            taluka = st.text_input("Taluka*", placeholder="Enter taluka name")
            district = st.text_input("District", placeholder="Enter district name")
        
        with col2:
            mantri_name = st.text_input("Mantri Name*", placeholder="Enter mantri name")
            mantri_mobile = st.text_input("Mantri Mobile*", placeholder="Enter 10-digit mobile number")
            # Remove status for now since your function doesn't have it
            # status = st.selectbox("Status", ["Active", "Inactive", "Prospective"], index=0)
        
        st.markdown("### 📊 Network Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sabhasad_count = st.number_input("Current Sabhasad Count", min_value=0, value=0)
            contact_in_group = st.number_input("Contacts in WhatsApp Group", min_value=0, value=0)
        
        with col2:
            potential_sabhasad = st.number_input("Potential Sabhasad (6 months)", min_value=0, value=0)
            market_coverage = st.slider("Market Coverage (%)", 0, 100, 50)
        
        # Quick duplicate check
        if distributor_name and village and taluka:
            if db.distributor_exists(distributor_name, village, taluka):
                st.warning("⚠️ A distributor with this name already exists in this location!")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Add Distributor to Network", type="primary")
        
        if submitted:
            # Validation
            errors = []
            if not distributor_name:
                errors.append("Distributor name is required")
            if not village:
                errors.append("Village is required")
            if not taluka:
                errors.append("Taluka is required")
            if not mantri_name:
                errors.append("Mantri name is required")
            if not mantri_mobile or len(mantri_mobile) < 10:
                errors.append("Valid mobile number is required (10 digits)")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                try:
                    # Add distributor to database - WITHOUT status parameter
                    distributor_id = db.add_distributor(
                        name=distributor_name,
                        village=village,
                        taluka=taluka,
                        district=district,
                        mantri_name=mantri_name,
                        mantri_mobile=mantri_mobile,
                        sabhasad_count=sabhasad_count,
                        contact_in_group=contact_in_group
                        # status=status  # Remove this line since your function doesn't have it
                    )
                    
                    if distributor_id and distributor_id > 0:
                        st.success(f"✅ Distributor '{distributor_name}' added successfully!")
                        
                        # Store additional metrics
                        save_distributor_metrics(db, distributor_id, {
                            'potential_sabhasad': potential_sabhasad,
                            'market_coverage': market_coverage,
                            'notes': "Added via distributor form"
                        })
                        
                        # Show success summary
                        show_distributor_summary(db, distributor_id)
                        
                        # Send welcome message
                        if whatsapp_manager and mantri_mobile:
                            send_welcome_message(whatsapp_manager, mantri_mobile, distributor_name)
                    
                    else:
                        st.error("❌ Failed to add distributor. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Error adding distributor: {e}")

def calculate_potential_score(sabhasad_count, contact_in_group, potential_sabhasad,
                            market_coverage, leadership_quality, community_influence,
                            business_experience, has_vehicle, digital_literacy):
    """Calculate distributor potential score (0-100)"""
    score = 0
    
    # Network factors (40%)
    score += min(sabhasad_count * 2, 20)  # Max 20 points for current sabhasad
    score += min(contact_in_group * 0.2, 10)  # Max 10 points for contacts
    score += min(potential_sabhasad * 1.5, 10)  # Max 10 points for potential
    
    # Market factors (20%)
    score += market_coverage * 0.2  # 20 points for coverage
    
    # Personal factors (25%)
    leadership_scores = {"Low": 0, "Medium": 5, "High": 8, "Very High": 10}
    score += leadership_scores.get(leadership_quality, 0)
    
    influence_scores = {"Low": 0, "Medium": 5, "High": 8, "Very High": 10}
    score += influence_scores.get(community_influence, 0)
    
    experience_scores = {"None": 0, "1-2 years": 2, "3-5 years": 3, "5+ years": 5}
    score += experience_scores.get(business_experience, 0)
    
    # Infrastructure factors (15%)
    if has_vehicle:
        score += 5
    digital_scores = {"Basic": 2, "Intermediate": 4, "Advanced": 6}
    score += digital_scores.get(digital_literacy, 0)
    
    return min(score, 100)

def save_distributor_metrics(db, distributor_id, metrics):
    """Save additional distributor metrics"""
    try:
        # Create metrics table if not exists
        db.execute_query('''
        CREATE TABLE IF NOT EXISTS distributor_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            distributor_id INTEGER,
            potential_sabhasad INTEGER,
            market_coverage INTEGER,
            monthly_target REAL,
            current_business_value REAL,
            has_vehicle BOOLEAN,
            vehicle_type TEXT,
            storage_capacity TEXT,
            whatsapp_active BOOLEAN,
            digital_literacy TEXT,
            uses_app BOOLEAN,
            business_experience TEXT,
            sales_background BOOLEAN,
            leadership_quality TEXT,
            community_influence TEXT,
            known_in_village BOOLEAN,
            reference_source TEXT,
            potential_score REAL,
            notes TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (distributor_id) REFERENCES distributors (distributor_id) ON DELETE CASCADE
        )
        ''', log_action=False)
        
        # Insert metrics
        db.execute_query('''
        INSERT INTO distributor_metrics (
            distributor_id, potential_sabhasad, market_coverage, monthly_target,
            current_business_value, has_vehicle, vehicle_type, storage_capacity,
            whatsapp_active, digital_literacy, uses_app, business_experience,
            sales_background, leadership_quality, community_influence, known_in_village,
            reference_source, potential_score, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            distributor_id, metrics['potential_sabhasad'], metrics['market_coverage'],
            metrics['monthly_target'], metrics['current_business_value'],
            metrics['has_vehicle'], metrics['vehicle_type'], metrics['storage_capacity'],
            metrics['whatsapp_active'], metrics['digital_literacy'], metrics['uses_app'],
            metrics['business_experience'], metrics['sales_background'],
            metrics['leadership_quality'], metrics['community_influence'],
            metrics['known_in_village'], metrics['reference_source'],
            metrics['potential_score'], metrics['notes']
        ), log_action=False)
        
    except Exception as e:
        st.warning(f"Could not save additional metrics: {e}")

def show_distributor_summary(name, village, taluka, mantri_name, sabhasad_count, 
                           contact_in_group, potential_sabhasad, potential_score, monthly_target):
    """Show summary of newly added distributor"""
    st.markdown("## 🎉 Distributor Added Successfully!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Basic Information")
        st.write(f"**Name:** {name}")
        st.write(f"**Village:** {village}")
        st.write(f"**Taluka:** {taluka}")
        st.write(f"**Mantri:** {mantri_name}")
    
    with col2:
        st.subheader("📊 Network Metrics")
        st.write(f"**Current Sabhasad:** {sabhasad_count}")
        st.write(f"**WhatsApp Contacts:** {contact_in_group}")
        st.write(f"**Potential Sabhasad:** {potential_sabhasad}")
        st.write(f"**Monthly Target:** ₹{monthly_target:,.0f}")
    
    st.subheader("🎯 Potential Assessment")
    
    # Potential score visualization
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Create gauge chart for potential score
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = potential_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Potential Score"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "gray"},
                    {'range': [70, 100], 'color': "lightblue"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Action recommendations based on score
    st.subheader("💡 Recommended Actions")
    
    if potential_score >= 80:
        st.success("**🎯 High Potential Distributor**")
        st.write("- Provide advanced training materials")
        st.write("- Set ambitious growth targets")
        st.write("- Consider for leadership role")
        st.write("- Regular high-level engagement")
    
    elif potential_score >= 60:
        st.info("**📈 Good Potential Distributor**")
        st.write("- Standard training program")
        st.write("- Moderate growth targets")
        st.write("- Regular follow-ups")
        st.write("- Support with marketing materials")
    
    elif potential_score >= 40:
        st.warning("**🔄 Moderate Potential Distributor**")
        st.write("- Basic training focus")
        st.write("- Conservative targets")
        st.write("- Close monitoring needed")
        st.write("- Additional support required")
    
    else:
        st.error("**⚠️ Needs Development**")
        st.write("- Intensive training program")
        st.write("- Small, achievable targets")
        st.write("- Frequent check-ins")
        st.write("- Consider mentorship")

def send_welcome_message(whatsapp_manager, mobile, distributor_name):
    """Send welcome message to new distributor"""
    try:
        message = f"""Welcome {distributor_name}! 🎉

Thank you for joining our distributor network! 

We're excited to have you on board and look forward to working together to grow your business.

Our team will contact you shortly to discuss:
• Training schedule
• Product information  
• Sales strategies
• Support systems

For any immediate queries, feel free to contact us.

Best regards,
Sales Team"""

        success = whatsapp_manager.send_message(mobile, message)
        if success:
            st.success("📱 Welcome message sent to distributor!")
        else:
            st.warning("⚠️ Could not send welcome message")
    
    except Exception as e:
        st.warning(f"Could not send welcome message: {e}")

# Keep all your existing functions (show_performance_dashboard_tab, show_territory_analysis_tab, etc.)
# ... [rest of your existing functions remain unchanged]

def show_performance_dashboard_tab(db):
    """Show distributor performance dashboard"""
    st.subheader("🏆 Distributor Performance Dashboard")
    
    try:
        distributors_data = get_distributor_analytics_data(db)
        
        if distributors_data.empty:
            st.info("No distributor data available yet.")
            return
        
    except:
        pass
def show_distributors_page(db, whatsapp_manager=None):
    """Show intelligent distributors network optimization hub"""
    st.title("🤝 Distributor Network Intelligence")
    
    if not db:
        st.error("Database not available. Please check initialization.")
        return
    
    # Tabs for different distributor functions
    tab1, tab2, tab3, tab4, tab5 ,tab6= st.tabs(["🏆 Performance Dashboard", "🗺️ Territory Analysis", 
                                           "📈 Growth Opportunities", "👥 Team Management", 
                                           "🔍 Distributor Directory","➕Add new distributor"])
    
    with tab1:
        show_performance_dashboard_tab(db)
    
    with tab2:
        show_territory_analysis_tab(db)
    
    with tab3:
        show_growth_opportunities_tab(db)
    
    with tab4:
        show_team_management_tab(db, whatsapp_manager)
    
    with tab5:
        show_distributor_directory_tab(db)
    
    with tab6:
        show_add_distributor_tab(db)

def show_performance_dashboard_tab(db):
    """Show distributor performance dashboard"""
    st.subheader("🏆 Distributor Performance Dashboard")
    
    try:
        distributors_data = get_distributor_analytics_data(db)
        
        if distributors_data.empty:
            st.info("No distributor data available yet.")
            return
        
        # Key Performance Indicators
        st.subheader("🎯 Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_distributors = len(distributors_data)
            st.metric("Total Distributors", total_distributors)
        
        with col2:
            active_distributors = len(distributors_data[distributors_data['total_customers'] > 0])
            st.metric("Active Distributors", active_distributors)
        
        with col3:
            avg_sabhasad_per_dist = distributors_data['sabhasad_count'].mean()
            st.metric("Avg Sabhasad/Dist", f"{avg_sabhasad_per_dist:.1f}")
        
        with col4:
            total_network_size = distributors_data['sabhasad_count'].sum() + total_distributors
            st.metric("Total Network Size", total_network_size)
        
        # Performance Tiers
        st.subheader("📊 Performance Tiers")
        
        # Define performance tiers based on sabhasad count
        distributors_data['performance_tier'] = distributors_data['sabhasad_count'].apply(
            lambda x: 'Platinum' if x >= 20 else 'Gold' if x >= 10 else 'Silver' if x >= 5 else 'Bronze'
        )
        
        tier_stats = distributors_data['performance_tier'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(values=tier_stats.values, names=tier_stats.index,
                        title='Distributor Performance Tier Distribution',
                        color=tier_stats.index,
                        color_discrete_map={'Platinum': '#FFD700', 'Gold': '#C0C0C0', 
                                          'Silver': '#CD7F32', 'Bronze': '#8C7853'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top performers
            top_performers = distributors_data.nlargest(5, 'sabhasad_count')[
                ['name', 'village', 'sabhasad_count', 'contact_in_group']
            ]
            top_performers.columns = ['Distributor', 'Village', 'Sabhasad', 'Contacts']
            
            st.write("**🏅 Top 5 Performers**")
            st.dataframe(top_performers, use_container_width=True)
        
        # Geographic Performance Heatmap
        st.subheader("🗺️ Geographic Performance Distribution")
        
        village_performance = distributors_data.groupby('village').agg({
            'distributor_id': 'count',
            'sabhasad_count': 'sum',
            'contact_in_group': 'sum'
        }).reset_index()
        village_performance.columns = ['Village', 'Distributors', 'Total Sabhasad', 'Total Contacts']
        village_performance = village_performance.sort_values('Total Sabhasad', ascending=False)
        
        if not village_performance.empty:
            fig = px.bar(village_performance.head(10), x='Village', y='Total Sabhasad',
                       title='Top 10 Villages by Sabhasad Network Size',
                       color='Total Sabhasad',
                       labels={'Total Sabhasad': 'Sabhasad Count'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance Trends (if we had date data)
        st.subheader("📈 Network Growth Potential")
        
        # Calculate network density score
        distributors_data['network_score'] = (
            distributors_data['sabhasad_count'] * 0.6 + 
            distributors_data['contact_in_group'] * 0.4
        )
        
        # Identify high-potential distributors
        high_potential = distributors_data[
            (distributors_data['sabhasad_count'] < 10) & 
            (distributors_data['contact_in_group'] > 20)
        ]
        
        if not high_potential.empty:
            st.write(f"**💎 {len(high_potential)} High-Potential Distributors Identified**")
            st.write("These distributors have good contact base but low sabhasad conversion")
            st.dataframe(high_potential[['name', 'village', 'sabhasad_count', 'contact_in_group']], 
                        use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading performance dashboard: {e}")

def show_territory_analysis_tab(db):
    """Show territory coverage and gap analysis"""
    st.subheader("🗺️ Territory Coverage Analysis")
    
    try:
        distributors_data = get_distributor_analytics_data(db)
        customers_data = get_customer_analytics_data(db)
        
        if distributors_data.empty or customers_data.empty:
            st.info("Insufficient data for territory analysis.")
            return
        
        # Territory Coverage Analysis
        st.subheader("📍 Coverage Gap Analysis")
        
        # Get all villages with distributors vs all villages with customers
        distributor_villages = set(distributors_data['village'].dropna().unique())
        customer_villages = set(customers_data['village'].dropna().unique())
        
        # Coverage analysis
        covered_villages = distributor_villages.intersection(customer_villages)
        uncovered_villages = customer_villages - distributor_villages
        distributor_only_villages = distributor_villages - customer_villages
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Covered Villages", len(covered_villages))
        
        with col2:
            st.metric("Uncovered Villages", len(uncovered_villages))
        
        with col3:
            st.metric("Distributor-Only Villages", len(distributor_only_villages))
        
        # Coverage visualization
        col1, col2 = st.columns(2)
        
        with col1:
            coverage_data = {
                'Category': ['Covered', 'Uncovered', 'Distributor Only'],
                'Count': [len(covered_villages), len(uncovered_villages), len(distributor_only_villages)]
            }
            coverage_df = pd.DataFrame(coverage_data)
            
            fig = px.pie(coverage_df, values='Count', names='Category',
                        title='Village Coverage Status',
                        color='Category',
                        color_discrete_map={'Covered': '#00FF00', 'Uncovered': '#FF0000', 
                                          'Distributor Only': '#FFFF00'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Customer density in uncovered areas
            if uncovered_villages:
                uncovered_customers = customers_data[customers_data['village'].isin(uncovered_villages)]
                village_customer_count = uncovered_customers['village'].value_counts().head(10)
                
                if not village_customer_count.empty:
                    fig = px.bar(x=village_customer_count.index, y=village_customer_count.values,
                               title='Top Uncovered Villages by Customer Count',
                               labels={'x': 'Village', 'y': 'Customer Count'})
                    st.plotly_chart(fig, use_container_width=True)
        
        # Strategic Expansion Recommendations
        st.subheader("🎯 Strategic Expansion Recommendations")
        
        if uncovered_villages:
            # Prioritize villages with most customers
            expansion_priority = customers_data[customers_data['village'].isin(uncovered_villages)]
            priority_villages = expansion_priority.groupby('village').agg({
                'customer_id': 'count',
                'total_spent': 'sum'
            }).reset_index()
            priority_villages = priority_villages.sort_values('customer_id', ascending=False)
            
            st.write("**🚀 High-Priority Expansion Targets**")
            st.dataframe(priority_villages.head(10), use_container_width=True)
            
            # Expansion strategy
            st.write("**📋 Recommended Expansion Strategy**")
            
            high_priority = priority_villages[priority_villages['customer_id'] >= 10]
            medium_priority = priority_villages[(priority_villages['customer_id'] >= 5) & 
                                              (priority_villages['customer_id'] < 10)]
            
            if not high_priority.empty:
                st.success(f"**Immediate Action Needed:** {len(high_priority)} villages with 10+ customers need distributor coverage")
            
            if not medium_priority.empty:
                st.warning(f"**Plan Expansion:** {len(medium_priority)} villages with 5-9 customers ready for coverage")
        
        # Territory Optimization
        st.subheader("⚡ Territory Optimization")
        
        # Identify overcrowded territories
        village_distributor_count = distributors_data['village'].value_counts()
        overcrowded_villages = village_distributor_count[village_distributor_count > 2]
        
        if not overcrowded_villages.empty:
            st.write("**🏙️ Overcrowded Territories**")
            st.write("Consider redistributing some distributors from these villages:")
            for village, count in overcrowded_villages.items():
                st.write(f"- {village}: {count} distributors")
    
    except Exception as e:
        st.error(f"Error in territory analysis: {e}")

def show_growth_opportunities_tab(db):
    """Show growth opportunities and network expansion"""
    st.subheader("📈 Network Growth Opportunities")
    
    try:
        distributors_data = get_distributor_analytics_data(db)
        
        if distributors_data.empty:
            st.info("No distributor data available for growth analysis.")
            return
        
        # Growth Levers Analysis
        st.subheader("🎯 Growth Lever Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Sabhasad Conversion Opportunity
            avg_conversion_rate = distributors_data['sabhasad_count'].sum() / distributors_data['contact_in_group'].sum() * 100
            st.metric("Avg Contact to Sabhasad Rate", f"{avg_conversion_rate:.1f}%")
        
        with col2:
            # Underperforming distributors
            underperformers = len(distributors_data[distributors_data['sabhasad_count'] < 3])
            st.metric("Distributors Needing Support", underperformers)
        
        with col3:
            # Expansion potential
            total_contacts = distributors_data['contact_in_group'].sum()
            potential_sabhasad = total_contacts * 0.3  # Assuming 30% conversion potential
            st.metric("Potential Sabhasad Growth", f"+{potential_sabhasad:.0f}")
        
        # Growth Initiatives
        st.subheader("🚀 Growth Initiatives")
        
        initiative = st.selectbox("Select Growth Initiative",
                                ["Sabhasad Conversion Drive", "New Distributor Recruitment", 
                                 "Territory Expansion", "Performance Improvement Program"])
        
        if initiative == "Sabhasad Conversion Drive":
            show_sabhasad_conversion_plan(db, distributors_data)
        
        elif initiative == "New Distributor Recruitment":
            show_recruitment_plan(db, distributors_data)
        
        elif initiative == "Territory Expansion":
            show_territory_expansion_plan(db)
        
        elif initiative == "Performance Improvement Program":
            show_performance_improvement_plan(db, distributors_data)
        
        # Progress Tracking
        st.subheader("📊 Initiative Progress Tracking")
        
        # Mock progress data - in real implementation, this would come from database
        progress_data = {
            'Initiative': ['Sabhasad Drive', 'Recruitment', 'Territory Expansion', 'Training'],
            'Target': [50, 10, 5, 25],
            'Achieved': [35, 7, 3, 20],
            'Completion': [70, 70, 60, 80]
        }
        progress_df = pd.DataFrame(progress_data)
        
        fig = px.bar(progress_df, x='Initiative', y='Completion',
                   title='Growth Initiative Progress',
                   labels={'Completion': 'Completion %'},
                   color='Completion')
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error in growth opportunities analysis: {e}")

def show_sabhasad_conversion_plan(db, distributors_data):
    """Show sabhasad conversion growth plan"""
    st.write("### 📈 Sabhasad Conversion Drive")
    
    # Identify best candidates for conversion
    conversion_candidates = distributors_data[
        (distributors_data['contact_in_group'] > distributors_data['sabhasad_count'] * 2) &
        (distributors_data['contact_in_group'] >= 10)
    ].sort_values('contact_in_group', ascending=False)
    
    if not conversion_candidates.empty:
        st.write(f"**🎯 {len(conversion_candidates)} Distributors with High Conversion Potential**")
        
        for _, dist in conversion_candidates.head(5).iterrows():
            conversion_potential = dist['contact_in_group'] - dist['sabhasad_count']
            st.write(f"- **{dist['name']}** ({dist['village']}): {dist['sabhasad_count']} sabhasad, "
                   f"{dist['contact_in_group']} contacts → **+{conversion_potential} potential**")
        
        # Action plan
        st.write("**📋 Action Plan**")
        st.write("1. Conduct conversion training sessions")
        st.write("2. Provide conversion scripts and materials")
        st.write("3. Set weekly conversion targets")
        st.write("4. Implement incentive program for conversions")
    else:
        st.info("No high-potential conversion candidates identified.")

def show_recruitment_plan(db, distributors_data):
    """Show new distributor recruitment plan"""
    st.write("### 👥 New Distributor Recruitment")
    
    # Analyze current distribution density
    village_coverage = distributors_data['village'].value_counts()
    low_coverage_villages = village_coverage[village_coverage == 1]
    
    if not low_coverage_villages.empty:
        st.write("**📍 Villages Needing Additional Distributors**")
        for village in low_coverage_villages.index[:5]:
            st.write(f"- {village}")
    
    # Recruitment targets
    st.write("**🎯 Recruitment Strategy**")
    st.write("- Focus on high-customer-density uncovered villages")
    st.write("- Target influential community members")
    st.write("- Offer attractive onboarding incentives")
    st.write("- Provide comprehensive training and support")

def show_territory_expansion_plan(db):
    """Show territory expansion strategy"""
    st.write("### 🗺️ Territory Expansion Plan")
    
    # This would integrate with the territory analysis data
    st.write("**🚀 Expansion Priority Areas**")
    st.write("1. High customer density uncovered villages")
    st.write("2. Adjacent territories to high-performing distributors")
    st.write("3. Villages with existing brand awareness")
    st.write("4. Areas with competitor weakness")

def show_performance_improvement_plan(db, distributors_data):
    """Show performance improvement program"""
    st.write("### 📊 Performance Improvement Program")
    
    # Identify underperformers
    underperformers = distributors_data[
        (distributors_data['sabhasad_count'] < 5) &
        (distributors_data['status'] == 'Active')
    ]
    
    if not underperformers.empty:
        st.write(f"**🔧 {len(underperformers)} Distributors Needing Performance Support**")
        
        for _, dist in underperformers.head(5).iterrows():
            st.write(f"- **{dist['name']}** ({dist['village']}): {dist['sabhasad_count']} sabhasad")
        
        # Support plan
        st.write("**🛠️ Support Initiatives**")
        st.write("1. One-on-one coaching sessions")
        st.write("2. Performance benchmarking")
        st.write("3. Additional training resources")
        st.write("4. Peer mentoring program")

def show_team_management_tab(db, whatsapp_manager):
    """Show team communication and management"""
    st.subheader("👥 Team Management & Communication")
    
    try:
        distributors_data = get_distributor_analytics_data(db)
        
        if distributors_data.empty:
            st.info("No distributor data available for team management.")
            return
        
        # Communication Center
        st.subheader("📞 Communication Center")
        
        col1, col2 = st.columns(2)
        
        with col1:
            communication_type = st.selectbox("Communication Type",
                                            ["Performance Update", "Training Announcement", 
                                             "Incentive Program", "Urgent Meeting", "Custom Message"])
        
        with col2:
            target_group = st.selectbox("Target Group",
                                      ["All Distributors", "High Performers", "Underperformers",
                                       "Specific Village", "Performance Tier"])
        
        # Message templates
        message_templates = {
            "Performance Update": "Hello {name}! Your current performance: {sabhasad_count} sabhasad. Keep up the great work! 🎯",
            "Training Announcement": "Hello {name}! Training session this week. Learn new strategies to grow your network! 📚",
            "Incentive Program": "Hello {name}! New incentive program launched. Earn more with higher conversions! 💰",
            "Urgent Meeting": "Hello {name}! Urgent meeting tomorrow. Your attendance is important! ⏰",
            "Custom Message": ""
        }
        
        message = st.text_area("Message Content", 
                             value=message_templates[communication_type],
                             height=100)
        
        # Personalization options
        st.write("**🎨 Personalization Options**")
        col1, col2 = st.columns(2)
        
        with col1:
            include_performance = st.checkbox("Include Performance Data", value=True)
            include_village = st.checkbox("Include Village", value=True)
        
        with col2:
            urgent_tag = st.checkbox("Mark as Urgent", value=False)
            request_response = st.checkbox("Request Response", value=True)
        
        # Send communication
        if st.button("📱 Send to Distributors", type="primary"):
            # Filter target distributors
            target_distributors = filter_distributors_by_criteria(distributors_data, target_group)
            
            if not target_distributors.empty:
                st.success(f"✅ Ready to send message to {len(target_distributors)} distributors")
                
                # Show preview
                sample_dist = target_distributors.iloc[0]
                preview_message = personalize_message(message, sample_dist, include_performance, include_village)
                st.write("**Preview:**", preview_message)
            else:
                st.warning("No distributors match the selected criteria")
        
        # Team Performance Alerts
        st.subheader("🚨 Performance Alerts")
        
        # Low performers alert
        low_performers = distributors_data[
            (distributors_data['sabhasad_count'] < 3) &
            (distributors_data['status'] == 'Active')
        ]
        
        if not low_performers.empty:
            st.warning(f"🚨 {len(low_performers)} distributors have less than 3 sabhasad")
            if st.button("🔄 Schedule Support Calls"):
                st.info("Support calls scheduled with underperforming distributors")
        
        # High performer recognition
        high_performers = distributors_data[distributors_data['sabhasad_count'] >= 15]
        if not high_performers.empty:
            st.success(f"🏆 {len(high_performers)} elite performers with 15+ sabhasad")
            if st.button("🎉 Send Recognition"):
                st.info("Recognition messages sent to top performers")
    
    except Exception as e:
        st.error(f"Error in team management: {e}")

def show_distributor_directory_tab(db):
    """Show comprehensive distributor directory"""
    st.subheader("🔍 Distributor Directory")
    
    try:
        distributors_data = get_distributor_analytics_data(db)
        
        if distributors_data.empty:
            st.info("No distributors found in the database.")
            return
        
        # Advanced filtering
        st.subheader("🔍 Advanced Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            village_filter = st.multiselect("Filter by Village", distributors_data['village'].unique())
            performance_filter = st.selectbox("Performance Tier", 
                                            ["All", "Platinum", "Gold", "Silver", "Bronze"])
        
        with col2:
            sabhasad_min = st.number_input("Min Sabhasad", 0, 100, 0)
            sabhasad_max = st.number_input("Max Sabhasad", 0, 100, 100)
        
        with col3:
            status_filter = st.multiselect("Status", distributors_data['status'].unique(), 
                                         default=['Active'])
            search_term = st.text_input("Search by Name/Village")
        
        # Apply filters
        filtered_data = distributors_data.copy()
        
        if village_filter:
            filtered_data = filtered_data[filtered_data['village'].isin(village_filter)]
        
        if performance_filter != "All":
            filtered_data = filtered_data[filtered_data['performance_tier'] == performance_filter]
        
        filtered_data = filtered_data[
            (filtered_data['sabhasad_count'] >= sabhasad_min) &
            (filtered_data['sabhasad_count'] <= sabhasad_max)
        ]
        
        if status_filter:
            filtered_data = filtered_data[filtered_data['status'].isin(status_filter)]
        
        if search_term:
            filtered_data = filtered_data[
                filtered_data['name'].str.contains(search_term, case=False, na=False) |
                filtered_data['village'].str.contains(search_term, case=False, na=False)
            ]
        
        # Display results
        st.write(f"**Found {len(filtered_data)} distributors**")
        
        display_columns = ['name', 'village', 'taluka', 'mantri_name', 'sabhasad_count', 
                         'contact_in_group', 'performance_tier', 'status']
        display_df = filtered_data[display_columns]
        display_df.columns = ['Name', 'Village', 'Taluka', 'Mantri', 'Sabhasad', 'Contacts', 'Tier', 'Status']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Export options
        if st.button("📥 Export Distributor Data"):
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"distributors_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error loading distributor directory: {e}")

def get_distributor_analytics_data(db):
    """Get comprehensive distributor data with analytics"""
    try:
        distributors = db.get_dataframe('distributors', '''
        SELECT d.*,
               COUNT(DISTINCT c.customer_id) as total_customers,
               COALESCE(SUM(s.total_amount), 0) as territory_sales
        FROM distributors d
        LEFT JOIN customers c ON d.village = c.village AND d.taluka = c.taluka
        LEFT JOIN sales s ON c.customer_id = s.customer_id
        GROUP BY d.distributor_id
        ORDER BY d.sabhasad_count DESC
        ''')
        return distributors
    except Exception as e:
        st.error(f"Error loading distributor analytics data: {e}")
        return pd.DataFrame()

def get_customer_analytics_data(db):
    """Get customer data for territory analysis"""
    try:
        customers = db.get_dataframe('customers', "SELECT * FROM customers")
        return customers
    except Exception as e:
        return pd.DataFrame()

def filter_distributors_by_criteria(distributors_data, criteria):
    """Filter distributors based on selection criteria"""
    if criteria == "All Distributors":
        return distributors_data
    elif criteria == "High Performers":
        return distributors_data[distributors_data['sabhasad_count'] >= 10]
    elif criteria == "Underperformers":
        return distributors_data[distributors_data['sabhasad_count'] < 5]
    elif criteria == "Specific Village":
        # This would need a village selection UI in real implementation
        return distributors_data
    elif criteria == "Performance Tier":
        # This would need a tier selection UI
        return distributors_data
    return distributors_data

def personalize_message(message, distributor, include_performance=True, include_village=True):
    """Personalize message for distributor"""
    personalized = message.replace('{name}', distributor['name'])
    
    if include_performance and '{sabhasad_count}' in message:
        personalized = personalized.replace('{sabhasad_count}', str(distributor['sabhasad_count']))
    
    if include_village and '{village}' in message:
        personalized = personalized.replace('{village}', distributor.get('village', ''))
    
    return personalized