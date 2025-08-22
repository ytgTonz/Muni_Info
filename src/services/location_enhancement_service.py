import requests
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.config import Config
from src.models.location import Location, WardInfo, ServiceCenter
from src.services.geocoding_service import geocoding_service
from src.services.location_service import location_service
from src.services.database_service import db_service
import logging

logger = logging.getLogger(__name__)

class LocationEnhancementService:
    def __init__(self):
        self.google_api_key = getattr(Config, 'GOOGLE_MAPS_API_KEY', None)
        self.ward_collection = db_service.get_collection('ward_boundaries')
        self.councillor_collection = db_service.get_collection('councillors')
        self.service_centers_collection = db_service.get_collection('service_centers')
        
        # Initialize sample data if collections are empty
        self._initialize_sample_data()
    
    def get_enhanced_location_info(self, lat: float, lon: float) -> Location:
        """Get comprehensive location information including address, ward, and services"""
        try:
            # Start with basic municipal information
            basic_location = location_service.get_location_from_coordinates(lat, lon)
            
            # Create enhanced location object
            location = Location(
                latitude=lat,
                longitude=lon,
                province=basic_location.province if basic_location else None,
                district=basic_location.district if basic_location else None,
                municipality=basic_location.municipality if basic_location else None,
                last_updated=datetime.now()
            )
            
            # Get detailed address information
            address_info = geocoding_service.coordinates_to_address(lat, lon)
            if address_info:
                location.formatted_address = address_info.get('formatted_address')
                location.street_number = address_info.get('street_number')
                location.street_name = address_info.get('route')
                location.suburb = address_info.get('sublocality')
                location.city = address_info.get('locality')
                location.postal_code = address_info.get('postal_code')
                location.geocoding_source = address_info.get('source')
            
            # Get ward information
            location.ward_info = self.get_ward_info(lat, lon, location.municipality)
            
            # Get nearest service centers
            location.nearest_service_centers = self.find_nearest_service_centers(lat, lon, location.municipality)
            
            return location
            
        except Exception as e:
            logger.error(f"Error getting enhanced location info: {e}")
            # Return basic location on error
            return Location(latitude=lat, longitude=lon, last_updated=datetime.now())
    
    def get_ward_info(self, lat: float, lon: float, municipality: Optional[str] = None) -> Optional[WardInfo]:
        """Get ward information for given coordinates"""
        try:
            # Try to find ward from database
            ward_data = self._find_ward_in_database(lat, lon, municipality)
            
            if ward_data:
                # Get councillor information
                councillor_info = self._get_councillor_from_database(ward_data.get('ward_number'), municipality)
                
                ward_info = WardInfo(
                    ward_number=ward_data.get('ward_number'),
                    ward_office_address=ward_data.get('office_address'),
                    ward_office_phone=ward_data.get('office_phone'),
                    ward_office_email=ward_data.get('office_email'),
                    office_hours=ward_data.get('office_hours', 'Monday - Friday, 8:00 AM - 4:30 PM')
                )
                
                if councillor_info:
                    ward_info.councillor_name = councillor_info.get('name')
                    ward_info.councillor_party = councillor_info.get('party')
                    ward_info.councillor_contact = councillor_info.get('phone')
                    ward_info.councillor_email = councillor_info.get('email')
                
                return ward_info
            
            # Fallback to estimated ward information
            return self._generate_estimated_ward_info(lat, lon, municipality)
            
        except Exception as e:
            logger.error(f"Error getting ward info: {e}")
            return None
    
    def find_nearest_service_centers(self, lat: float, lon: float, municipality: Optional[str] = None, radius_km: float = 10.0) -> List[ServiceCenter]:
        """Find nearest municipal service centers"""
        try:
            service_centers = []
            
            # Search database for service centers
            query = {}
            if municipality:
                query['municipality'] = municipality
            
            centers = self.service_centers_collection.find(query)
            
            for center in centers:
                center_lat = center.get('latitude')
                center_lon = center.get('longitude')
                
                if center_lat and center_lon:
                    distance = self._calculate_distance(lat, lon, center_lat, center_lon)
                    
                    if distance <= radius_km:
                        service_center = ServiceCenter(
                            name=center.get('name', 'Municipal Service Center'),
                            address=center.get('address', 'Address not available'),
                            phone=center.get('phone'),
                            email=center.get('email'),
                            services=center.get('services', []),
                            distance_km=distance,
                            coordinates={'lat': center_lat, 'lng': center_lon},
                            operating_hours=center.get('operating_hours'),
                            rating=center.get('rating')
                        )
                        service_centers.append(service_center)
            
            # If no centers found in database, try Google Places API
            if not service_centers and self.google_api_key:
                google_centers = self._find_service_centers_via_google(lat, lon)
                service_centers.extend(google_centers)
            
            # If still no centers, add default municipal services
            if not service_centers:
                service_centers = self._generate_default_service_centers(lat, lon, municipality)
            
            # Sort by distance
            service_centers.sort(key=lambda x: x.distance_km or float('inf'))
            
            # Return top 5 nearest centers
            return service_centers[:5]
            
        except Exception as e:
            logger.error(f"Error finding service centers: {e}")
            return []
    
    def get_service_area_boundaries(self, municipality: str) -> Optional[Dict[str, Any]]:
        """Get service area boundaries for mapping"""
        try:
            # This would typically return GeoJSON data for ward boundaries
            # For now, return a simplified boundary
            query = {'municipality': municipality}
            ward_boundaries = list(self.ward_collection.find(query))
            
            if ward_boundaries:
                # Convert to GeoJSON-like format
                features = []
                for ward in ward_boundaries:
                    if ward.get('boundary_coordinates'):
                        feature = {
                            'type': 'Feature',
                            'properties': {
                                'ward_number': ward.get('ward_number'),
                                'municipality': ward.get('municipality'),
                                'councillor': ward.get('councillor'),
                                'population': ward.get('population')
                            },
                            'geometry': {
                                'type': 'Polygon',
                                'coordinates': ward.get('boundary_coordinates')
                            }
                        }
                        features.append(feature)
                
                return {
                    'type': 'FeatureCollection',
                    'features': features
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting service area boundaries: {e}")
            return None
    
    def _find_ward_in_database(self, lat: float, lon: float, municipality: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find ward in database using coordinates"""
        try:
            query = {}
            if municipality:
                query['municipality'] = municipality
            
            # For demonstration, find ward by proximity
            # In a real implementation, you'd use spatial queries
            wards = self.ward_collection.find(query)
            
            closest_ward = None
            min_distance = float('inf')
            
            for ward in wards:
                ward_lat = ward.get('center_latitude')
                ward_lon = ward.get('center_longitude')
                
                if ward_lat and ward_lon:
                    distance = self._calculate_distance(lat, lon, ward_lat, ward_lon)
                    if distance < min_distance:
                        min_distance = distance
                        closest_ward = ward
            
            return closest_ward
            
        except Exception as e:
            logger.error(f"Error finding ward in database: {e}")
            return None
    
    def _get_councillor_from_database(self, ward_number: str, municipality: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get councillor information from database"""
        try:
            query = {'ward_number': ward_number}
            if municipality:
                query['municipality'] = municipality
            
            councillor = self.councillor_collection.find_one(query)
            return councillor
            
        except Exception as e:
            logger.error(f"Error getting councillor from database: {e}")
            return None
    
    def _find_service_centers_via_google(self, lat: float, lon: float) -> List[ServiceCenter]:
        """Find service centers using Google Places API"""
        try:
            if not self.google_api_key:
                return []
            
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            
            # Search for government offices and municipal services
            search_terms = [
                "municipal office",
                "government office", 
                "city hall",
                "municipality",
                "service center"
            ]
            
            service_centers = []
            
            for term in search_terms:
                params = {
                    'location': f"{lat},{lon}",
                    'radius': 10000,  # 10km radius
                    'keyword': term,
                    'key': self.google_api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for place in data.get('results', [])[:3]:  # Limit results
                    place_location = place.get('geometry', {}).get('location', {})
                    distance = self._calculate_distance(
                        lat, lon,
                        place_location.get('lat', 0),
                        place_location.get('lng', 0)
                    )
                    
                    service_center = ServiceCenter(
                        name=place.get('name', 'Municipal Service'),
                        address=place.get('vicinity', 'Address not available'),
                        services=['General Municipal Services'],
                        distance_km=distance,
                        coordinates=place_location,
                        rating=place.get('rating'),
                        operating_hours='Monday - Friday, 8:00 AM - 4:30 PM'
                    )
                    service_centers.append(service_center)
            
            return service_centers
            
        except Exception as e:
            logger.error(f"Error finding service centers via Google: {e}")
            return []
    
    def _generate_estimated_ward_info(self, lat: float, lon: float, municipality: Optional[str] = None) -> WardInfo:
        """Generate estimated ward information when database lookup fails"""
        # Generate a ward number based on coordinates
        ward_number = f"Ward {int(abs(lat * lon * 10) % 150) + 1}"
        
        return WardInfo(
            ward_number=ward_number,
            councillor_name="Councillor Information Available at Municipal Office",
            ward_office_address=f"Municipal Office - {municipality or 'Local Municipality'}",
            ward_office_phone="+27 XX XXX XXXX",
            office_hours="Monday - Friday, 8:00 AM - 4:30 PM"
        )
    
    def _generate_default_service_centers(self, lat: float, lon: float, municipality: Optional[str] = None) -> List[ServiceCenter]:
        """Generate default service centers when none are found"""
        centers = []
        
        # Main municipal office
        main_office = ServiceCenter(
            name=f"{municipality or 'Municipal'} Head Office",
            address="Municipal Head Office (Contact for exact address)",
            phone="+27 XX XXX XXXX",
            services=[
                "Building Plans", 
                "Rates & Taxes", 
                "Water & Electricity", 
                "General Inquiries"
            ],
            distance_km=5.0,
            operating_hours="Monday - Friday, 8:00 AM - 4:30 PM"
        )
        centers.append(main_office)
        
        # Service center
        service_center = ServiceCenter(
            name="Municipal Service Center",
            address="Service Center (Contact for exact address)",
            phone="+27 XX XXX XXXX",
            services=[
                "Water & Sanitation Complaints",
                "Electricity Issues",
                "Road Maintenance",
                "Waste Management"
            ],
            distance_km=3.0,
            operating_hours="Monday - Friday, 7:30 AM - 4:00 PM"
        )
        centers.append(service_center)
        
        return centers
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula"""
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
    
    def _initialize_sample_data(self):
        """Initialize sample ward and service center data"""
        try:
            # Check if data already exists
            if self.ward_collection.count_documents({}) > 0:
                return
            
            # Sample ward data for major South African cities
            sample_wards = [
                {
                    "ward_number": "Ward 1",
                    "municipality": "City of Cape Town",
                    "center_latitude": -33.9249,
                    "center_longitude": 18.4241,
                    "office_address": "Cape Town Civic Centre, 12 Hertzog Boulevard, Cape Town",
                    "office_phone": "+27 21 400 1111",
                    "office_email": "ward1@capetown.gov.za",
                    "boundary_coordinates": [[[18.420, -33.920], [18.430, -33.920], [18.430, -33.930], [18.420, -33.930], [18.420, -33.920]]]
                },
                {
                    "ward_number": "Ward 1",
                    "municipality": "City of Johannesburg",
                    "center_latitude": -26.2041,
                    "center_longitude": 28.0473,
                    "office_address": "Johannesburg City Hall, Pritchard Street, Johannesburg",
                    "office_phone": "+27 11 407 7911",
                    "office_email": "ward1@joburg.org.za",
                    "boundary_coordinates": [[[28.040, -26.200], [28.055, -26.200], [28.055, -26.210], [28.040, -26.210], [28.040, -26.200]]]
                },
                {
                    "ward_number": "Ward 1", 
                    "municipality": "eThekwini Municipality",
                    "center_latitude": -29.8587,
                    "center_longitude": 31.0218,
                    "office_address": "Durban City Hall, Smith Street, Durban",
                    "office_phone": "+27 31 311 1111",
                    "office_email": "ward1@durban.gov.za",
                    "boundary_coordinates": [[[31.015, -29.855], [31.030, -29.855], [31.030, -29.865], [31.015, -29.865], [31.015, -29.855]]]
                }
            ]
            
            # Sample councillor data
            sample_councillors = [
                {
                    "ward_number": "Ward 1",
                    "municipality": "City of Cape Town", 
                    "name": "Councillor A. Smith",
                    "party": "Democratic Alliance",
                    "phone": "+27 21 400 1234",
                    "email": "a.smith@capetown.gov.za"
                },
                {
                    "ward_number": "Ward 1",
                    "municipality": "City of Johannesburg",
                    "name": "Councillor B. Mthembu", 
                    "party": "African National Congress",
                    "phone": "+27 11 407 1234",
                    "email": "b.mthembu@joburg.org.za"
                },
                {
                    "ward_number": "Ward 1",
                    "municipality": "eThekwini Municipality",
                    "name": "Councillor C. Pillay",
                    "party": "African National Congress", 
                    "phone": "+27 31 311 1234",
                    "email": "c.pillay@durban.gov.za"
                }
            ]
            
            # Sample service centers
            sample_service_centers = [
                {
                    "name": "Cape Town Customer Service Centre",
                    "municipality": "City of Cape Town",
                    "latitude": -33.9249,
                    "longitude": 18.4241,
                    "address": "Civic Centre, 12 Hertzog Boulevard, Cape Town",
                    "phone": "+27 21 400 1111",
                    "email": "services@capetown.gov.za",
                    "services": ["Water & Sanitation", "Electricity", "Rates & Taxes", "Building Plans"],
                    "operating_hours": "Monday - Friday, 7:30 AM - 4:30 PM",
                    "rating": 4.2
                },
                {
                    "name": "Johannesburg Service Delivery Centre",
                    "municipality": "City of Johannesburg", 
                    "latitude": -26.2041,
                    "longitude": 28.0473,
                    "address": "Metro Centre, 158 Loveday Street, Johannesburg",
                    "phone": "+27 11 407 7911",
                    "email": "services@joburg.org.za",
                    "services": ["Electricity", "Water", "Waste Management", "Roads"],
                    "operating_hours": "Monday - Friday, 8:00 AM - 4:00 PM",
                    "rating": 3.8
                },
                {
                    "name": "eThekwini Customer Care Centre",
                    "municipality": "eThekwini Municipality",
                    "latitude": -29.8587,
                    "longitude": 31.0218,
                    "address": "City Hall, Smith Street, Durban",
                    "phone": "+27 31 311 1111", 
                    "email": "services@durban.gov.za",
                    "services": ["Water & Sanitation", "Electricity", "Solid Waste", "Parks"],
                    "operating_hours": "Monday - Friday, 8:00 AM - 4:30 PM",
                    "rating": 4.0
                }
            ]
            
            # Insert sample data
            if sample_wards:
                self.ward_collection.insert_many(sample_wards)
                logger.info(f"Inserted {len(sample_wards)} sample wards")
            
            if sample_councillors:
                self.councillor_collection.insert_many(sample_councillors)
                logger.info(f"Inserted {len(sample_councillors)} sample councillors")
            
            if sample_service_centers:
                self.service_centers_collection.insert_many(sample_service_centers)
                logger.info(f"Inserted {len(sample_service_centers)} sample service centers")
                
        except Exception as e:
            logger.error(f"Error initializing sample data: {e}")

# Global service instance
location_enhancement_service = LocationEnhancementService()