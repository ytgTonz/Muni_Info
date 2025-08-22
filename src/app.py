from flask import Flask, send_from_directory, abort
from src.config import Config
from src.handlers.webhook_handler import webhook_handler
from src.handlers.api_handler import api_handler
from src.admin.views import admin_bp
from src.api.v1.routes import api_v1
from src.portal.views import portal_bp
from src.services.user_service import user_service
from src.services.ussd_service import ussd_service
from src.services.database_service import db_service
from src.services.media_service import media_service
import os

def create_app():
    import os
    # Get the parent directory (root of the project)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY if hasattr(Config, 'SECRET_KEY') else 'dev-secret-key-change-in-production'
    
    # Initialize user service
    user_service.init_app(app)
    
    # Register blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_v1)
    app.register_blueprint(portal_bp)
    
    @app.route('/whatsapp', methods=['POST', 'GET'])
    def whatsapp_webhook():
        return webhook_handler.process_whatsapp_webhook()
    
    @app.route('/locate', methods=['POST'])
    def locate():
        return api_handler.locate_endpoint()
    
    @app.route('/ussd', methods=['POST'])
    def ussd_endpoint():
        """USSD endpoint for feature phone access"""
        from flask import request
        
        # Get USSD parameters (format may vary by telecom provider)
        session_id = request.form.get('sessionId', '')
        phone_number = request.form.get('phoneNumber', '')
        text = request.form.get('text', '')
        
        # Process USSD request
        response_text, continue_session = ussd_service.process_ussd_request(session_id, phone_number, text)
        
        # Return USSD response (format depends on provider)
        return {
            'text': response_text,
            'continueSession': continue_session
        }
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded media files"""
        try:
            # Ensure proper path handling for Windows
            safe_path = filename.replace('\\', '/')
            upload_folder = os.path.abspath(media_service.upload_folder)
            
            # Security check to prevent directory traversal
            file_path = os.path.join(upload_folder, safe_path)
            file_path = os.path.abspath(file_path)
            
            if not file_path.startswith(upload_folder):
                abort(403)  # Forbidden - attempted directory traversal
            
            if not os.path.exists(file_path):
                abort(404)  # File not found
            
            return send_from_directory(upload_folder, safe_path)
        except Exception as e:
            app.logger.error(f"Error serving file {filename}: {e}")
            abort(500)
    
    @app.route('/')
    @app.route('/index')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('portal.index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG)