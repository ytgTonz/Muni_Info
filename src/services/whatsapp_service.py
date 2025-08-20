from twilio.twiml.messaging_response import MessagingResponse
from src.models.location import Location
from src.models.complaint import ComplaintPriority
from src.services.location_service import location_service
from src.services.complaint_service import complaint_service
from src.services.language_service import language_service, Language
from src.services.notification_service import notification_service
from src.services.media_service import media_service
from src.utils.state_manager import state_manager
from src.config import Config
import re

class WhatsAppService:
    def __init__(self):
        pass
    
    def create_response(self) -> MessagingResponse:
        return MessagingResponse()
    
    def get_user_language(self, sender: str) -> Language:
        return state_manager.get_user_data(sender, 'language') or Language.ENGLISH
    
    def set_user_language(self, sender: str, language: Language):
        state_manager.set_user_data(sender, 'language', language)
    
    def handle_location(self, lat: float, lon: float, sender: str) -> str:
        location = location_service.get_location_from_coordinates(lat, lon)
        user_language = self.get_user_language(sender)
        
        if not location:
            return language_service.get_text('no_location', user_language)
        
        state_manager.set_user_data(sender, 'location', location)
        state_manager.set_state(sender, 'in_location')
        
        response = language_service.get_text('location_info', user_language,
            province=location.province or 'Unknown',
            district=location.district or 'Unknown', 
            municipality=location.municipality or 'Unknown'
        )
        
        response += f"\n\n{language_service.get_text('main_menu', user_language)}"
        return response
    
    def handle_menu_choice(self, choice: str, sender: str) -> str:
        location = state_manager.get_user_data(sender, 'location')
        user_language = self.get_user_language(sender)
        
        if choice == "1":
            if location and location.district:
                return f"📍 {location.district}"
            return language_service.get_text('error_occurred', user_language)
        
        elif choice == "2":
            if location and location.municipality:
                return f"🏦 {location.municipality}"
            return language_service.get_text('error_occurred', user_language)
        
        elif choice == "3":
            return "🗺️ Map functionality coming soon!"
        
        elif choice == "4":
            state_manager.set_state(sender, 'complaint_category')
            return language_service.get_text('complaint_categories', user_language)
        
        elif choice == "5":
            return language_service.get_text('emergency_services', user_language)
        
        elif choice == "6":
            complaints = complaint_service.get_user_complaints(sender)
            return self.format_complaints_history(complaints, user_language)
        
        elif choice == "7":
            state_manager.set_state(sender, 'language_selection')
            return language_service.get_text('language_selection', user_language)
        
        else:
            return f"{language_service.get_text('invalid_choice', user_language)}\n\n{language_service.get_text('main_menu', user_language)}"
    
    def handle_complaint_category(self, choice: str, sender: str) -> str:
        user_language = self.get_user_language(sender)
        
        if complaint_service.is_valid_complaint_choice(choice):
            complaint_type = complaint_service.get_complaint_type(choice)
            translated_type = language_service.get_complaint_type_translation(complaint_type, user_language)
            
            state_manager.set_user_data(sender, 'complaint_type', complaint_type)
            state_manager.set_state(sender, 'complaint_description')
            
            return language_service.get_text('complaint_description', user_language,
                complaint_type=translated_type
            )
        else:
            return f"{language_service.get_text('invalid_choice', user_language)}\n\n{language_service.get_text('complaint_categories', user_language)}"
    
    def handle_complaint_description(self, description: str, sender: str) -> str:
        complaint_type = state_manager.get_user_data(sender, 'complaint_type')
        location = state_manager.get_user_data(sender, 'location')
        user_language = self.get_user_language(sender)
        
        location_dict = location.to_dict() if location else None
        
        complaint = complaint_service.create_complaint(
            sender=sender,
            complaint_type=complaint_type,
            description=description,
            location_info=location_dict
        )
        
        # Send notification
        notification_service.notify_complaint_submitted(complaint, user_language.value)
        
        state_manager.set_state(sender, 'in_location')
        
        translated_type = language_service.get_complaint_type_translation(complaint_type, user_language)
        priority_display = language_service.get_priority_translation(complaint.priority.value, user_language)
        
        response = language_service.get_text('complaint_submitted', user_language,
            reference_id=complaint.reference_id,
            complaint_type=translated_type,
            priority=priority_display
        )
        
        response += f"\n\n{language_service.get_text('main_menu', user_language)}"
        return response
    
    def handle_greeting(self, sender: str) -> str:
        # Try to detect language from previous interactions or default to English
        user_language = self.get_user_language(sender)
        return language_service.get_text('welcome', user_language)
    
    def handle_language_selection(self, choice: str, sender: str) -> str:
        if language_service.is_valid_language_choice(choice):
            new_language = language_service.get_language_from_choice(choice)
            self.set_user_language(sender, new_language)
            state_manager.set_state(sender, 'in_location')
            
            response = language_service.get_text('language_changed', new_language)
            response += f"\n\n{language_service.get_text('main_menu', new_language)}"
            return response
        else:
            user_language = self.get_user_language(sender)
            return f"{language_service.get_text('invalid_choice', user_language)}\n\n{language_service.get_text('language_selection', user_language)}"
    
    def handle_reference_lookup(self, reference_id: str, sender: str) -> str:
        user_language = self.get_user_language(sender)
        complaint = complaint_service.get_complaint_by_reference(reference_id.upper())
        
        if complaint:
            translated_type = language_service.get_complaint_type_translation(complaint.complaint_type, user_language)
            return complaint_service.format_complaint_summary(complaint)
        else:
            return language_service.get_text('error_occurred', user_language)
    
    def format_complaints_history(self, complaints, user_language: Language) -> str:
        if not complaints:
            return language_service.get_text('no_complaints', user_language)
        
        complaints_list = ""
        for i, complaint in enumerate(complaints[:5], 1):
            translated_type = language_service.get_complaint_type_translation(complaint.complaint_type, user_language)
            status_display = complaint.get_status_display()
            complaints_list += f"{i}. **{complaint.reference_id}** - {translated_type}\n"
            complaints_list += f"   {status_display} | {complaint.timestamp.strftime('%d %b %Y')}\n"
            complaints_list += f"   _{complaint.description[:50]}{'...' if len(complaint.description) > 50 else ''}_\n\n"
        
        if len(complaints) > 5:
            complaints_list += f"... and {len(complaints) - 5} more complaints\n\n"
        
        return language_service.get_text('complaints_history', user_language,
            count=len(complaints),
            complaints_list=complaints_list
        )
    
    def handle_media_message(self, media_url: str, sender: str) -> str:
        user_language = self.get_user_language(sender)
        
        # Download and save media
        file_path = media_service.download_media_from_twilio(
            media_url, 
            Config.TWILIO_AUTH_TOKEN, 
            Config.TWILIO_ACCOUNT_SID
        )
        
        if file_path:
            # Check if user has a pending complaint to attach media to
            current_state = state_manager.get_state(sender)
            if current_state == 'complaint_description':
                # This media is for the current complaint being created
                return "📸 Image received! Please describe your complaint."
            else:
                return "📸 Image received and saved."
        else:
            return "❌ Failed to process image. Please try again."
    
    def detect_reference_id(self, text: str) -> str:
        """Detect if text contains a reference ID pattern (MI-YYYY-XXXXXX)"""
        pattern = r'MI-\d{4}-\d{6}'
        match = re.search(pattern, text.upper())
        return match.group(0) if match else None

whatsapp_service = WhatsAppService()