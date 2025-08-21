from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os
from src.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from src.config import Config

class ComplaintRepository:
    def __init__(self, data_file: str = "data/complaints.json"):
        self.data_file = data_file
        self._ensure_data_file_exists()
    
    def _ensure_data_file_exists(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"complaints": []}, f)
    
    def _load_complaints(self) -> List[Dict[str, Any]]:
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return data.get("complaints", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_complaints(self, complaints: List[Dict[str, Any]]):
        with open(self.data_file, 'w') as f:
            json.dump({"complaints": complaints}, f, indent=2)
    
    def _dict_to_complaint(self, data: Dict[str, Any]) -> Complaint:
        complaint = Complaint(
            sender=data["sender"],
            complaint_type=data["complaint_type"],
            description=data["description"],
            reference_id=data["reference_id"]
        )
        
        complaint.status = ComplaintStatus(data.get("status", "submitted"))
        complaint.priority = ComplaintPriority(data.get("priority", "medium"))
        complaint.timestamp = datetime.fromisoformat(data["timestamp"])
        complaint.updated_at = datetime.fromisoformat(data.get("updated_at", data["timestamp"]))
        complaint.image_urls = data.get("image_urls", [])
        complaint.assigned_to = data.get("assigned_to")
        complaint.resolution_notes = data.get("resolution_notes")
        complaint.location_info = data.get("location_info")
        
        return complaint
    
    def save_complaint(self, complaint: Complaint) -> Complaint:
        complaints = self._load_complaints()
        
        existing_index = None
        for i, comp_data in enumerate(complaints):
            if comp_data["reference_id"] == complaint.reference_id:
                existing_index = i
                break
        
        complaint_dict = complaint.to_dict()
        
        if existing_index is not None:
            complaints[existing_index] = complaint_dict
        else:
            complaints.append(complaint_dict)
        
        self._save_complaints(complaints)
        return complaint
    
    def get_complaint_by_reference(self, reference_id: str) -> Optional[Complaint]:
        complaints = self._load_complaints()
        for comp_data in complaints:
            if comp_data["reference_id"] == reference_id:
                return self._dict_to_complaint(comp_data)
        return None
    
    def get_complaints_by_sender(self, sender: str) -> List[Complaint]:
        complaints = self._load_complaints()
        user_complaints = []
        
        for comp_data in complaints:
            if comp_data["sender"] == sender:
                user_complaints.append(self._dict_to_complaint(comp_data))
        
        return sorted(user_complaints, key=lambda x: x.timestamp, reverse=True)
    
    def get_all_complaints(self) -> List[Complaint]:
        complaints = self._load_complaints()
        return [self._dict_to_complaint(comp_data) for comp_data in complaints]
    
    def get_complaints_by_status(self, status: ComplaintStatus) -> List[Complaint]:
        complaints = self._load_complaints()
        filtered_complaints = []
        
        for comp_data in complaints:
            if comp_data.get("status") == status.value:
                filtered_complaints.append(self._dict_to_complaint(comp_data))
        
        return sorted(filtered_complaints, key=lambda x: x.timestamp, reverse=True)
    
    def get_complaints_by_priority(self, priority: ComplaintPriority) -> List[Complaint]:
        complaints = self._load_complaints()
        filtered_complaints = []
        
        for comp_data in complaints:
            if comp_data.get("priority") == priority.value:
                filtered_complaints.append(self._dict_to_complaint(comp_data))
        
        return sorted(filtered_complaints, key=lambda x: x.timestamp, reverse=True)
    
    def get_recent_complaints(self, days: int = 7) -> List[Complaint]:
        cutoff_date = datetime.now() - timedelta(days=days)
        complaints = self._load_complaints()
        recent_complaints = []
        
        for comp_data in complaints:
            complaint_date = datetime.fromisoformat(comp_data["timestamp"])
            if complaint_date >= cutoff_date:
                recent_complaints.append(self._dict_to_complaint(comp_data))
        
        return sorted(recent_complaints, key=lambda x: x.timestamp, reverse=True)
    
    def update_complaint_status(self, reference_id: str, new_status: ComplaintStatus, notes: Optional[str] = None) -> Optional[Complaint]:
        complaint = self.get_complaint_by_reference(reference_id)
        if complaint:
            complaint.update_status(new_status, notes)
            return self.save_complaint(complaint)
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        complaints = self._load_complaints()
        
        total = len(complaints)
        if total == 0:
            return {
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "by_type": {}
            }
        
        stats = {
            "total": total,
            "by_status": {},
            "by_priority": {},
            "by_type": {}
        }
        
        for comp_data in complaints:
            status = comp_data.get("status", "submitted")
            priority = comp_data.get("priority", "medium")
            comp_type = comp_data.get("complaint_type", "Other")
            
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            stats["by_type"][comp_type] = stats["by_type"].get(comp_type, 0) + 1
        
        return stats
    
    def get_complaints_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Complaint]:
        """Get complaints within a specific date range for analytics"""
        complaints = self._load_complaints()
        filtered_complaints = []
        
        for comp_data in complaints:
            try:
                complaint_date = datetime.fromisoformat(comp_data["timestamp"])
                if start_date <= complaint_date <= end_date:
                    filtered_complaints.append(self._dict_to_complaint(comp_data))
            except (KeyError, ValueError):
                # Skip complaints with invalid timestamps
                continue
        
        return sorted(filtered_complaints, key=lambda x: x.timestamp, reverse=True)

complaint_repository = ComplaintRepository()