#!/usr/bin/env python3
"""
Test Flask file serving functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from src.app import create_app
from src.services.media_service import media_service

def test_file_serving():
    """Test that file serving route works"""
    app = create_app()
    
    with app.test_client() as client:
        # Test if the route exists
        test_url = '/uploads/images/MI-2025-142630/20250822_095723_0006c69f.png'
        print(f"Testing URL: {test_url}")
        
        response = client.get(test_url)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print("ERROR: File serving not working")
            
            # Debug: check if files exist
            file_path = 'uploads/images/MI-2025-142630/20250822_095723_0006c69f.png'
            print(f"File exists: {os.path.exists(file_path)}")
            print(f"Upload folder: {media_service.upload_folder}")
            print(f"Upload folder exists: {os.path.exists(media_service.upload_folder)}")
            
            # Test send_from_directory directly
            try:
                from flask import send_from_directory
                with app.app_context():
                    test_response = send_from_directory(
                        media_service.upload_folder, 
                        'images/MI-2025-142630/20250822_095723_0006c69f.png'
                    )
                    print(f"Direct send_from_directory works: {test_response}")
            except Exception as e:
                print(f"Direct send_from_directory error: {e}")
        else:
            print("SUCCESS: File serving working!")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {response.headers.get('Content-Length')}")

if __name__ == "__main__":
    test_file_serving()