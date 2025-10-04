import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_sales_data(data1, data2):
    """
    Analyze sales data to identify targets for mantri communication and village focus
    """
    
    # Convert date column if needed
    data1['Date'] = pd.to_datetime(data1['Date'])
    
    # Clean and preprocess data2
    data2['Date'] = pd.to_datetime(data2['Date'])
    
    # Calculate key metrics from Data1 (village level)
    data1['Conversion_Rate'] = (data1['Contact_In_Group'] / data1['Sabhasad'] * 100).round(2)
    data1['Conversion_Rate'] = data1['Conversion_Rate'].replace([np.inf, -np.inf], 0).fillna(0)
    data1['Untapped_Potential'] = data1['Sabhasad'] - data1['Contact_In_Group']
    data1['Sales_Per_Contact'] = (data1['Total_L'] / data1['Contact_In_Group']).round(2)
    data1['Sales_Per_Contact'] = data1['Sales_Per_Contact'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Calculate priority score for villages
    data1['Priority_Score'] = (
        (data1['Untapped_Potential'] / data1['Untapped_Potential'].max() * 50) +
        ((100 - data1['Conversion_Rate']) / 100 * 50)
    ).round(2)
    
    # Analyze recent sales from Data2 (customer level)
    # Since we don't have customer contact info, we'll analyze at village level
    recent_sales = data2.groupby('Village').agg({
        'Total_L': ['sum', 'count'],
        'Date': 'max'
    }).reset_index()
    
    # Flatten the column names
    recent_sales.columns = ['Village', 'Recent_Sales_L', 'Recent_Customers', 'Last_Sale_Date']
    
    # Calculate days since last sale
    recent_sales['Days_Since_Last_Sale'] = (datetime.now() - recent_sales['Last_Sale_Date']).dt.days
    
    # Merge with Data1
    analysis_df = data1.merge(recent_sales, on='Village', how='left')
    analysis_df['Recent_Sales_L'] = analysis_df['Recent_Sales_L'].fillna(0)
    analysis_df['Recent_Customers'] = analysis_df['Recent_Customers'].fillna(0)
    analysis_df['Days_Since_Last_Sale'] = analysis_df['Days_Since_Last_Sale'].fillna(999)
    
    # Generate recommendations for mantris
    recommendations = []
    
    for _, row in analysis_df.iterrows():
        village = row['Village']
        mantri = row['Mantri_Name']
        mobile = row['Mantri_Mobile']
        taluka = row['Taluka']
        district = row['District']
        
        # Recommendation logic
        if row['Conversion_Rate'] < 20:
            recommendations.append({
                'Village': village,
                'Taluka': taluka,
                'District': district,
                'Mantri': mantri,
                'Mobile': mobile,
                'Action': 'Send Marketing Team',
                'Reason': f'Low conversion rate ({row["Conversion_Rate"]:.1f}%) - Only {row["Contact_In_Group"]} of {row["Sabhasad"]} sabhasad contacted',
                'Priority': 'High',
                'Score': row['Priority_Score']
            })
        elif row['Untapped_Potential'] > 30:
            recommendations.append({
                'Village': village,
                'Taluka': taluka,
                'District': district,
                'Mantri': mantri,
                'Mobile': mobile,
                'Action': 'Call Mantri for Follow-up',
                'Reason': f'High untapped potential ({row["Untapped_Potential"]} sabhasad not contacted)',
                'Priority': 'High',
                'Score': row['Priority_Score']
            })
        elif row['Days_Since_Last_Sale'] > 30:
            recommendations.append({
                'Village': village,
                'Taluka': taluka,
                'District': district,
                'Mantri': mantri,
                'Mobile': mobile,
                'Action': 'Check on Mantri',
                'Reason': f'No recent sales ({row["Days_Since_Last_Sale"]} days since last sale)',
                'Priority': 'Medium',
                'Score': row['Priority_Score']
            })
        elif row['Sales_Per_Contact'] > 10:
            recommendations.append({
                'Village': village,
                'Taluka': taluka,
                'District': district,
                'Mantri': mantri,
                'Mobile': mobile,
                'Action': 'Provide More Stock',
                'Reason': f'High sales per contact ({row["Sales_Per_Contact"]}L per contact)',
                'Priority': 'Medium',
                'Score': row['Priority_Score']
            })
        else:
            recommendations.append({
                'Village': village,
                'Taluka': taluka,
                'District': district,
                'Mantri': mantri,
                'Mobile': mobile,
                'Action': 'Regular Follow-up',
                'Reason': 'Steady performance - maintain relationship',
                'Priority': 'Low',
                'Score': row['Priority_Score']
            })
    
    return pd.DataFrame(recommendations), analysis_df

def generate_mantri_messages(recommendations):
    """
    Generate personalized WhatsApp messages for mantris based on recommendations
    """
    messages = []
    
    for _, row in recommendations.iterrows():
        if row['Action'] == 'Send Marketing Team':
            message = f"""
Namaste {row['Mantri']} Ji!

Aapke kshetra {row['Village']} mein humare calcium supplement ki conversion rate kam hai. 
Humari marketing team aapke yaha demo dene aayegi. 
Kripya taiyaari rakhein aur sabhi dudh utpadakon ko soochit karein.

Dhanyavaad,
Calcium Supplement Team
"""
        elif row['Action'] == 'Call Mantri for Follow-up':
            message = f"""
Namaste {row['Mantri']} Ji!

Aapke kshetra {row['Village']} mein bahut se aise farmers hain jo abhi tak humare product se anabhijit hain. 
Kripya unse sampark karein aur unhe product ke fayde batayein. 
Aapke liye special commission offer hai agle 10 customers ke liye.

Dhanyavaad,
Calcium Supplement Team
"""
        elif row['Action'] == 'Check on Mantri':
            message = f"""
Namaste {row['Mantri']} Ji!

Humne dekha ki aapke kshetra {row['Village']} mein kuch samay se sales nahi hue hain.
Kya koi samasya hai? Kya hum aapki kisi tarah madad kar sakte hain?

Kripya hame batayein.

Dhanyavaad,
Calcium Supplement Team
"""
        elif row['Action'] == 'Provide More Stock':
            message = f"""
Namaste {row['Mantri']} Ji!

Badhai ho! Aapke kshetra {row['Village']} mein humare product ki demand badh rahi hai.
Kya aapko aur stock ki zaroorat hai? Hum jald se jald aapko extra stock bhej denge.

Dhanyavaad,
Calcium Supplement Team
"""
        else:
            message = f"""
Namaste {row['Mantri']} Ji!

Aapke kshetra {row['Village']} mein humare product ki sales theek chal rahi hain.
Kripya aise hi continue rakhein aur koi bhi sujhav ho toh hame batayein.

Dhanyavaad,
Calcium Supplement Team
"""
        
        messages.append({
            'Mantri': row['Mantri'],
            'Mobile': row['Mobile'],
            'Village': row['Village'],
            'Action': row['Action'],
            'Message': message,
            'Priority': row['Priority']
        })
    
    return pd.DataFrame(messages)

def identify_demo_locations(analysis_df, top_n=5):
    """
    Identify the best locations for demos based on various factors
    """
    # Calculate a demo score based on multiple factors
    analysis_df['Demo_Score'] = (
        (analysis_df['Untapped_Potential'] / analysis_df['Untapped_Potential'].max() * 40) +
        ((100 - analysis_df['Conversion_Rate']) / 100 * 30) +
        (analysis_df['Recent_Sales_L'] / analysis_df['Recent_Sales_L'].max() * 30)
    ).round(2)
    
    # Get top locations for demos
    demo_locations = analysis_df.nlargest(top_n, 'Demo_Score')[
        ['Village', 'Taluka', 'District', 'Mantri_Name', 'Mantri_Mobile', 
         'Conversion_Rate', 'Untapped_Potential', 'Demo_Score']
    ]
    
    return demo_locations

# Example usage with sample data structure
def main():
    # Sample data based on your new structure
    data2=pd.read_excel("sampletesting.xlsx",sheet_name="Sheet1")
    data1=pd.read_excel("sampletesting.xlsx",sheet_name="Sheet2")
    
    # Generate recommendations
    recommendations, analysis = analyze_sales_data(data1, data2)
    
    print("RECOMMENDED ACTIONS:")
    print(recommendations.sort_values('Score', ascending=False).to_string(index=False))
    
    # Generate messages for mantris
    mantri_messages = generate_mantri_messages(recommendations)
    
    print("\nMANTRI MESSAGES:")
    for _, msg in mantri_messages.iterrows():
        print(f"\nTo: {msg['Mantri']} ({msg['Mobile']}) - {msg['Village']}")
        print(f"Action: {msg['Action']}")
        print(f"Message: {msg['Message']}")
    
    # Identify demo locations
    demo_locations = identify_demo_locations(analysis)
    
    print("\nTOP DEMO LOCATIONS:")
    print(demo_locations.to_string(index=False))
    
    return recommendations, mantri_messages, demo_locations

if __name__ == "__main__":
    recommendations, mantri_messages, demo_locations = main()