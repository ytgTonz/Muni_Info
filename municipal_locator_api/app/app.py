from flask import Flask, request, jsonify, render_template
from services.locator import locate_by_coordinates
import os


app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return "South Municipality Locator API"

@app.route('/locate', method=['POST'])
def locate():
    data = request.json()
    lat = data.get('latitude')
    lon = data .get('longitude')
    if lat is None or lon is None:
        return jsonify({"error": "Latitude and longitude are required to continue."}), 404
    
    result = locate_by_coordinates(lat,lon)
    if not result:
        return jsonify({"error": "Location not found"}), 404
    
    return jsonify(result)
    
@app.route('/map')
def map_view():
    return render_template('map_template.html')

if __name__ == '__main__':
    app.run(debug=True)
