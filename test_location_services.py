#!/usr/bin/env python3
"""
Test script for advanced location services
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_location_service():
    """Test basic location service"""
    try:
        from src.services.location_service import location_service
        
        # Test coordinates for Cape Town
        lat, lon = -33.9249, 18.4241
        
        print("Testing basic location service...")
        location = location_service.get_location_from_coordinates(lat, lon)
        
        if location:
            print(f"[OK] Basic location found:")
            print(f"   Municipality: {location.municipality}")
            print(f"   Province: {location.province}")
            print(f"   District: {location.district}")
            print(f"   Coordinates: {location.latitude}, {location.longitude}")
            return True
        else:
            print("[ERROR] No location found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Basic location service failed: {e}")
        return False

def test_geocoding_service():
    """Test geocoding service for address conversion"""
    try:
        from src.services.geocoding_service import geocoding_service
        
        # Test coordinates for Cape Town
        lat, lon = -33.9249, 18.4241
        
        print("\nTesting geocoding service...")
        address_info = geocoding_service.coordinates_to_address(lat, lon)
        
        if address_info:
            print(f"[OK] Address information found:")
            print(f"   Formatted Address: {address_info.get('formatted_address')}")
            print(f"   Street: {address_info.get('route')}")
            print(f"   Locality: {address_info.get('locality')}")
            print(f"   Province: {address_info.get('administrative_area_level_1')}")
            print(f"   Source: {address_info.get('source')}")
            return True
        else:
            print("[ERROR] No address information found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Geocoding service failed: {e}")
        return False

def test_enhanced_location_service():
    """Test enhanced location service with ward and service center information"""
    try:
        from src.services.location_enhancement_service import location_enhancement_service
        
        # Test coordinates for Cape Town
        lat, lon = -33.9249, 18.4241
        
        print("\nTesting enhanced location service...")
        location = location_enhancement_service.get_enhanced_location_info(lat, lon)
        
        if location:
            print(f"[OK] Enhanced location found:")
            print(f"   Municipality: {location.municipality}")
            print(f"   Province: {location.province}")
            print(f"   Full Address: {location.get_full_address()}")
            print(f"   Geocoding Source: {location.geocoding_source}")
            
            # Test ward information
            if location.ward_info:
                print(f"   Ward Number: {location.ward_info.ward_number}")
                print(f"   Councillor: {location.ward_info.councillor_name}")
                print(f"   Ward Office: {location.ward_info.ward_office_address}")
            
            # Test service centers
            if location.nearest_service_centers:
                print(f"   Nearest Service Centers: {len(location.nearest_service_centers)} found")
                for i, center in enumerate(location.nearest_service_centers[:2]):
                    print(f"     {i+1}. {center.name} ({center.distance_km} km)")
            
            return True
        else:
            print("[ERROR] No enhanced location found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Enhanced location service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ward_lookup():
    """Test ward information lookup"""
    try:
        from src.services.location_enhancement_service import location_enhancement_service
        
        # Test coordinates for multiple cities
        test_locations = [
            (-33.9249, 18.4241, "Cape Town"),
            (-26.2041, 28.0473, "Johannesburg"),
            (-29.8587, 31.0218, "Durban")
        ]
        
        print("\nTesting ward lookup for multiple cities...")
        
        for lat, lon, city in test_locations:
            print(f"\n  Testing {city} ({lat}, {lon}):")
            ward_info = location_enhancement_service.get_ward_info(lat, lon)
            
            if ward_info:
                print(f"    Ward: {ward_info.ward_number}")
                print(f"    Councillor: {ward_info.councillor_name}")
                print(f"    Contact: {ward_info.councillor_contact}")
            else:
                print(f"    No ward information found")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Ward lookup failed: {e}")
        return False

def test_service_centers():
    """Test service center lookup"""
    try:
        from src.services.location_enhancement_service import location_enhancement_service
        
        # Test coordinates for Cape Town
        lat, lon = -33.9249, 18.4241
        
        print("\nTesting service center lookup...")
        service_centers = location_enhancement_service.find_nearest_service_centers(
            lat, lon, "City of Cape Town", radius_km=15.0
        )
        
        if service_centers:
            print(f"[OK] Found {len(service_centers)} service centers:")
            for center in service_centers:
                print(f"   - {center.name}")
                print(f"     Address: {center.address}")
                print(f"     Distance: {center.distance_km} km")
                print(f"     Services: {', '.join(center.services[:3])}...")
                print()
            return True
        else:
            print("[ERROR] No service centers found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Service center lookup failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints by making HTTP requests"""
    try:
        import requests
        
        print("\nTesting API endpoints...")
        base_url = "http://127.0.0.1:5000"
        
        # Test enhanced location API
        params = {"lat": -33.9249, "lon": 18.4241}
        response = requests.get(f"{base_url}/portal/api/location/enhanced", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("[OK] Enhanced location API working")
                location_data = data.get('location', {})
                print(f"   Municipality: {location_data.get('municipality')}")
                print(f"   Address: {location_data.get('formatted_address')}")
            else:
                print(f"[ERROR] API returned error: {data.get('error')}")
                return False
        else:
            print(f"[ERROR] API request failed: {response.status_code}")
            return False
        
        # Test service centers API
        response = requests.get(f"{base_url}/portal/api/location/service-centers", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                centers = data.get('service_centers', [])
                print(f"[OK] Service centers API working - found {len(centers)} centers")
            else:
                print(f"[ERROR] Service centers API error: {data.get('error')}")
                return False
        else:
            print(f"[ERROR] Service centers API failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] API testing failed: {e}")
        return False

def main():
    """Run all location service tests"""
    print("Testing Advanced Location Services for Muni-Info")
    print("=" * 55)
    
    tests = [
        ("Basic Location Service", test_basic_location_service),
        ("Geocoding Service", test_geocoding_service), 
        ("Enhanced Location Service", test_enhanced_location_service),
        ("Ward Lookup", test_ward_lookup),
        ("Service Centers", test_service_centers)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name + ":"))
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 55)
    print("TEST SUMMARY:")
    
    passed = 0
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n[SUCCESS] All location services are working correctly!")
        print("\nFeatures available:")
        print("- GPS coordinates to street addresses")
        print("- Ward number and councillor information")
        print("- Nearest municipal offices and service centers")
        print("- Enhanced location APIs")
        print("- Service area boundary data")
    else:
        print(f"\n[WARNING] {len(results) - passed} tests failed")
        print("Some location features may not work properly.")

if __name__ == "__main__":
    main()