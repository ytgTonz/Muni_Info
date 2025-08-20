from typing import Optional, Dict, Any, List
from twilio.rest import Client
from src.config import Config
from src.models.complaint import Complaint, ComplaintStatus
from datetime import datetime

class NotificationService:
    def __init__(self):
        self.client = None
        if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
            self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        self.templates = {
            'complaint_submitted': {
                'en': "✅ Complaint submitted successfully!\n\nReference: {reference_id}\nType: {complaint_type}\n\nWe'll update you on progress. Save this reference number.",
                'af': "✅ Klagte suksesvol ingedien!\n\nVerwysing: {reference_id}\nTipe: {complaint_type}\n\nOns sal u op hoogte hou van vordering. Stoor hierdie verwysingsnommer.",
                'zu': "✅ Isikhalazo sithunyelwe ngempumelelo!\n\nInkomba: {reference_id}\nUhlobo: {complaint_type}\n\nSizokwazisa ngenqubekela phambili. Gcina le nombolo yenkomba.",
                'xh': "✅ Isikhalazo sithunyezelwe ngempumelelo!\n\nIsalathiso: {reference_id}\nUhlobo: {complaint_type}\n\nSiza kukwazisa ngenkqubela phambili. Gcina eli nombolo lesalathiso."
            },
            'status_update': {
                'en': "📢 Update on your complaint {reference_id}\n\nStatus: {status}\nType: {complaint_type}\n\n{notes}",
                'af': "📢 Opdatering op u klagte {reference_id}\n\nStatus: {status}\nTipe: {complaint_type}\n\n{notes}",
                'zu': "📢 Isibuyekezo ngesikhalaze sakho {reference_id}\n\nIsimo: {status}\nUhlobo: {complaint_type}\n\n{notes}",
                'xh': "📢 Uhlaziyo lwesikhalazo sakho {reference_id}\n\nImeko: {status}\nUhlobo: {complaint_type}\n\n{notes}"
            },
            'complaint_resolved': {
                'en': "✅ Your complaint has been resolved!\n\nReference: {reference_id}\nType: {complaint_type}\n\nResolution: {notes}\n\nThank you for using Muni-Info!",
                'af': "✅ U klagte is opgelos!\n\nVerwysing: {reference_id}\nTipe: {complaint_type}\n\nOplossing: {notes}\n\nDankie dat u Muni-Info gebruik!",
                'zu': "✅ Isikhalazo sakho sixazululiwe!\n\nInkomba: {reference_id}\nUhlobo: {complaint_type}\n\nIsixazululo: {notes}\n\nSiyabonga ngokusebenzisa i-Muni-Info!",
                'xh': "✅ Isikhalazo sakho siyasombululiwe!\n\nIsalathiso: {reference_id}\nUhlobo: {complaint_type}\n\nIsisombululo: {notes}\n\nSiyabulela ngokusebenzisa i-Muni-Info!"
            },
            'welcome': {
                'en': "👋 Welcome to Muni-Info!\n\nWe help you access municipal services and lodge complaints.\n\n📍 Share your location to get started, or type 'menu' for options.",
                'af': "👋 Welkom by Muni-Info!\n\nOns help u om munisipale dienste te verkry en klagtes in te dien.\n\n📍 Deel u ligging om te begin, of tik 'menu' vir opsies.",
                'zu': "👋 Siyakwamukela ku-Muni-Info!\n\nSikusiza ukufinyelela izinsizakalo zamasipala nokufaka izikhalazo.\n\n📍 Yabelana ngendawo yakho ukuze uqale, noma uthayipe 'menu' ukuthola izinketho.",
                'xh': "👋 Wamkelekile ku-Muni-Info!\n\nSikunceda ukufikelela kwiinkonzo zikamasipala kunye nokufaka izikhalazo.\n\n📍 Yabelana ngendawo yakho ukuze uqale, okanye uthayiphe 'menu' ukufumana ezongezelelo."
            }
        }
    
    def send_sms(self, to_number: str, message: str, from_number: str = None) -> Optional[str]:
        if not self.client:
            print("Twilio client not initialized. Check your credentials.")
            return None
        
        try:
            if not from_number:
                from_number = "whatsapp:+1234567890"  # Configure your WhatsApp Business number
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            print(f"SMS sent successfully. SID: {message_obj.sid}")
            return message_obj.sid
            
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return None
    
    def send_whatsapp_message(self, to_number: str, message: str, from_number: str = None) -> Optional[str]:
        if not self.client:
            print("Twilio client not initialized. Check your credentials.")
            return None
        
        try:
            if not from_number:
                from_number = "whatsapp:+1234567890"  # Configure your WhatsApp Business number
            
            # Ensure the to_number has the whatsapp: prefix
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{to_number}"
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            print(f"WhatsApp message sent successfully. SID: {message_obj.sid}")
            return message_obj.sid
            
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return None
    
    def get_message_template(self, template_key: str, language: str = 'en', **kwargs) -> str:
        template = self.templates.get(template_key, {})
        message = template.get(language, template.get('en', ''))
        
        try:
            return message.format(**kwargs)
        except KeyError as e:
            print(f"Missing template variable: {e}")
            return message
    
    def notify_complaint_submitted(self, complaint: Complaint, language: str = 'en') -> Optional[str]:
        message = self.get_message_template(
            'complaint_submitted',
            language,
            reference_id=complaint.reference_id,
            complaint_type=complaint.complaint_type
        )
        
        return self.send_whatsapp_message(complaint.sender, message)
    
    def notify_status_update(self, complaint: Complaint, notes: str = "", language: str = 'en') -> Optional[str]:
        status_display = self._get_status_display(complaint.status, language)
        
        message = self.get_message_template(
            'status_update',
            language,
            reference_id=complaint.reference_id,
            status=status_display,
            complaint_type=complaint.complaint_type,
            notes=notes or "No additional details."
        )
        
        return self.send_whatsapp_message(complaint.sender, message)
    
    def notify_complaint_resolved(self, complaint: Complaint, language: str = 'en') -> Optional[str]:
        message = self.get_message_template(
            'complaint_resolved',
            language,
            reference_id=complaint.reference_id,
            complaint_type=complaint.complaint_type,
            notes=complaint.resolution_notes or "Issue has been addressed."
        )
        
        return self.send_whatsapp_message(complaint.sender, message)
    
    def send_welcome_message(self, phone_number: str, language: str = 'en') -> Optional[str]:
        message = self.get_message_template('welcome', language)
        return self.send_whatsapp_message(phone_number, message)
    
    def _get_status_display(self, status: ComplaintStatus, language: str = 'en') -> str:
        status_translations = {
            'en': {
                ComplaintStatus.SUBMITTED: "📥 Submitted",
                ComplaintStatus.IN_PROGRESS: "⚠️ In Progress",
                ComplaintStatus.UNDER_REVIEW: "🔍 Under Review",
                ComplaintStatus.RESOLVED: "✅ Resolved",
                ComplaintStatus.CLOSED: "🔒 Closed"
            },
            'af': {
                ComplaintStatus.SUBMITTED: "📥 Ingedien",
                ComplaintStatus.IN_PROGRESS: "⚠️ In Proses",
                ComplaintStatus.UNDER_REVIEW: "🔍 Onder Hersiening",
                ComplaintStatus.RESOLVED: "✅ Opgelos",
                ComplaintStatus.CLOSED: "🔒 Gesluit"
            },
            'zu': {
                ComplaintStatus.SUBMITTED: "📥 Kuthunyelwe",
                ComplaintStatus.IN_PROGRESS: "⚠️ Kuyaqhubeka",
                ComplaintStatus.UNDER_REVIEW: "🔍 Kubuyekezwa",
                ComplaintStatus.RESOLVED: "✅ Kuxazululiwe",
                ComplaintStatus.CLOSED: "🔒 Kuvaliwe"
            },
            'xh': {
                ComplaintStatus.SUBMITTED: "📥 Kuthunyelwe",
                ComplaintStatus.IN_PROGRESS: "⚠️ Kuyaqhuba",
                ComplaintStatus.UNDER_REVIEW: "🔍 Kuphononongwa",
                ComplaintStatus.RESOLVED: "✅ Kusonjululiwe",
                ComplaintStatus.CLOSED: "🔒 Kuvaliwe"
            }
        }
        
        translations = status_translations.get(language, status_translations['en'])
        return translations.get(status, f"❓ {status.value.title()}")
    
    def send_bulk_notification(self, phone_numbers: List[str], message: str) -> Dict[str, Optional[str]]:
        results = {}
        
        for phone_number in phone_numbers:
            result = self.send_whatsapp_message(phone_number, message)
            results[phone_number] = result
        
        return results
    
    def schedule_reminder(self, complaint: Complaint, hours_from_now: int = 24) -> bool:
        # TODO: Implement scheduled notifications using a task queue like Celery
        # For now, this is a placeholder
        print(f"Reminder scheduled for complaint {complaint.reference_id} in {hours_from_now} hours")
        return True

notification_service = NotificationService()