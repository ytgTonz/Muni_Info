import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MAPIT_BASE_URL = "https://mapit.openup.org.za"
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # MongoDB Configuration
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://hamzaMaq:hamza_78674@cluster0.iewu6.mongodb.net/")
    MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "muni_info_db")
    
    # Google Maps API (optional - for enhanced geocoding)
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
    
    # Data file paths
    MUNICIPALITIES_DATA = "data/za_municipalities.json"
    EMERGENCY_SERVICES_DATA = "data/za_emergency_services.json"