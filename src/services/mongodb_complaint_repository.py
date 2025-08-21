from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError
import logging

from src.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from src.services.database_service import db_service

logger = logging.getLogger(__name__)

class MongoDBComplaintRepository:
    def __init__(self):
        self.collection = db_service.get_collection('complaints')
    
    def save_complaint(self, complaint: Complaint) -> Complaint:
        """Save a complaint to MongoDB"""
        try:
            complaint_data = complaint.to_mongo_dict()
            
            if complaint._id:
                # Update existing complaint
                result = self.collection.replace_one(
                    {"_id": complaint._id}, 
                    complaint_data
                )
                if result.matched_count == 0:
                    raise ValueError(f"Complaint with id {complaint._id} not found")
            else:
                # Insert new complaint
                result = self.collection.insert_one(complaint_data)
                complaint._id = result.inserted_id
            
            logger.info(f"Complaint {complaint.reference_id} saved successfully")
            return complaint
            
        except DuplicateKeyError:
            raise ValueError(f"Complaint with reference ID {complaint.reference_id} already exists")
        except Exception as e:
            logger.error(f"Error saving complaint: {e}")
            raise
    
    def get_complaint_by_reference(self, reference_id: str) -> Optional[Complaint]:
        """Get complaint by reference ID"""
        try:
            document = self.collection.find_one({"reference_id": reference_id})
            return Complaint.from_mongo_dict(document)
        except Exception as e:
            logger.error(f"Error retrieving complaint {reference_id}: {e}")
            return None
    
    def get_complaint_by_id(self, complaint_id) -> Optional[Complaint]:
        """Get complaint by MongoDB ObjectId"""
        try:
            document = self.collection.find_one({"_id": complaint_id})
            return Complaint.from_mongo_dict(document)
        except Exception as e:
            logger.error(f"Error retrieving complaint by ID {complaint_id}: {e}")
            return None
    
    def get_complaints_by_sender(self, sender: str, limit: int = 50) -> List[Complaint]:
        """Get all complaints by a specific sender"""
        try:
            documents = self.collection.find(
                {"sender": sender}
            ).sort("timestamp", -1).limit(limit)
            
            return [Complaint.from_mongo_dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error retrieving complaints for sender {sender}: {e}")
            return []
    
    def get_complaints_by_status(self, status: ComplaintStatus, limit: int = 50) -> List[Complaint]:
        """Get complaints by status"""
        try:
            documents = self.collection.find(
                {"status": status.value}
            ).sort("timestamp", -1).limit(limit)
            
            return [Complaint.from_mongo_dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error retrieving complaints by status {status}: {e}")
            return []
    
    def get_all_complaints(self, limit: int = 100, skip: int = 0, 
                          status_filter: Optional[str] = None,
                          type_filter: Optional[str] = None,
                          priority_filter: Optional[str] = None) -> List[Complaint]:
        """Get all complaints with optional filtering"""
        try:
            query = {}
            
            if status_filter:
                query["status"] = status_filter
            if type_filter:
                query["complaint_type"] = type_filter
            if priority_filter:
                query["priority"] = priority_filter
            
            documents = self.collection.find(query).sort(
                "timestamp", -1
            ).skip(skip).limit(limit)
            
            return [Complaint.from_mongo_dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error retrieving complaints: {e}")
            return []
    
    def get_complaint_count(self, status_filter: Optional[str] = None,
                           type_filter: Optional[str] = None,
                           priority_filter: Optional[str] = None) -> int:
        """Get total count of complaints with optional filtering"""
        try:
            query = {}
            
            if status_filter:
                query["status"] = status_filter
            if type_filter:
                query["complaint_type"] = type_filter
            if priority_filter:
                query["priority"] = priority_filter
            
            return self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting complaints: {e}")
            return 0
    
    def update_complaint_status(self, reference_id: str, new_status: ComplaintStatus, 
                               notes: Optional[str] = None) -> bool:
        """Update complaint status"""
        try:
            update_data = {
                "status": new_status.value,
                "updated_at": datetime.now()
            }
            
            if notes:
                update_data["resolution_notes"] = notes
            
            result = self.collection.update_one(
                {"reference_id": reference_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating complaint status: {e}")
            return False
    
    def delete_complaint(self, reference_id: str) -> bool:
        """Delete a complaint by reference ID"""
        try:
            result = self.collection.delete_one({"reference_id": reference_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting complaint {reference_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get complaint statistics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            status_counts = {}
            for result in self.collection.aggregate(pipeline):
                status_counts[result["_id"]] = result["count"]
            
            total_count = self.collection.count_documents({})
            
            # Get statistics by type
            type_pipeline = [
                {
                    "$group": {
                        "_id": "$complaint_type",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            type_counts = {}
            for result in self.collection.aggregate(type_pipeline):
                type_counts[result["_id"]] = result["count"]
            
            # Get statistics by priority
            priority_pipeline = [
                {
                    "$group": {
                        "_id": "$priority",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            priority_counts = {}
            for result in self.collection.aggregate(priority_pipeline):
                priority_counts[result["_id"]] = result["count"]
            
            return {
                "total": total_count,
                "by_status": status_counts,
                "by_type": type_counts,
                "by_priority": priority_counts
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "total": 0,
                "by_status": {},
                "by_type": {},
                "by_priority": {}
            }
    
    def get_recent_complaints(self, days: int = 7, limit: int = 10) -> List[Complaint]:
        """Get recent complaints from the last N days"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            documents = self.collection.find(
                {"timestamp": {"$gte": since_date}}
            ).sort("timestamp", -1).limit(limit)
            
            return [Complaint.from_mongo_dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error retrieving recent complaints: {e}")
            return []
    
    def search_complaints(self, search_term: str, limit: int = 50) -> List[Complaint]:
        """Search complaints by text"""
        try:
            # Create text search query
            query = {
                "$or": [
                    {"description": {"$regex": search_term, "$options": "i"}},
                    {"complaint_type": {"$regex": search_term, "$options": "i"}},
                    {"reference_id": {"$regex": search_term, "$options": "i"}},
                    {"sender": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            documents = self.collection.find(query).sort(
                "timestamp", -1
            ).limit(limit)
            
            return [Complaint.from_mongo_dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error searching complaints: {e}")
            return []

# Global repository instance
mongodb_complaint_repository = MongoDBComplaintRepository()