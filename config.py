# Configuration settings
import os

# Database configuration
DB_NAME = "sales_management.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)

# File paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

