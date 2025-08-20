import requests
from typing import Optional, Dict, Any, List
from src.config import Config

class GeocodingService:
    def __init__(self):
        self.google_api_key = Config.GOOGLE_MAPS_API_KEY if hasattr(Config, 'GOOGLE_MAPS_API_KEY') else None
        self.nominatim_url = "https://nominatim.openstreetmap.org"
    
    def coordinates_to_address(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Convert GPS coordinates to a readable address"""
        # Try Google Maps API first if available
        if self.google_api_key:
            address = self._google_reverse_geocode(lat, lon)
            if address:
                return address
        
        # Fallback to OpenStreetMap Nominatim (free)
        return self._nominatim_reverse_geocode(lat, lon)
    
    def address_to_coordinates(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert address to GPS coordinates"""
        # Try Google Maps API first if available
        if self.google_api_key:
            coords = self._google_geocode(address)
            if coords:
                return coords
        
        # Fallback to OpenStreetMap Nominatim (free)
        return self._nominatim_geocode(address)
    
    def find_nearby_services(self, lat: float, lon: float, service_type: str = "municipal_office", radius: int = 5000) -> List[Dict[str, Any]]:
        """Find nearby municipal services"""
        if not self.google_api_key:
            return []
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f"{lat},{lon}",
            'radius': radius,
            'keyword': service_type,
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            services = []
            for place in data.get('results', [])[:10]:  # Limit to 10 results
                service = {
                    'name': place.get('name'),
                    'address': place.get('vicinity'),
                    'rating': place.get('rating'),
                    'location': place.get('geometry', {}).get('location', {}),
                    'place_id': place.get('place_id'),
                    'types': place.get('types', []),
                    'open_now': place.get('opening_hours', {}).get('open_now'),
                    'distance': self._calculate_distance(
                        lat, lon,
                        place.get('geometry', {}).get('location', {}).get('lat', 0),
                        place.get('geometry', {}).get('location', {}).get('lng', 0)
                    )
                }
                services.append(service)
            
            # Sort by distance
            services.sort(key=lambda x: x['distance'])
            return services
            
        except Exception as e:
            print(f"Error finding nearby services: {e}")
            return []
    
    def get_ward_information(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get ward information for the given coordinates"""
        # This would typically require a specific South African municipal API
        # For now, we'll use a placeholder implementation
        try:
            # Try to use a South African ward API or database
            # This is a simplified example - in production you'd use:
            # - Municipal Demarcation Board API
            # - Provincial government APIs
            # - Local municipal databases
            
            ward_info = {
                'ward_number': self._estimate_ward_from_coordinates(lat, lon),
                'councillor': self._get_councillor_info(lat, lon),
                'contact_details': self._get_ward_contact_details(lat, lon),
                'service_delivery_office': self._find_nearest_service_office(lat, lon)
            }
            
            return ward_info
            
        except Exception as e:
            print(f"Error getting ward information: {e}")
            return None
    
    def _google_reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Google Maps reverse geocoding"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{lat},{lon}",
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                
                # Extract address components
                components = {comp['types'][0]: comp['long_name'] 
                            for comp in result.get('address_components', [])}
                
                return {
                    'formatted_address': result.get('formatted_address'),
                    'street_number': components.get('street_number'),
                    'route': components.get('route'),
                    'locality': components.get('locality'),
                    'sublocality': components.get('sublocality'),
                    'administrative_area_level_1': components.get('administrative_area_level_1'),
                    'administrative_area_level_2': components.get('administrative_area_level_2'),
                    'postal_code': components.get('postal_code'),
                    'country': components.get('country'),
                    'coordinates': {
                        'lat': result['geometry']['location']['lat'],
                        'lng': result['geometry']['location']['lng']
                    },
                    'source': 'google'
                }
                
        except Exception as e:
            print(f"Google reverse geocoding error: {e}")
            return None
    
    def _nominatim_reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """OpenStreetMap Nominatim reverse geocoding (free)"""
        url = f"{self.nominatim_url}/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18
        }
        headers = {
            'User-Agent': 'Muni-Info/1.0 (municipal complaint system)'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            address = data.get('address', {})
            
            return {
                'formatted_address': data.get('display_name'),
                'street_number': address.get('house_number'),
                'route': address.get('road'),
                'locality': address.get('city') or address.get('town') or address.get('village'),
                'sublocality': address.get('suburb'),
                'administrative_area_level_1': address.get('state') or address.get('province'),
                'administrative_area_level_2': address.get('county'),
                'postal_code': address.get('postcode'),
                'country': address.get('country'),
                'coordinates': {
                    'lat': float(data.get('lat', lat)),
                    'lng': float(data.get('lon', lon))
                },
                'source': 'nominatim'
            }
            
        except Exception as e:
            print(f"Nominatim reverse geocoding error: {e}")
            return None
    
    def _google_geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """Google Maps geocoding"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': self.google_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': result['formatted_address'],
                    'source': 'google'
                }
                
        except Exception as e:
            print(f"Google geocoding error: {e}")
            return None
    
    def _nominatim_geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """OpenStreetMap Nominatim geocoding (free)"""
        url = f"{self.nominatim_url}/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'Muni-Info/1.0 (municipal complaint system)'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lng': float(result['lon']),
                    'formatted_address': result['display_name'],
                    'source': 'nominatim'
                }
                
        except Exception as e:
            print(f"Nominatim geocoding error: {e}")
            return None
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return round(distance, 2)
    
    def _estimate_ward_from_coordinates(self, lat: float, lon: float) -> Optional[str]:
        """Estimate ward number from coordinates (placeholder implementation)"""
        # This would require access to ward boundary data
        # For now, return a placeholder
        return f"Ward {int(abs(lat * lon) % 100) + 1}"
    
    def _get_councillor_info(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get councillor information for the area (placeholder implementation)"""
        # This would require access to councillor database
        return {
            'name': 'Councillor Name (Demo)',
            'party': 'Political Party',
            'contact_number': '+27 XX XXX XXXX',
            'email': 'councillor@municipality.gov.za',
            'office_hours': 'Monday - Friday, 8:00 AM - 4:30 PM'
        }
    
    def _get_ward_contact_details(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get ward contact details (placeholder implementation)"""
        return {
            'ward_office_address': '123 Municipal Street, City, Province',
            'phone': '+27 XX XXX XXXX',
            'email': 'ward@municipality.gov.za',
            'office_hours': 'Monday - Friday, 8:00 AM - 4:30 PM'
        }
    
    def _find_nearest_service_office(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Find nearest municipal service office (placeholder implementation)"""
        return {
            'name': 'Municipal Service Center',
            'address': '456 Service Avenue, City, Province',
            'phone': '+27 XX XXX XXXX',
            'services': ['Water & Sanitation', 'Electricity', 'Building Plans', 'General Inquiries'],
            'distance': 2.5  # km
        }

geocoding_service = GeocodingService()