from twilio.twiml.messaging_response import MessagingResponse
from src.models.location import Location
from src.services.location_service import location_service
from src.services.complaint_service import complaint_service
from src.utils.state_manager import state_manager

class WhatsAppService:
    def __init__(self):
        self.main_menu = (
            "📋 *Main Menu*\n\n"
            "1. View District\n"
            "2. View Municipality\n"
            "3. View Map\n"
            "4. Lodge Complaint\n"
            "5. Emergency Services\n\n"
            "Please type the number of your choice."
        )
    
    def create_response(self) -> MessagingResponse:
        return MessagingResponse()
    
    def handle_location(self, lat: float, lon: float, sender: str) -> str:
        location = location_service.get_location_from_coordinates(lat, lon)
        if not location:
            return "❌ Sorry, we couldn't identify your location. Please try again."
        
        state_manager.set_user_data(sender, 'location', location)
        state_manager.set_state(sender, 'in_location')
        
        response = "📍 *Your Location Information*\n\n"
        if location.province:
            response += f"Province: {location.province}\n"
        if location.district:
            response += f"District: {location.district}\n"
        if location.municipality:
            response += f"Municipality: {location.municipality}\n"
        
        response += f"\n{self.main_menu}"
        return response
    
    def handle_menu_choice(self, choice: str, sender: str) -> str:
        location = state_manager.get_user_data(sender, 'location')
        
        if choice == "1":
            if location and location.district:
                return f"📍 You are in {location.district}"
            return "❌ District information not available"
        
        elif choice == "2":
            if location and location.municipality:
                return f"🏛️ Your local municipality is {location.municipality}"
            return "❌ Municipality information not available"
        
        elif choice == "3":
            return "🗺️ Map functionality coming soon!"
        
        elif choice == "4":
            state_manager.set_state(sender, 'complaint_category')
            return complaint_service.get_complaint_menu()
        
        elif choice == "5":
            return complaint_service.get_emergency_services()
        
        else:
            return f"❌ Invalid choice. {self.main_menu}"
    
    def handle_complaint_category(self, choice: str, sender: str) -> str:
        if complaint_service.is_valid_complaint_choice(choice):
            complaint_type = complaint_service.get_complaint_type(choice)
            state_manager.set_user_data(sender, 'complaint_type', complaint_type)
            state_manager.set_state(sender, 'complaint_description')
            
            return (
                f"📝 You've selected: *{complaint_type}*\n\n"
                "Please describe your complaint in detail. "
                "You can also include an image if needed. 📸"
            )
        else:
            return f"❌ Invalid selection. {complaint_service.get_complaint_menu()}"
    
    def handle_complaint_description(self, description: str, sender: str) -> str:
        complaint_type = state_manager.get_user_data(sender, 'complaint_type')
        
        complaint = complaint_service.create_complaint(
            sender=sender,
            complaint_type=complaint_type,
            description=description
        )
        
        state_manager.set_state(sender, 'in_location')
        
        return (
            f"✅ *Complaint Submitted Successfully!*\n\n"
            f"**Type:** {complaint_type}\n"
            f"**Description:** {description}\n"
            f"**Reference ID:** {id(complaint)}\n\n"
            "Thank you for reporting this issue. "
            "Your complaint has been logged and will be addressed.\n\n"
            f"{self.main_menu}"
        )
    
    def handle_greeting(self) -> str:
        return (
            "👋 Welcome to Muni-Info!\n\n"
            "I help you access municipal information and services.\n\n"
            "📍 Please share your location to get started, "
            "or type 'menu' to see available options."
        )

whatsapp_service = WhatsAppService()