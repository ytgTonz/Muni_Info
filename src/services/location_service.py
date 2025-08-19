import requests
import json
from typing import Optional
from src.config import Config
from src.models.location import Location
from src.utils.geo_utils import load_municipal_data, point_in_polygon

class LocationService:
    def __init__(self):
        self.mapit_url = Config.MAPIT_BASE_URL
    
    def get_location_from_coordinates(self, lat: float, lon: float) -> Optional[Location]:
        location = Location(latitude=lat, longitude=lon)
        
        try:
            mapit_url = f"{self.mapit_url}/point/4326/{lon},{lat}"
            response = requests.get(mapit_url)
            response.raise_for_status()
            data = response.json()
            
            for area in data.values():
                if area['type_name'] == "Province":
                    location.province = area['name']
                elif area['type_name'] == "District":
                    location.district = area['name']
                elif area['type_name'] == "Municipality":
                    location.municipality = area['name']
            
            return location
            
        except requests.RequestException as e:
            print(f"Error fetching location from MapIt API: {e}")
            return self._fallback_location_lookup(lat, lon)
    
    def _fallback_location_lookup(self, lat: float, lon: float) -> Optional[Location]:
        try:
            data = load_municipal_data()
            location = Location(latitude=lat, longitude=lon)
            
            for province in data.get('provinces', []):
                for district in province.get('districts', []):
                    if 'geometry' in district:
                        found = point_in_polygon(lat, lon, [district])
                        if found:
                            location.province = province['name']
                            location.district = district['name']
                            return location
                            
                    for lm in district.get("local_municipalities", []):
                        if "geometry" in lm:
                            found = point_in_polygon(lat, lon, [lm])
                            if found:
                                location.province = province['name']
                                location.district = district['name']
                                location.municipality = lm['name']
                                return location
            
            return location
            
        except Exception as e:
            print(f"Error in fallback location lookup: {e}")
            return Location(latitude=lat, longitude=lon)

location_service = LocationService()