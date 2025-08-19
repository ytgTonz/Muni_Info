from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from src.services.whatsapp_service import whatsapp_service
from src.utils.state_manager import state_manager

class WebhookHandler:
    def process_whatsapp_webhook(self):
        incoming_msg = request.values.get("Body", "").lower().strip()
        lat = request.values.get("Latitude")
        lon = request.values.get("Longitude")
        sender = request.form.get("From")
        
        resp = MessagingResponse()
        msg = resp.message()
        
        current_state = state_manager.get_state(sender)
        
        try:
            if lat and lon and current_state in ["start", "started"]:
                response_text = whatsapp_service.handle_location(float(lat), float(lon), sender)
                msg.body(response_text)
            
            elif incoming_msg in ["menu", "hi", "hello", "start"]:
                if current_state == "start":
                    state_manager.set_state(sender, 'started')
                    response_text = whatsapp_service.handle_greeting()
                else:
                    response_text = whatsapp_service.main_menu
                msg.body(response_text)
            
            elif current_state == "in_location" and incoming_msg in ["1", "2", "3", "4", "5"]:
                response_text = whatsapp_service.handle_menu_choice(incoming_msg, sender)
                msg.body(response_text)
            
            elif current_state == "complaint_category":
                response_text = whatsapp_service.handle_complaint_category(incoming_msg, sender)
                msg.body(response_text)
            
            elif current_state == "complaint_description":
                response_text = whatsapp_service.handle_complaint_description(incoming_msg, sender)
                msg.body(response_text)
            
            else:
                if current_state == "start":
                    state_manager.set_state(sender, 'started')
                response_text = whatsapp_service.handle_greeting()
                msg.body(response_text)
        
        except Exception as e:
            print(f"Error processing webhook: {e}")
            msg.body("❌ Sorry, something went wrong. Please try again or type 'menu' for options.")
        
        return str(resp)

webhook_handler = WebhookHandler()