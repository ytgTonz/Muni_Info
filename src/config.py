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
    
    # Google Maps API (optional - for enhanced geocoding)
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
    
    # Data file paths
    MUNICIPALITIES_DATA = "data/za_municipalities.json"
    EMERGENCY_SERVICES_DATA = "data/za_emergency_services.json"