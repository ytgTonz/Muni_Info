#!/usr/bin/env python3
"""
Quick test script to verify MongoDB connection and complaint functionality
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        from src.services.database_service import db_service
        
        # Test connection
        collection = db_service.get_collection('test')
        result = collection.insert_one({"test": "connection", "timestamp": "2024-01-01"})
        print(f"[OK] MongoDB connection successful. Test document ID: {result.inserted_id}")
        
        # Clean up test document
        collection.delete_one({"_id": result.inserted_id})
        print("[OK] Test document cleaned up")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        return False

def test_complaint_creation():
    """Test complaint creation with MongoDB"""
    try:
        from src.services.complaint_service import complaint_service
        from src.models.complaint import ComplaintPriority
        
        # Create a test complaint
        complaint = complaint_service.create_complaint(
            sender="0123456789",
            complaint_type="Water",
            description="Test water leak at 123 Main Street - urgent repair needed",
            priority=ComplaintPriority.HIGH
        )
        
        print("[OK] Complaint created successfully!")
        print(f"   Reference ID: {complaint.reference_id}")
        print(f"   Status: {complaint.get_status_display()}")
        print(f"   Priority: {complaint.get_priority_display()}")
        print(f"   MongoDB ID: {complaint._id}")
        
        # Test retrieval
        retrieved = complaint_service.get_complaint_by_reference(complaint.reference_id)
        if retrieved:
            print("[OK] Complaint retrieval successful")
            print(f"   Retrieved ID: {retrieved.reference_id}")
        else:
            print("[ERROR] Could not retrieve complaint")
            return False
        
        # Test statistics
        stats = complaint_service.repository.get_statistics()
        print(f"[OK] Statistics retrieved: {stats['total']} total complaints")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Complaint creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Testing MongoDB Integration for Muni-Info")
    print("=" * 50)
    
    # Test 1: MongoDB Connection
    print("\n1. Testing MongoDB Connection...")
    connection_ok = test_mongodb_connection()
    
    if not connection_ok:
        print("[ERROR] Cannot proceed without MongoDB connection")
        return
    
    # Test 2: Complaint Creation
    print("\n2. Testing Complaint Creation...")
    complaint_ok = test_complaint_creation()
    
    print("\n" + "=" * 50)
    if connection_ok and complaint_ok:
        print("[SUCCESS] All tests passed! MongoDB integration is working correctly.")
        print("\nYou can now:")
        print("   - Submit complaints through the web portal")
        print("   - View complaint statistics")
        print("   - Track complaint status")
        print("   - Access the admin dashboard")
    else:
        print("[ERROR] Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()