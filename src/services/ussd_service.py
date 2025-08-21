"""
USSD Service for Muni-Info Phase 3
Provides USSD support for feature phones and improved accessibility
"""

from typing import Dict, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.models.complaint import ComplaintPriority
from src.services.complaint_service import ComplaintService
from src.services.location_service import location_service
from src.services.ai_service import ai_service

class USSDState(Enum):
    """USSD session states"""
    MAIN_MENU = "main_menu"
    COMPLAINT_CATEGORY = "complaint_category"
    COMPLAINT_DESCRIPTION = "complaint_description"
    COMPLAINT_LOCATION = "complaint_location"
    COMPLAINT_PRIORITY = "complaint_priority"
    COMPLAINT_CONFIRM = "complaint_confirm"
    STATUS_CHECK = "status_check"
    EMERGENCY_MENU = "emergency_menu"
    INFO_MENU = "info_menu"
    LANGUAGE_SELECT = "language_select"

@dataclass
class USSDSession:
    """USSD session data"""
    session_id: str
    phone_number: str
    state: USSDState
    data: Dict
    language: str = "en"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class USSDService:
    """USSD service for feature phone access"""
    
    def __init__(self):
        self.complaint_service = ComplaintService()
        self.sessions: Dict[str, USSDSession] = {}
        
        # Multi-language support
        self.messages = {
            'en': {
                'welcome': "Welcome to Muni-Info\n1. Lodge Complaint\n2. Check Status\n3. Emergency\n4. Information\n5. Language\n0. Exit",
                'complaint_menu': "Select Category:\n1. Water\n2. Electricity\n3. Sanitation\n4. Roads\n5. Housing\n6. Parks\n7. Other\n0. Back",
                'enter_description': "Describe your complaint in detail:\n(Type your complaint and send)",
                'location_options': "Location:\n1. Use my current area\n2. Enter manually\n0. Back",
                'priority_menu': "Priority Level:\n1. Emergency (Life threatening)\n2. Urgent (Major impact)\n3. Normal (Standard issue)\n4. Low (Minor issue)\n0. Back",
                'confirm_complaint': "Confirm Complaint:\nType: {category}\nArea: {location}\nPriority: {priority}\n\n1. Submit\n2. Edit\n0. Cancel",
                'complaint_submitted': "✅ Complaint submitted!\nReference: {reference}\n\nYou will receive SMS updates.\n\n1. Submit Another\n2. Main Menu\n0. Exit",
                'enter_reference': "Enter your complaint reference number:",
                'status_info': "Reference: {reference}\nStatus: {status}\nSubmitted: {date}\nPriority: {priority}\n\n1. Check Another\n2. Main Menu\n0. Exit",
                'emergency_menu': "🚨 EMERGENCY SERVICES 🚨\n1. Police: 10111\n2. Ambulance: 10177\n3. Fire: 10177\n4. Municipal Emergency\n\nFor life-threatening emergencies, CALL immediately!\n\n0. Back",
                'info_menu': "Information:\n1. Service Hours\n2. Contact Details\n3. Service Types\n4. How It Works\n0. Back",
                'language_menu': "Select Language:\n1. English\n2. Afrikaans\n3. isiZulu\n4. isiXhosa\n0. Back",
                'invalid_option': "Invalid option. Please try again.",
                'session_timeout': "Session expired. Please start again.",
                'error_occurred': "An error occurred. Please try again or contact support.",
                'complaint_not_found': "Complaint not found. Please check your reference number.",
                'goodbye': "Thank you for using Muni-Info. Stay safe!"
            },
            'af': {
                'welcome': "Welkom by Muni-Info\n1. Dien Klagte In\n2. Toets Status\n3. Noodgeval\n4. Inligting\n5. Taal\n0. Verlaat",
                'complaint_menu': "Kies Kategorie:\n1. Water\n2. Elektrisiteit\n3. Sanitasie\n4. Paaie\n5. Behuising\n6. Parke\n7. Ander\n0. Terug",
                'enter_description': "Beskryf jou klagte in detail:\n(Tik jou klagte en stuur)",
                'invalid_option': "Ongeldige opsie. Probeer asseblief weer.",
                'goodbye': "Dankie dat jy Muni-Info gebruik het. Bly veilig!"
            },
            'zu': {
                'welcome': "Sawubona ku-Muni-Info\n1. Nikela Isikhalazo\n2. Hlola Isimo\n3. Isiphuthuma\n4. Ulwazi\n5. Ulimi\n0. Phuma",
                'complaint_menu': "Khetha Uhlobo:\n1. Amanzi\n2. Ugesi\n3. Ucoceko\n4. Imigwaqo\n5. Izindlu\n6. Amapaki\n7. Okunye\n0. Emuva",
                'invalid_option': "Inketho engekho. Sicela uzame futhi.",
                'goodbye': "Siyabonga ngokusebenzisa i-Muni-Info. Zivikeleni!"
            },
            'xh': {
                'welcome': "Molo ku-Muni-Info\n1. Ngenisa Isikhalazo\n2. Khangela Imeko\n3. Ingxaki\n4. Inkcazelo\n5. Ulwimi\n0. Phuma",
                'complaint_menu': "Khetha Udidi:\n1. Amanzi\n2. Umbane\n3. Ucoceko\n4. Iindlela\n5. Izindlu\n6. Iipaki\n7. Ezinye\n0. Emva",
                'invalid_option': "Ukhetho olungekho. Nceda uzame kwakhona.",
                'goodbye': "Enkosi ngokusebenzisa i-Muni-Info. Zikhathalele!"
            }
        }
        
        # Category mappings
        self.categories = {
            '1': 'Water',
            '2': 'Electricity', 
            '3': 'Sanitation',
            '4': 'Roads',
            '5': 'Housing',
            '6': 'Parks',
            '7': 'Other'
        }
        
        # Priority mappings
        self.priorities = {
            '1': ComplaintPriority.URGENT,
            '2': ComplaintPriority.URGENT, 
            '3': ComplaintPriority.MEDIUM,
            '4': ComplaintPriority.LOW
        }
        
        # Language codes
        self.languages = {
            '1': 'en',
            '2': 'af',
            '3': 'zu', 
            '4': 'xh'
        }
    
    def process_ussd_request(self, session_id: str, phone_number: str, text: str) -> Tuple[str, bool]:
        """
        Process USSD request and return response
        Returns (response_text, continue_session)
        """
        try:
            # Get or create session
            session = self.get_or_create_session(session_id, phone_number, text)
            
            # Handle empty input (initial request)
            if text == "":
                return self.show_main_menu(session)
            
            # Process based on current state
            return self.process_state(session, text)
            
        except Exception as e:
            # Log error and return user-friendly message
            print(f"USSD Error: {e}")
            return self.get_message("error_occurred", "en"), False
    
    def get_or_create_session(self, session_id: str, phone_number: str, text: str) -> USSDSession:
        """Get existing session or create new one"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Check for timeout (5 minutes)
            if (datetime.now() - session.created_at).total_seconds() > 300:
                del self.sessions[session_id]
                return USSDSession(session_id, phone_number, USSDState.MAIN_MENU, {})
            return session
        else:
            session = USSDSession(session_id, phone_number, USSDState.MAIN_MENU, {})
            self.sessions[session_id] = session
            return session
    
    def process_state(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Process input based on current session state"""
        input_text = input_text.strip()
        
        if session.state == USSDState.MAIN_MENU:
            return self.handle_main_menu(session, input_text)
        elif session.state == USSDState.COMPLAINT_CATEGORY:
            return self.handle_complaint_category(session, input_text)
        elif session.state == USSDState.COMPLAINT_DESCRIPTION:
            return self.handle_complaint_description(session, input_text)
        elif session.state == USSDState.COMPLAINT_LOCATION:
            return self.handle_complaint_location(session, input_text)
        elif session.state == USSDState.COMPLAINT_PRIORITY:
            return self.handle_complaint_priority(session, input_text)
        elif session.state == USSDState.COMPLAINT_CONFIRM:
            return self.handle_complaint_confirm(session, input_text)
        elif session.state == USSDState.STATUS_CHECK:
            return self.handle_status_check(session, input_text)
        elif session.state == USSDState.EMERGENCY_MENU:
            return self.handle_emergency_menu(session, input_text)
        elif session.state == USSDState.INFO_MENU:
            return self.handle_info_menu(session, input_text)
        elif session.state == USSDState.LANGUAGE_SELECT:
            return self.handle_language_select(session, input_text)
        else:
            return self.show_main_menu(session)
    
    def show_main_menu(self, session: USSDSession) -> Tuple[str, bool]:
        """Show main USSD menu"""
        session.state = USSDState.MAIN_MENU
        message = self.get_message("welcome", session.language)
        return message, True
    
    def handle_main_menu(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle main menu selection"""
        if input_text == "1":  # Lodge Complaint
            session.state = USSDState.COMPLAINT_CATEGORY
            session.data = {}
            return self.get_message("complaint_menu", session.language), True
        elif input_text == "2":  # Check Status
            session.state = USSDState.STATUS_CHECK
            return self.get_message("enter_reference", session.language), True
        elif input_text == "3":  # Emergency
            session.state = USSDState.EMERGENCY_MENU
            return self.get_message("emergency_menu", session.language), True
        elif input_text == "4":  # Information
            session.state = USSDState.INFO_MENU
            return self.get_message("info_menu", session.language), True
        elif input_text == "5":  # Language
            session.state = USSDState.LANGUAGE_SELECT
            return self.get_message("language_menu", session.language), True
        elif input_text == "0":  # Exit
            self.cleanup_session(session.session_id)
            return self.get_message("goodbye", session.language), False
        else:
            return self.get_message("invalid_option", session.language) + "\n\n" + self.get_message("welcome", session.language), True
    
    def handle_complaint_category(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle complaint category selection"""
        if input_text in self.categories:
            session.data['category'] = self.categories[input_text]
            session.state = USSDState.COMPLAINT_DESCRIPTION
            return self.get_message("enter_description", session.language), True
        elif input_text == "0":  # Back
            return self.show_main_menu(session)
        else:
            return self.get_message("invalid_option", session.language) + "\n\n" + self.get_message("complaint_menu", session.language), True
    
    def handle_complaint_description(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle complaint description input"""
        if len(input_text.strip()) < 10:
            return "Please provide more details about your complaint (minimum 10 characters):", True
        
        session.data['description'] = input_text
        session.state = USSDState.COMPLAINT_LOCATION
        return self.get_message("location_options", session.language), True
    
    def handle_complaint_location(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle location input"""
        if input_text == "1":  # Use current area
            # For USSD, we'll use a default location or derive from phone number
            session.data['location'] = self.get_default_location(session.phone_number)
            session.state = USSDState.COMPLAINT_PRIORITY
            return self.get_message("priority_menu", session.language), True
        elif input_text == "2":  # Manual entry - simplified for USSD
            session.data['location'] = "Manual Location Entry"
            session.state = USSDState.COMPLAINT_PRIORITY
            return self.get_message("priority_menu", session.language), True
        elif input_text == "0":  # Back
            session.state = USSDState.COMPLAINT_DESCRIPTION
            return self.get_message("enter_description", session.language), True
        else:
            return self.get_message("invalid_option", session.language) + "\n\n" + self.get_message("location_options", session.language), True
    
    def handle_complaint_priority(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle priority selection"""
        if input_text in self.priorities:
            session.data['priority'] = self.priorities[input_text]
            session.state = USSDState.COMPLAINT_CONFIRM
            
            # Use AI to enhance the priority detection
            description = session.data.get('description', '')
            if description:
                ai_analysis = ai_service.analyze_complaint(description)
                # Override if AI suggests higher priority with high confidence
                if ai_analysis.priority_confidence > 0.8:
                    ai_priority_map = {
                        'urgent': ComplaintPriority.URGENT,
                        'high': ComplaintPriority.HIGH,
                        'medium': ComplaintPriority.MEDIUM,
                        'low': ComplaintPriority.LOW
                    }
                    ai_priority = ai_priority_map.get(ai_analysis.priority, session.data['priority'])
                    if ai_priority.value == 'urgent' and session.data['priority'].value != 'urgent':
                        session.data['priority'] = ai_priority
                        session.data['ai_adjusted'] = True
            
            return self.show_confirmation(session), True
        elif input_text == "0":  # Back
            session.state = USSDState.COMPLAINT_LOCATION
            return self.get_message("location_options", session.language), True
        else:
            return self.get_message("invalid_option", session.language) + "\n\n" + self.get_message("priority_menu", session.language), True
    
    def handle_complaint_confirm(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle complaint confirmation"""
        if input_text == "1":  # Submit
            return self.submit_complaint(session)
        elif input_text == "2":  # Edit
            session.state = USSDState.COMPLAINT_CATEGORY
            return self.get_message("complaint_menu", session.language), True
        elif input_text == "0":  # Cancel
            return self.show_main_menu(session)
        else:
            return self.get_message("invalid_option", session.language) + "\n\n" + self.show_confirmation(session)[0], True
    
    def handle_status_check(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle complaint status check"""
        reference = input_text.strip().upper()
        
        if input_text == "0":  # Back
            return self.show_main_menu(session)
        
        complaint = self.complaint_service.get_complaint_by_reference(reference)
        if complaint:
            status_message = self.get_message("status_info", session.language).format(
                reference=complaint.reference_id,
                status=complaint.get_status_display(),
                date=complaint.timestamp.strftime("%Y-%m-%d %H:%M"),
                priority=complaint.get_priority_display()
            )
            
            # Add AI insights if available
            if hasattr(complaint, 'ai_analysis') and complaint.ai_analysis:
                predicted_time = complaint.ai_analysis.get('predicted_resolution_time', '')
                if predicted_time:
                    status_message += f"\nEst. Resolution: {predicted_time}"
            
            return status_message, True
        else:
            return self.get_message("complaint_not_found", session.language) + "\n\n" + self.get_message("enter_reference", session.language), True
    
    def handle_emergency_menu(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle emergency menu"""
        if input_text == "4":  # Municipal Emergency
            session.data = {'category': 'Emergency', 'priority': ComplaintPriority.URGENT}
            session.state = USSDState.COMPLAINT_DESCRIPTION
            return "🚨 EMERGENCY COMPLAINT 🚨\nDescribe the emergency situation:", True
        elif input_text == "0":  # Back
            return self.show_main_menu(session)
        else:
            return self.get_message("emergency_menu", session.language), True
    
    def handle_info_menu(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle information menu"""
        if input_text == "1":  # Service Hours
            info = "Municipal Service Hours:\nMon-Fri: 08:00-16:30\nSat: 08:00-12:00\nSun: Closed\n\nEmergencies: 24/7\n\n0. Back"
            return info, True
        elif input_text == "2":  # Contact Details
            info = "Contact Details:\nCall Center: 080 MUNI (6864)\nEmail: help@muni-info.gov.za\nWhatsApp: +27 XX XXX XXXX\n\n0. Back"
            return info, True
        elif input_text == "3":  # Service Types
            info = "We handle complaints for:\n• Water & Sanitation\n• Electricity\n• Roads & Infrastructure\n• Housing\n• Parks & Recreation\n\n0. Back"
            return info, True
        elif input_text == "4":  # How It Works
            info = "How It Works:\n1. Lodge complaint via USSD/WhatsApp\n2. Get reference number\n3. Track progress\n4. Receive updates\n5. Rate service\n\n0. Back"
            return info, True
        elif input_text == "0":  # Back
            return self.show_main_menu(session)
        else:
            return self.get_message("info_menu", session.language), True
    
    def handle_language_select(self, session: USSDSession, input_text: str) -> Tuple[str, bool]:
        """Handle language selection"""
        if input_text in self.languages:
            session.language = self.languages[input_text]
            return self.show_main_menu(session)
        elif input_text == "0":  # Back
            return self.show_main_menu(session)
        else:
            return self.get_message("language_menu", session.language), True
    
    def show_confirmation(self, session: USSDSession) -> Tuple[str, bool]:
        """Show complaint confirmation"""
        data = session.data
        ai_note = " (AI-enhanced)" if data.get('ai_adjusted') else ""
        
        message = self.get_message("confirm_complaint", session.language).format(
            category=data.get('category', ''),
            location=data.get('location', ''),
            priority=data.get('priority', ComplaintPriority.MEDIUM).value.title() + ai_note
        )
        return message, True
    
    def submit_complaint(self, session: USSDSession) -> Tuple[str, bool]:
        """Submit the complaint"""
        try:
            data = session.data
            
            # Create location info
            location_info = {
                'municipality': data.get('location', 'Unknown'),
                'source': 'ussd'
            }
            
            # Submit complaint
            complaint = self.complaint_service.create_complaint(
                sender=session.phone_number,
                complaint_type=data['category'],
                description=data['description'],
                priority=data['priority'],
                location_info=location_info
            )
            
            # Success message
            message = self.get_message("complaint_submitted", session.language).format(
                reference=complaint.reference_id
            )
            
            return message, True
            
        except Exception as e:
            print(f"USSD Complaint submission error: {e}")
            return self.get_message("error_occurred", session.language), True
    
    def get_message(self, key: str, language: str = "en") -> str:
        """Get localized message"""
        messages = self.messages.get(language, self.messages['en'])
        return messages.get(key, self.messages['en'].get(key, "Message not found"))
    
    def get_default_location(self, phone_number: str) -> str:
        """Get default location based on phone number (simplified)"""
        # In a real implementation, you would use telecom provider APIs
        # or maintain a database of area codes to locations
        return "Default Area"
    
    def cleanup_session(self, session_id: str):
        """Clean up expired session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Clean up all expired sessions (call this periodically)"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if (current_time - session.created_at).total_seconds() > 300:  # 5 minutes
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]

# Global USSD service instance
ussd_service = USSDService()