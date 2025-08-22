from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class AnnouncementType(Enum):
    GENERAL = "general"
    MAINTENANCE = "maintenance"
    SERVICE_DISRUPTION = "service_disruption"
    EVENT = "event"
    EMERGENCY = "emergency"

class AnnouncementPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Announcement:
    title: str
    content: str
    municipality: str
    author: str
    announcement_type: AnnouncementType = AnnouncementType.GENERAL
    priority: AnnouncementPriority = AnnouncementPriority.MEDIUM
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    announcement_id: str = field(default_factory=lambda: f"ANN-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    areas_affected: List[str] = field(default_factory=list)  # Ward numbers or area names
    contact_info: Optional[str] = None
    
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def get_priority_display(self) -> str:
        priority_map = {
            AnnouncementPriority.LOW: "Low",
            AnnouncementPriority.MEDIUM: "Medium", 
            AnnouncementPriority.HIGH: "High",
            AnnouncementPriority.URGENT: "Urgent"
        }
        return priority_map.get(self.priority, "Unknown")
    
    def get_type_display(self) -> str:
        type_map = {
            AnnouncementType.GENERAL: "General",
            AnnouncementType.MAINTENANCE: "Maintenance",
            AnnouncementType.SERVICE_DISRUPTION: "Service Disruption",
            AnnouncementType.EVENT: "Event",
            AnnouncementType.EMERGENCY: "Emergency"
        }
        return type_map.get(self.announcement_type, "Unknown")
    
    def to_dict(self):
        return {
            "announcement_id": self.announcement_id,
            "title": self.title,
            "content": self.content,
            "municipality": self.municipality,
            "author": self.author,
            "announcement_type": self.announcement_type.value,
            "priority": self.priority.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "areas_affected": self.areas_affected,
            "contact_info": self.contact_info
        }

@dataclass 
class ServiceRating:
    service_type: str
    rating: int  # 1-5 stars
    municipality: str
    user_phone: str
    comment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    rating_id: str = field(default_factory=lambda: f"RAT-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    is_anonymous: bool = False
    
    def get_rating_display(self) -> str:
        stars = "⭐" * self.rating + "☆" * (5 - self.rating)
        return f"{stars} ({self.rating}/5)"
    
    def to_dict(self):
        return {
            "rating_id": self.rating_id,
            "service_type": self.service_type,
            "rating": self.rating,
            "municipality": self.municipality,
            "user_phone": self.user_phone if not self.is_anonymous else "Anonymous",
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
            "is_anonymous": self.is_anonymous
        }

@dataclass
class Poll:
    question: str
    options: List[str]
    municipality: str
    author: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    poll_id: str = field(default_factory=lambda: f"POLL-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    max_votes_per_user: int = 1
    areas_affected: List[str] = field(default_factory=list)
    votes: Dict[str, int] = field(default_factory=dict)  # option -> vote count
    voters: List[str] = field(default_factory=list)  # phone numbers of voters
    
    def __post_init__(self):
        # Initialize vote counts
        for option in self.options:
            if option not in self.votes:
                self.votes[option] = 0
    
    def add_vote(self, user_phone: str, option: str) -> bool:
        if not self.is_active or self.is_expired():
            return False
        
        if option not in self.options:
            return False
        
        # Check if user already voted
        if user_phone in self.voters and self.max_votes_per_user == 1:
            return False
        
        # Check if user reached vote limit
        user_vote_count = self.voters.count(user_phone)
        if user_vote_count >= self.max_votes_per_user:
            return False
        
        self.votes[option] += 1
        self.voters.append(user_phone)
        return True
    
    def get_results(self) -> Dict[str, Any]:
        total_votes = sum(self.votes.values())
        results = {}
        
        for option in self.options:
            vote_count = self.votes.get(option, 0)
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            results[option] = {
                'votes': vote_count,
                'percentage': round(percentage, 1)
            }
        
        return {
            'results': results,
            'total_votes': total_votes,
            'total_voters': len(set(self.voters))
        }
    
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def to_dict(self):
        return {
            "poll_id": self.poll_id,
            "question": self.question,
            "options": self.options,
            "municipality": self.municipality,
            "author": self.author,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "max_votes_per_user": self.max_votes_per_user,
            "areas_affected": self.areas_affected,
            "votes": self.votes,
            "voters": self.voters
        }