from typing import List, Dict, Any
from src.models.complaint import Complaint
from src.utils.geo_utils import load_emergency_services

class ComplaintService:
    COMPLAINT_TYPES = {
        "1": "Water",
        "2": "Electricity", 
        "3": "Sanitation",
        "4": "Roads",
        "5": "Other"
    }
    
    def __init__(self):
        self.complaints: List[Complaint] = []
    
    def get_complaint_menu(self) -> str:
        menu = "🎯 *Complaint Categories*\n\n"
        for key, value in self.COMPLAINT_TYPES.items():
            menu += f"{key}. {value}\n"
        menu += "\nPlease type the number of your complaint category."
        return menu
    
    def get_complaint_type(self, choice: str) -> str:
        return self.COMPLAINT_TYPES.get(choice, "Other")
    
    def is_valid_complaint_choice(self, choice: str) -> bool:
        return choice in self.COMPLAINT_TYPES
    
    def create_complaint(self, sender: str, complaint_type: str, description: str, image_url: str = None) -> Complaint:
        complaint = Complaint(
            sender=sender,
            complaint_type=complaint_type,
            description=description,
            image_url=image_url
        )
        self.complaints.append(complaint)
        return complaint
    
    def get_emergency_services(self) -> str:
        try:
            services = load_emergency_services()
            emergency_text = "🚨 *Emergency Services*\n\n"
            
            if 'emergency_numbers' in services:
                for service in services['emergency_numbers']:
                    emergency_text += f"{service.get('name', 'Service')}: {service.get('number', 'N/A')}\n"
            else:
                emergency_text += "Police: 10111\nAmbulance: 10177\nFire: 10177"
            
            return emergency_text
            
        except Exception as e:
            print(f"Error loading emergency services: {e}")
            return "🚨 *Emergency Services*\n\nPolice: 10111\nAmbulance: 10177\nFire: 10177"

complaint_service = ComplaintService()