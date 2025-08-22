from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from src.services.whatsapp_service import whatsapp_service
from src.services.language_service import language_service
from src.utils.state_manager import state_manager

class WebhookHandler:
    def process_whatsapp_webhook(self):
        incoming_msg = request.values.get("Body", "").strip()
        lat = request.values.get("Latitude")
        lon = request.values.get("Longitude")
        sender = request.form.get("From")
        media_url = request.values.get("MediaUrl0")  # First media attachment
        media_content_type = request.values.get("MediaContentType0")  # Content type of media
        num_media = int(request.values.get("NumMedia", 0))  # Number of media attachments
        
        resp = MessagingResponse()
        msg = resp.message()
        
        current_state = state_manager.get_state(sender)
        user_language = whatsapp_service.get_user_language(sender)
        
        try:
            # Handle media messages
            if num_media > 0:
                # Collect all media URLs
                media_items = []
                for i in range(num_media):
                    media_url_key = f"MediaUrl{i}"
                    content_type_key = f"MediaContentType{i}"
                    media_url = request.values.get(media_url_key)
                    content_type = request.values.get(content_type_key)
                    
                    if media_url:
                        media_items.append({
                            'url': media_url,
                            'content_type': content_type,
                            'index': i
                        })
                
                response_text = whatsapp_service.handle_media_message(media_items, sender, incoming_msg)
                msg.body(response_text)
                return str(resp)
            
            # Handle location sharing
            if lat and lon and current_state in ["start", "started"]:
                response_text = whatsapp_service.handle_location(float(lat), float(lon), sender)
                msg.body(response_text)
            
            # Handle greetings and menu requests
            elif incoming_msg.lower() in ["menu", "hi", "hello", "start", "sawubona", "molo", "hallo"]:
                if current_state == "start":
                    state_manager.set_state(sender, 'started')
                    response_text = whatsapp_service.handle_greeting(sender)
                else:
                    response_text = language_service.get_text('main_menu', user_language)
                msg.body(response_text)
            
            # Handle main menu choices
            elif current_state == "in_location" and incoming_msg in ["1", "2", "3", "4", "5", "6", "7"]:
                response_text = whatsapp_service.handle_menu_choice(incoming_msg, sender)
                msg.body(response_text)
            
            # Handle complaint category selection
            elif current_state == "complaint_category":
                response_text = whatsapp_service.handle_complaint_category(incoming_msg, sender)
                msg.body(response_text)
            
            # Handle complaint description
            elif current_state == "complaint_description":
                response_text = whatsapp_service.handle_complaint_description(incoming_msg, sender)
                msg.body(response_text)
            
            # Handle language selection
            elif current_state == "language_selection":
                response_text = whatsapp_service.handle_language_selection(incoming_msg, sender)
                msg.body(response_text)
            
            # Check if message contains a reference ID
            elif whatsapp_service.detect_reference_id(incoming_msg):
                reference_id = whatsapp_service.detect_reference_id(incoming_msg)
                response_text = whatsapp_service.handle_reference_lookup(reference_id, sender)
                msg.body(response_text)
            
            # Auto-detect language from message
            elif current_state == "start":
                detected_language = language_service.detect_language(incoming_msg)
                whatsapp_service.set_user_language(sender, detected_language)
                state_manager.set_state(sender, 'started')
                response_text = whatsapp_service.handle_greeting(sender)
                msg.body(response_text)
            
            # Default fallback
            else:
                response_text = whatsapp_service.handle_greeting(sender)
                msg.body(response_text)
        
        except Exception as e:
            print(f"Error processing webhook: {e}")
            error_text = language_service.get_text('error_occurred', user_language)
            msg.body(error_text)
        
        return str(resp)

webhook_handler = WebhookHandler()