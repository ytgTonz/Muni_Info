from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid
from bson import ObjectId

class ComplaintStatus(Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ComplaintPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Complaint:
    sender: str
    complaint_type: str
    description: str
    reference_id: str = field(default_factory=lambda: f"MI-{datetime.now().year}-{str(uuid.uuid4().int)[:6]}")
    status: ComplaintStatus = ComplaintStatus.SUBMITTED
    priority: ComplaintPriority = ComplaintPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    image_urls: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    location_info: Optional[dict] = None
    ai_analysis: Optional[dict] = field(default_factory=dict)
    _id: Optional[ObjectId] = None  # MongoDB document ID
    
    def update_status(self, new_status: ComplaintStatus, notes: Optional[str] = None):
        self.status = new_status
        self.updated_at = datetime.now()
        if notes:
            self.resolution_notes = notes
    
    def add_image(self, image_url: str):
        if image_url not in self.image_urls:
            self.image_urls.append(image_url)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "reference_id": self.reference_id,
            "sender": self.sender,
            "complaint_type": self.complaint_type,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "image_urls": self.image_urls,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "location_info": self.location_info,
            "ai_analysis": self.ai_analysis
        }
    
    def to_mongo_dict(self):
        """Convert to dictionary for MongoDB storage"""
        mongo_dict = {
            "reference_id": self.reference_id,
            "sender": self.sender,
            "complaint_type": self.complaint_type,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "updated_at": self.updated_at,
            "image_urls": self.image_urls,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "location_info": self.location_info,
            "ai_analysis": self.ai_analysis
        }
        
        # Include _id if it exists
        if self._id:
            mongo_dict["_id"] = self._id
            
        return mongo_dict
    
    @classmethod
    def from_mongo_dict(cls, data):
        """Create Complaint instance from MongoDB document"""
        if not data:
            return None
            
        complaint = cls(
            sender=data.get("sender", ""),
            complaint_type=data.get("complaint_type", ""),
            description=data.get("description", ""),
            reference_id=data.get("reference_id", ""),
            status=ComplaintStatus(data.get("status", "submitted")),
            priority=ComplaintPriority(data.get("priority", "medium")),
            timestamp=data.get("timestamp", datetime.now()),
            updated_at=data.get("updated_at", datetime.now()),
            image_urls=data.get("image_urls", []),
            assigned_to=data.get("assigned_to"),
            resolution_notes=data.get("resolution_notes"),
            location_info=data.get("location_info"),
            ai_analysis=data.get("ai_analysis", {}),
            _id=data.get("_id")
        )
        
        return complaint
    
    def get_status_display(self) -> str:
        status_map = {
            ComplaintStatus.SUBMITTED: "Submitted",
            ComplaintStatus.IN_PROGRESS: "In Progress", 
            ComplaintStatus.UNDER_REVIEW: "Under Review",
            ComplaintStatus.RESOLVED: "Resolved",
            ComplaintStatus.CLOSED: "Closed"
        }
        return status_map.get(self.status, "Unknown")
    
    def get_priority_display(self) -> str:
        priority_map = {
            ComplaintPriority.LOW: "Low",
            ComplaintPriority.MEDIUM: "Medium",
            ComplaintPriority.HIGH: "High", 
            ComplaintPriority.URGENT: "Urgent"
        }
        return priority_map.get(self.priority, "Unknown")