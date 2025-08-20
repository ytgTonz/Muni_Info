from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime, timedelta
from src.models.community import Announcement, ServiceRating, Poll, AnnouncementType, AnnouncementPriority

class CommunityRepository:
    def __init__(self):
        self.announcements_file = "data/announcements.json"
        self.ratings_file = "data/service_ratings.json"
        self.polls_file = "data/polls.json"
        self._ensure_data_files_exist()
    
    def _ensure_data_files_exist(self):
        for file_path in [self.announcements_file, self.ratings_file, self.polls_file]:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump({"data": []}, f)
    
    # Announcements
    def save_announcement(self, announcement: Announcement) -> Announcement:
        data = self._load_data(self.announcements_file)
        
        # Remove existing announcement with same ID
        data = [item for item in data if item.get("announcement_id") != announcement.announcement_id]
        data.append(announcement.to_dict())
        
        self._save_data(self.announcements_file, data)
        return announcement
    
    def get_active_announcements(self, municipality: str = None, limit: int = 50) -> List[Announcement]:
        data = self._load_data(self.announcements_file)
        announcements = []
        
        for item in data:
            announcement = self._dict_to_announcement(item)
            if announcement.is_active and not announcement.is_expired():
                if municipality is None or announcement.municipality == municipality:
                    announcements.append(announcement)
        
        # Sort by priority (urgent first) then by creation date (newest first)
        priority_order = {
            AnnouncementPriority.URGENT: 0,
            AnnouncementPriority.HIGH: 1,
            AnnouncementPriority.MEDIUM: 2,
            AnnouncementPriority.LOW: 3
        }
        
        announcements.sort(key=lambda x: (priority_order.get(x.priority, 4), -x.created_at.timestamp()))
        return announcements[:limit]
    
    def get_announcement_by_id(self, announcement_id: str) -> Optional[Announcement]:
        data = self._load_data(self.announcements_file)
        for item in data:
            if item.get("announcement_id") == announcement_id:
                return self._dict_to_announcement(item)
        return None
    
    # Service Ratings
    def save_rating(self, rating: ServiceRating) -> ServiceRating:
        data = self._load_data(self.ratings_file)
        data.append(rating.to_dict())
        self._save_data(self.ratings_file, data)
        return rating
    
    def get_service_ratings(self, service_type: str = None, municipality: str = None) -> List[ServiceRating]:
        data = self._load_data(self.ratings_file)
        ratings = []
        
        for item in data:
            rating = self._dict_to_rating(item)
            if (service_type is None or rating.service_type == service_type) and \
               (municipality is None or rating.municipality == municipality):
                ratings.append(rating)
        
        return sorted(ratings, key=lambda x: x.created_at, reverse=True)
    
    def get_average_rating(self, service_type: str, municipality: str) -> Dict[str, Any]:
        ratings = self.get_service_ratings(service_type, municipality)
        
        if not ratings:
            return {"average": 0, "count": 0, "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}
        
        total = sum(r.rating for r in ratings)
        average = total / len(ratings)
        
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            distribution[rating.rating] += 1
        
        return {
            "average": round(average, 1),
            "count": len(ratings),
            "distribution": distribution
        }
    
    # Polls
    def save_poll(self, poll: Poll) -> Poll:
        data = self._load_data(self.polls_file)
        
        # Remove existing poll with same ID
        data = [item for item in data if item.get("poll_id") != poll.poll_id]
        data.append(poll.to_dict())
        
        self._save_data(self.polls_file, data)
        return poll
    
    def get_active_polls(self, municipality: str = None) -> List[Poll]:
        data = self._load_data(self.polls_file)
        polls = []
        
        for item in data:
            poll = self._dict_to_poll(item)
            if poll.is_active and not poll.is_expired():
                if municipality is None or poll.municipality == municipality:
                    polls.append(poll)
        
        return sorted(polls, key=lambda x: x.created_at, reverse=True)
    
    def get_poll_by_id(self, poll_id: str) -> Optional[Poll]:
        data = self._load_data(self.polls_file)
        for item in data:
            if item.get("poll_id") == poll_id:
                return self._dict_to_poll(item)
        return None
    
    def vote_in_poll(self, poll_id: str, user_phone: str, option: str) -> bool:
        poll = self.get_poll_by_id(poll_id)
        if not poll:
            return False
        
        if poll.add_vote(user_phone, option):
            self.save_poll(poll)
            return True
        return False
    
    # Helper methods
    def _load_data(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data.get("data", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, file_path: str, data: List[Dict[str, Any]]):
        with open(file_path, 'w') as f:
            json.dump({"data": data}, f, indent=2)
    
    def _dict_to_announcement(self, data: Dict[str, Any]) -> Announcement:
        announcement = Announcement(
            title=data["title"],
            content=data["content"],
            municipality=data["municipality"],
            author=data["author"],
            announcement_id=data["announcement_id"]
        )
        
        announcement.announcement_type = AnnouncementType(data.get("announcement_type", "general"))
        announcement.priority = AnnouncementPriority(data.get("priority", "medium"))
        announcement.is_active = data.get("is_active", True)
        announcement.created_at = datetime.fromisoformat(data["created_at"])
        announcement.areas_affected = data.get("areas_affected", [])
        announcement.contact_info = data.get("contact_info")
        
        if data.get("expires_at"):
            announcement.expires_at = datetime.fromisoformat(data["expires_at"])
        
        return announcement
    
    def _dict_to_rating(self, data: Dict[str, Any]) -> ServiceRating:
        rating = ServiceRating(
            service_type=data["service_type"],
            rating=data["rating"],
            municipality=data["municipality"],
            user_phone=data["user_phone"],
            rating_id=data["rating_id"]
        )
        
        rating.comment = data.get("comment")
        rating.created_at = datetime.fromisoformat(data["created_at"])
        rating.is_anonymous = data.get("is_anonymous", False)
        
        return rating
    
    def _dict_to_poll(self, data: Dict[str, Any]) -> Poll:
        poll = Poll(
            question=data["question"],
            options=data["options"],
            municipality=data["municipality"],
            author=data["author"],
            poll_id=data["poll_id"]
        )
        
        poll.description = data.get("description")
        poll.is_active = data.get("is_active", True)
        poll.created_at = datetime.fromisoformat(data["created_at"])
        poll.max_votes_per_user = data.get("max_votes_per_user", 1)
        poll.areas_affected = data.get("areas_affected", [])
        poll.votes = data.get("votes", {})
        poll.voters = data.get("voters", [])
        
        if data.get("expires_at"):
            poll.expires_at = datetime.fromisoformat(data["expires_at"])
        
        return poll

class CommunityService:
    def __init__(self):
        self.repository = CommunityRepository()
    
    # Announcements
    def create_announcement(self, title: str, content: str, municipality: str, author: str,
                          announcement_type: AnnouncementType = AnnouncementType.GENERAL,
                          priority: AnnouncementPriority = AnnouncementPriority.MEDIUM,
                          expires_in_days: int = None, areas_affected: List[str] = None,
                          contact_info: str = None) -> Announcement:
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        announcement = Announcement(
            title=title,
            content=content,
            municipality=municipality,
            author=author,
            announcement_type=announcement_type,
            priority=priority,
            expires_at=expires_at,
            areas_affected=areas_affected or [],
            contact_info=contact_info
        )
        
        return self.repository.save_announcement(announcement)
    
    def get_announcements_for_user(self, municipality: str, user_area: str = None) -> List[Announcement]:
        announcements = self.repository.get_active_announcements(municipality)
        
        # Filter by user area if provided
        if user_area:
            filtered = []
            for announcement in announcements:
                if not announcement.areas_affected or user_area in announcement.areas_affected:
                    filtered.append(announcement)
            return filtered
        
        return announcements
    
    def format_announcement_for_whatsapp(self, announcement: Announcement) -> str:
        message = f"{announcement.get_type_display()} {announcement.get_priority_display()}\n\n"
        message += f"*{announcement.title}*\n\n"
        message += f"{announcement.content}\n\n"
        
        if announcement.areas_affected:
            message += f"*Areas:* {', '.join(announcement.areas_affected)}\n"
        
        if announcement.contact_info:
            message += f"*Contact:* {announcement.contact_info}\n"
        
        message += f"*Posted:* {announcement.created_at.strftime('%d %b %Y')}"
        
        if announcement.expires_at:
            message += f"\n*Expires:* {announcement.expires_at.strftime('%d %b %Y')}"
        
        return message
    
    # Service Ratings
    def submit_rating(self, service_type: str, rating: int, municipality: str, user_phone: str,
                     comment: str = None, is_anonymous: bool = False) -> ServiceRating:
        
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        service_rating = ServiceRating(
            service_type=service_type,
            rating=rating,
            municipality=municipality,
            user_phone=user_phone,
            comment=comment,
            is_anonymous=is_anonymous
        )
        
        return self.repository.save_rating(service_rating)
    
    def get_service_rating_summary(self, municipality: str) -> Dict[str, Any]:
        service_types = ["Water", "Electricity", "Sanitation", "Roads", "General Services"]
        summary = {}
        
        for service_type in service_types:
            rating_data = self.repository.get_average_rating(service_type, municipality)
            summary[service_type] = rating_data
        
        return summary
    
    def format_rating_request(self, service_types: List[str]) -> str:
        message = "📊 *Rate Our Services*\n\n"
        message += "Help us improve by rating our services:\n\n"
        
        for i, service in enumerate(service_types, 1):
            message += f"{i}. {service}\n"
        
        message += "\nReply with the number to rate that service."
        return message
    
    # Polls
    def create_poll(self, question: str, options: List[str], municipality: str, author: str,
                   description: str = None, expires_in_days: int = 30,
                   areas_affected: List[str] = None) -> Poll:
        
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        poll = Poll(
            question=question,
            options=options,
            municipality=municipality,
            author=author,
            description=description,
            expires_at=expires_at,
            areas_affected=areas_affected or []
        )
        
        return self.repository.save_poll(poll)
    
    def vote_in_poll(self, poll_id: str, user_phone: str, option_number: int) -> bool:
        poll = self.repository.get_poll_by_id(poll_id)
        if not poll:
            return False
        
        if option_number < 1 or option_number > len(poll.options):
            return False
        
        option = poll.options[option_number - 1]
        return self.repository.vote_in_poll(poll_id, user_phone, option)
    
    def format_poll_for_whatsapp(self, poll: Poll) -> str:
        message = f"📊 *Community Poll*\n\n"
        message += f"*{poll.question}*\n\n"
        
        if poll.description:
            message += f"{poll.description}\n\n"
        
        for i, option in enumerate(poll.options, 1):
            message += f"{i}. {option}\n"
        
        message += f"\nReply with the number (1-{len(poll.options)}) to vote."
        message += f"\nPoll ID: {poll.poll_id}"
        
        if poll.expires_at:
            message += f"\nExpires: {poll.expires_at.strftime('%d %b %Y')}"
        
        return message
    
    def format_poll_results(self, poll: Poll) -> str:
        results = poll.get_results()
        
        message = f"📊 *Poll Results*\n\n"
        message += f"*{poll.question}*\n\n"
        
        for option in poll.options:
            result = results['results'][option]
            bar = "█" * int(result['percentage'] / 10) + "░" * (10 - int(result['percentage'] / 10))
            message += f"{option}\n{bar} {result['percentage']}% ({result['votes']} votes)\n\n"
        
        message += f"Total voters: {results['total_voters']}"
        return message

community_service = CommunityService()