from flask import request, jsonify
from src.services.location_service import location_service

class APIHandler:
    def locate_endpoint(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            lat = data.get('latitude')
            lon = data.get('longitude')
            
            if lat is None or lon is None:
                return jsonify({"error": "Latitude and longitude are required"}), 400
            
            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid latitude or longitude format"}), 400
            
            location = location_service.get_location_from_coordinates(lat, lon)
            
            if not location:
                return jsonify({"error": "Location not found"}), 404
            
            return jsonify(location.to_dict())
        
        except Exception as e:
            print(f"Error in locate endpoint: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    def index(self):
        return jsonify({
            "service": "Muni-Info API",
            "version": "1.0",
            "description": "South African Municipal Information Service",
            "endpoints": {
                "/locate": "POST - Get municipal information from coordinates"
            }
        })

api_handler = APIHandler()