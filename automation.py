# automation.py
import schedule
import time
from main import DatabaseManager, DataProcessor, SalesManager

def daily_tasks():
    db_manager = DatabaseManager()
    data_processor = DataProcessor(db_manager)
    sales_manager = SalesManager(db_manager, data_processor)
    
    # Track payments
    sales_manager.track_payments()
    
    # Schedule demo follow-ups
    sales_manager.schedule_demo_followups()
    
    print("Daily automation tasks completed!")

def weekly_reports():
    db_manager = DatabaseManager()
    data_processor = DataProcessor(db_manager)
    sales_manager = SalesManager(db_manager, data_processor)
    
    # Generate weekly report
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    report = sales_manager.generate_reports(start_date, end_date)
    # Email the report to management
    print("Weekly report generated!")

# Schedule tasks
schedule.every().day.at("09:00").do(daily_tasks)
schedule.every().monday.at("10:00").do(weekly_reports)

while True:
    schedule.run_pending()
    time.sleep(60)