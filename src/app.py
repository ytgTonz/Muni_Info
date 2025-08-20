from flask import Flask
from src.config import Config
from src.handlers.webhook_handler import webhook_handler
from src.handlers.api_handler import api_handler
from src.admin.views import admin_bp
from src.api.v1.routes import api_v1
from src.portal.views import portal_bp
from src.services.user_service import user_service

def create_app():
    app = Flask(__name__)
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
    
    @app.route('/')
    @app.route('/index')
    def index():
        return portal_bp.index()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG)