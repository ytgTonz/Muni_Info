from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Complaint:
    sender: str
    complaint_type: str
    description: str
    timestamp: datetime = None
    image_url: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            "sender": self.sender,
            "complaint_type": self.complaint_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "image_url": self.image_url
        }