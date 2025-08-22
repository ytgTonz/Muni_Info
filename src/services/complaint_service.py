from typing import List, Dict, Any, Optional
from src.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from src.services.mongodb_complaint_repository import mongodb_complaint_repository
from src.services.ai_service import ai_service
from src.utils.geo_utils import load_emergency_services

class ComplaintService:
    COMPLAINT_TYPES = {
        "1": "Water",
        "2": "Electricity", 
        "3": "Sanitation",
        "4": "Roads",
        "5": "Other"
    }
    
    PRIORITY_KEYWORDS = {
        ComplaintPriority.URGENT: ["emergency", "urgent", "critical", "dangerous", "life-threatening", "flooding", "fire", "electrical hazard"],
        ComplaintPriority.HIGH: ["major", "serious", "severe", "broken", "no water", "no electricity", "blocked"],
        ComplaintPriority.MEDIUM: ["repair", "fix", "maintenance", "problem", "issue"],
        ComplaintPriority.LOW: ["minor", "small", "cosmetic", "suggestion", "improvement"]
    }
    
    def __init__(self):
        self.repository = mongodb_complaint_repository
    
    def get_complaint_menu(self) -> str:
        menu = "🎯 *Complaint Categories*\n\n"
        for key, value in self.COMPLAINT_TYPES.items():
            menu += f"{key}. {value}\n"
        menu += "\nPlease type the number of your complaint category."
        return menu
    
    def get_priority_selection_menu(self) -> str:
        menu = "⚡ *Priority Level*\n\n"
        menu += "1. 🔴 Urgent (Emergency/Safety Issue)\n"
        menu += "2. 🟠 High (Major Service Impact)\n"
        menu += "3. 🟡 Medium (Standard Issue)\n"
        menu += "4. 🟢 Low (Minor Issue)\n\n"
        menu += "Please select priority level (1-4), or skip to use auto-detection:"
        return menu
    
    def get_complaint_type(self, choice: str) -> str:
        return self.COMPLAINT_TYPES.get(choice, "Other")
    
    def is_valid_complaint_choice(self, choice: str) -> bool:
        return choice in self.COMPLAINT_TYPES
    
    def is_valid_priority_choice(self, choice: str) -> bool:
        return choice in ["1", "2", "3", "4"]
    
    def get_priority_from_choice(self, choice: str) -> ComplaintPriority:
        priority_map = {
            "1": ComplaintPriority.URGENT,
            "2": ComplaintPriority.HIGH,
            "3": ComplaintPriority.MEDIUM,
            "4": ComplaintPriority.LOW
        }
        return priority_map.get(choice, ComplaintPriority.MEDIUM)
    
    def auto_detect_priority(self, description: str) -> ComplaintPriority:
        description_lower = description.lower()
        
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            if any(keyword in description_lower for keyword in keywords):
                return priority
        
        return ComplaintPriority.MEDIUM
    
    def create_complaint(self, sender: str, complaint_type: str, description: str, 
                        priority: Optional[ComplaintPriority] = None,
                        location_info: Optional[dict] = None) -> Complaint:
        
        # Phase 3: AI-Enhanced Complaint Processing
        location_str = ""
        if location_info:
            location_str = f"{location_info.get('province', '')} {location_info.get('municipality', '')}"
        
        # Use AI service for intelligent analysis
        ai_analysis = ai_service.analyze_complaint(description, location_str, complaint_type)
        
        # Override category if AI suggests a better one with high confidence
        if ai_analysis.confidence > 0.8 and ai_analysis.category != complaint_type:
            complaint_type = ai_analysis.category
        
        # Use AI priority if not manually specified
        if priority is None:
            priority_map = {
                'urgent': ComplaintPriority.URGENT,
                'high': ComplaintPriority.HIGH,
                'medium': ComplaintPriority.MEDIUM,
                'low': ComplaintPriority.LOW
            }
            priority = priority_map.get(ai_analysis.priority, ComplaintPriority.MEDIUM)
        
        complaint = Complaint(
            sender=sender,
            complaint_type=complaint_type,
            description=description,
            priority=priority,
            location_info=location_info
        )
        
        # Store AI analysis results in complaint metadata
        complaint.ai_analysis = {
            'category': ai_analysis.category,
            'category_confidence': ai_analysis.confidence,
            'detected_priority': ai_analysis.priority,
            'priority_confidence': ai_analysis.priority_confidence,
            'department': ai_analysis.department,
            'keywords': ai_analysis.keywords,
            'urgency_indicators': ai_analysis.urgency_indicators,
            'predicted_resolution_time': ai_service.predict_resolution_time(ai_analysis.category, ai_analysis.priority),
            'suggested_response': ai_analysis.suggested_response
        }
        
        return self.repository.save_complaint(complaint)
    
    def get_complaint_by_reference(self, reference_id: str) -> Optional[Complaint]:
        return self.repository.get_complaint_by_reference(reference_id)
    
    def get_user_complaints(self, sender: str) -> List[Complaint]:
        return self.repository.get_complaints_by_sender(sender)
    
    def update_complaint_status(self, reference_id: str, new_status: ComplaintStatus, notes: Optional[str] = None) -> Optional[Complaint]:
        return self.repository.update_complaint_status(reference_id, new_status, notes)
    
    def add_image_to_complaint(self, reference_id: str, image_url: str) -> Optional[Complaint]:
        complaint = self.repository.get_complaint_by_reference(reference_id)
        if complaint:
            complaint.add_image(image_url)
            return self.repository.save_complaint(complaint)
        return None
    
    def update_complaint(self, complaint: Complaint) -> Optional[Complaint]:
        """Update an existing complaint in the repository"""
        return self.repository.save_complaint(complaint)
    
    def format_complaint_summary(self, complaint: Complaint) -> str:
        summary = f"📋 *Complaint Summary*\n\n"
        summary += f"**Reference:** {complaint.reference_id}\n"
        summary += f"**Type:** {complaint.complaint_type}\n"
        summary += f"**Status:** {complaint.get_status_display()}\n"
        summary += f"**Priority:** {complaint.get_priority_display()}\n"
        summary += f"**Submitted:** {complaint.timestamp.strftime('%d %b %Y, %H:%M')}\n"
        
        if complaint.updated_at != complaint.timestamp:
            summary += f"**Last Updated:** {complaint.updated_at.strftime('%d %b %Y, %H:%M')}\n"
        
        summary += f"**Description:** {complaint.description}\n"
        
        if complaint.resolution_notes:
            summary += f"**Notes:** {complaint.resolution_notes}\n"
        
        if complaint.image_urls:
            summary += f"**Images:** {len(complaint.image_urls)} attached\n"
        
        return summary
    
    def format_complaints_history(self, complaints: List[Complaint]) -> str:
        if not complaints:
            return "📝 No complaints found for your number."
        
        history = f"📋 *Your Complaints History* ({len(complaints)} total)\n\n"
        
        for i, complaint in enumerate(complaints[:5], 1):
            history += f"{i}. **{complaint.reference_id}** - {complaint.complaint_type}\n"
            history += f"   {complaint.get_status_display()} | {complaint.timestamp.strftime('%d %b %Y')}\n"
            history += f"   _{complaint.description[:50]}{'...' if len(complaint.description) > 50 else ''}_\n\n"
        
        if len(complaints) > 5:
            history += f"... and {len(complaints) - 5} more complaints\n\n"
        
        history += "Reply with a reference number (e.g., MI-2024-123456) to view details."
        return history
    
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