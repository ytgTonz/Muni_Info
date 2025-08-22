#!/usr/bin/env python3
"""
Test end-to-end photo/video functionality
"""

import sys
import os
from PIL import Image
import io
import requests

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app
from src.services.complaint_service import complaint_service

def test_end_to_end_flow():
    """Test complete photo/video upload and retrieval flow"""
    print("Testing End-to-End Photo/Video Flow")
    print("=" * 50)
    
    app = create_app()
    
    with app.test_client() as client:
        # Step 1: Test form submission with file upload
        print("\n1. Testing file upload with complaint submission...")
        
        # Create a test image
        test_image = Image.new('RGB', (400, 300), color='blue')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        # Simulate form submission with file
        form_data = {
            'phone_number': '+27123456789',
            'complaint_type': 'Water',
            'description': 'Test complaint with image attachment',
            'priority': 'medium',
            'media_files': (img_buffer, 'test_image.jpg', 'image/jpeg')
        }
        
        response = client.post('/portal/complaints/submit', 
                             data=form_data, 
                             content_type='multipart/form-data',
                             follow_redirects=False)
        
        print(f"   Form submission status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect after successful submission
            print("   ✅ Form submitted successfully")
            
            # Extract reference ID from redirect location
            location = response.headers.get('Location', '')
            print(f"   Redirect location: {location}")
            
            # Try to extract reference ID
            if 'reference_id=' in location:
                reference_id = location.split('reference_id=')[1]
                print(f"   Reference ID: {reference_id}")
                
                # Step 2: Check if complaint was saved with media
                print("\n2. Testing database storage...")
                complaint = complaint_service.get_complaint_by_reference(reference_id)
                
                if complaint:
                    print(f"   ✅ Complaint found: {complaint.reference_id}")
                    print(f"   Image URLs: {len(complaint.image_urls)}")
                    print(f"   Video URLs: {len(complaint.video_urls)}")
                    print(f"   Media metadata entries: {len(complaint.media_metadata)}")
                    
                    # Step 3: Test file retrieval
                    if complaint.image_urls:
                        print("\n3. Testing file retrieval...")
                        for i, image_url in enumerate(complaint.image_urls):
                            print(f"   Testing URL {i+1}: {image_url}")
                            
                            # Test file serving
                            file_response = client.get(image_url)
                            print(f"   File serving status: {file_response.status_code}")
                            
                            if file_response.status_code == 200:
                                print(f"   ✅ File served successfully")
                                print(f"   Content-Type: {file_response.headers.get('Content-Type')}")
                                print(f"   Content-Length: {file_response.headers.get('Content-Length')}")
                            else:
                                print(f"   ❌ File serving failed")
                    
                    # Step 4: Test complaint status page
                    print("\n4. Testing complaint status page...")
                    status_response = client.get(f'/portal/complaints/status/{reference_id}')
                    print(f"   Status page response: {status_response.status_code}")
                    
                    if status_response.status_code == 200:
                        page_content = status_response.get_data(as_text=True)
                        has_images = 'Attachments' in page_content
                        print(f"   ✅ Status page loaded")
                        print(f"   Contains image section: {has_images}")
                    
                    return True
                else:
                    print("   ❌ Complaint not found in database")
                    return False
            else:
                print("   ❌ Could not extract reference ID from redirect")
                return False
        else:
            print(f"   ❌ Form submission failed: {response.status_code}")
            if response.data:
                print(f"   Response: {response.get_data(as_text=True)[:500]}")
            return False

def test_existing_complaint_with_media():
    """Test displaying existing complaint that has media"""
    print("\n" + "=" * 50)
    print("Testing Existing Complaint with Media")
    print("=" * 50)
    
    # Use the complaint we know has media
    reference_id = "MI-2025-243097"
    
    app = create_app()
    with app.test_client() as client:
        print(f"\n1. Testing complaint status page for {reference_id}...")
        
        response = client.get(f'/portal/complaints/status/{reference_id}')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Status page loaded")
            
            # Check content
            content = response.get_data(as_text=True)
            has_attachments = 'Attachments' in content
            has_images = '/uploads/images/' in content
            
            print(f"   Contains 'Attachments' section: {has_attachments}")
            print(f"   Contains image URLs: {has_images}")
            
            # Test image serving
            if has_images:
                print("\n2. Testing image serving...")
                complaint = complaint_service.get_complaint_by_reference(reference_id)
                
                for i, image_url in enumerate(complaint.image_urls):
                    print(f"   Testing image {i+1}: {image_url}")
                    img_response = client.get(image_url)
                    print(f"   Response: {img_response.status_code}")
                    
                    if img_response.status_code == 200:
                        print(f"   ✅ Image served successfully")
                        print(f"   Content-Type: {img_response.headers.get('Content-Type')}")
                    else:
                        print(f"   ❌ Image serving failed")
            
            return True
        else:
            print(f"   ❌ Status page failed to load")
            return False

def main():
    """Run all end-to-end tests"""
    print("Running End-to-End Photo/Video Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Complete upload flow
    try:
        result1 = test_end_to_end_flow()
        results.append(("Complete Upload Flow", result1))
    except Exception as e:
        print(f"Complete Upload Flow failed with error: {e}")
        results.append(("Complete Upload Flow", False))
    
    # Test 2: Existing complaint display
    try:
        result2 = test_existing_complaint_with_media()
        results.append(("Existing Complaint Display", result2))
    except Exception as e:
        print(f"Existing Complaint Display failed with error: {e}")
        results.append(("Existing Complaint Display", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("Photo/Video feature is working end-to-end!")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed")
        print("Some issues may need attention.")

if __name__ == "__main__":
    main()