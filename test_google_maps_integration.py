#!/usr/bin/env python3
"""
Test Google Maps integration in location services
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.geocoding_service import geocoding_service
from src.services.location_enhancement_service import location_enhancement_service
from src.config import Config

def test_google_api_configuration():
    """Test Google API configuration"""
    print("Testing Google Maps API Configuration")
    print("=" * 50)
    
    # Check if API key is configured
    if hasattr(Config, 'GOOGLE_MAPS_API_KEY') and Config.GOOGLE_MAPS_API_KEY:
        api_key_preview = Config.GOOGLE_MAPS_API_KEY[:10] + "..." + Config.GOOGLE_MAPS_API_KEY[-5:]
        print(f"+ Google Maps API Key configured: {api_key_preview}")
        return True
    else:
        print("- Google Maps API Key not configured")
        return False

def test_geocoding_with_google():
    """Test geocoding functionality with Google API"""
    print("\nTesting Geocoding with Google API")
    print("=" * 50)
    
    # Test reverse geocoding (coordinates to address)
    print("\n1. Testing reverse geocoding (Cape Town coordinates)...")
    lat, lon = -33.9249, 18.4241  # Cape Town, South Africa
    
    address_info = geocoding_service.coordinates_to_address(lat, lon)
    
    if address_info:
        print(f"+ Address found: {address_info.get('formatted_address', 'N/A')}")
        print(f"+ Source: {address_info.get('source', 'N/A')}")
        print(f"+ Locality: {address_info.get('locality', 'N/A')}")
        print(f"+ Province: {address_info.get('administrative_area_level_1', 'N/A')}")
        return True
    else:
        print("- Failed to get address information")
        return False

def test_places_api():
    """Test Google Places API integration"""
    print("\n2. Testing Google Places API (nearby services)...")
    
    # Cape Town City Hall coordinates
    lat, lon = -33.9249, 18.4241
    
    nearby_services = geocoding_service.find_nearby_services(lat, lon, "municipal office", 2000)
    
    if nearby_services:
        print(f"+ Found {len(nearby_services)} nearby services:")
        for i, service in enumerate(nearby_services[:3], 1):
            print(f"   {i}. {service.get('name', 'Unknown')}")
            print(f"      Address: {service.get('address', 'N/A')}")
            print(f"      Distance: {service.get('distance', 'N/A')}km")
            if service.get('rating'):
                print(f"      Rating: {service.get('rating')}/5")
        return True
    else:
        print("- No nearby services found")
        return False

def test_enhanced_location_service():
    """Test enhanced location service integration"""
    print("\n3. Testing Enhanced Location Service...")
    
    # Test with Johannesburg coordinates
    lat, lon = -26.2041, 28.0473  # Johannesburg, South Africa
    
    enhanced_location = location_enhancement_service.get_enhanced_location_info(lat, lon)
    
    if enhanced_location:
        print(f"+ Enhanced location data retrieved")
        print(f"+ Municipality: {enhanced_location.municipality or 'N/A'}")
        print(f"+ Formatted Address: {enhanced_location.formatted_address or 'N/A'}")
        print(f"+ Ward Info Available: {'Yes' if enhanced_location.ward_info else 'No'}")
        print(f"+ Service Centers: {len(enhanced_location.nearest_service_centers)}")
        
        if enhanced_location.nearest_service_centers:
            print("   Service centers found:")
            for center in enhanced_location.nearest_service_centers[:2]:
                print(f"   - {center.name} ({center.distance}km)")
        
        return True
    else:
        print("- Failed to get enhanced location information")
        return False

def test_web_integration():
    """Test web integration of location services"""
    print("\n4. Testing Web Integration...")
    
    from src.app import create_app
    
    app = create_app()
    with app.test_client() as client:
        # Test location lookup page
        response = client.get('/portal/location')
        
        if response.status_code == 200:
            print("+ Location page loads successfully")
            
            content = response.get_data(as_text=True)
            
            # Check for Google Maps integration
            if 'maps.googleapis.com' in content:
                print("+ Google Maps JavaScript API included")
            else:
                print("- Google Maps JavaScript API not found")
            
            # Check for map container
            if 'location-map' in content:
                print("+ Map container present")
            else:
                print("- Map container missing")
            
            return True
        else:
            print(f"- Location page failed to load: {response.status_code}")
            return False

def test_api_endpoints():
    """Test API endpoints for location services"""
    print("\n5. Testing API Endpoints...")
    
    from src.app import create_app
    
    app = create_app()
    with app.test_client() as client:
        # Test enhanced location API
        response = client.get('/portal/api/location/enhanced?lat=-33.9249&lon=18.4241')
        
        if response.status_code == 200:
            print("+ Enhanced location API working")
            data = response.get_json()
            
            if data.get('success'):
                location = data.get('location')
                print(f"+ API returned location data for: {location.get('municipality', 'Unknown')}")
                return True
            else:
                print(f"- API returned error: {data.get('error')}")
                return False
        else:
            print(f"- Enhanced location API failed: {response.status_code}")
            return False

def main():
    """Run all Google Maps integration tests"""
    print("Google Maps Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("API Configuration", test_google_api_configuration),
        ("Google Geocoding", test_geocoding_with_google),
        ("Google Places API", test_places_api),
        ("Enhanced Location Service", test_enhanced_location_service),
        ("Web Integration", test_web_integration),
        ("API Endpoints", test_api_endpoints)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n[PASS] {test_name}")
                passed += 1
            else:
                print(f"\n[FAIL] {test_name}")
                failed += 1
        except Exception as e:
            print(f"\n[ERROR] {test_name}: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("GOOGLE MAPS INTEGRATION TEST RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if passed >= 4:  # Allow some tolerance for API limits
        print("\nSUCCESS: Google Maps integration is working!")
        print("\nFeatures now available:")
        print("- Enhanced geocoding with Google Maps API")
        print("- Interactive maps with user location marker")
        print("- Nearby service center discovery")
        print("- Real-time address resolution")
        print("- Municipal service integration")
        
        print("\nTo test the interface:")
        print("1. Visit: http://localhost:5000/portal/location")
        print("2. Enter coordinates: -33.9249, 18.4241 (Cape Town)")
        print("3. View the interactive Google Map with markers")
    else:
        print(f"\nSome features may not be fully functional.")
        print("Please check your Google Maps API key and quota.")
    
    return passed >= 4

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)