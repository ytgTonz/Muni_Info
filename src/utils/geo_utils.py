import json
from shapely.geometry import shape, Point
from src.config import Config
from typing import Optional, Dict, Any, List

def load_municipal_data() -> Dict[str, Any]:
    try:
        with open(Config.MUNICIPALITIES_DATA, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Municipal data file not found: {Config.MUNICIPALITIES_DATA}")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from: {Config.MUNICIPALITIES_DATA}")
        return {}

def load_emergency_services() -> Dict[str, Any]:
    try:
        with open(Config.EMERGENCY_SERVICES_DATA, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Emergency services data file not found: {Config.EMERGENCY_SERVICES_DATA}")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from: {Config.EMERGENCY_SERVICES_DATA}")
        return {}

def point_in_polygon(lat: float, lon: float, polygons: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    try:
        point = Point(lon, lat)
        for item in polygons:
            if 'geometry' in item:
                geom = shape(item['geometry'])
                if geom.contains(point):
                    return item
    except Exception as e:
        print(f"Error in point_in_polygon calculation: {e}")
    
    return None