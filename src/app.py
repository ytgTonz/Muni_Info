from flask import Flask
from src.config import Config
from src.handlers.webhook_handler import webhook_handler
from src.handlers.api_handler import api_handler

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    @app.route('/whatsapp', methods=['POST', 'GET'])
    def whatsapp_webhook():
        return webhook_handler.process_whatsapp_webhook()
    
    @app.route('/locate', methods=['POST'])
    def locate():
        return api_handler.locate_endpoint()
    
    @app.route('/')
    @app.route('/index')
    def index():
        return api_handler.index()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG)