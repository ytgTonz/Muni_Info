from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class UserRole(Enum):
    ADMIN = "admin"
    MUNICIPAL_STAFF = "municipal_staff"
    SUPERVISOR = "supervisor"
    CITIZEN = "citizen"

@dataclass
class User(UserMixin):
    username: str
    email: str
    phone_number: str
    full_name: str
    password_hash: str = ""
    role: UserRole = UserRole.CITIZEN
    municipality: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    user_id: str = field(default_factory=lambda: str(datetime.now().timestamp()).replace('.', ''))
    
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.user_id
    
    def has_role(self, role: UserRole) -> bool:
        return self.role == role
    
    def can_manage_complaints(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.MUNICIPAL_STAFF, UserRole.SUPERVISOR]
    
    def can_access_dashboard(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.MUNICIPAL_STAFF, UserRole.SUPERVISOR]
    
    def can_manage_users(self) -> bool:
        return self.role in [UserRole.ADMIN, UserRole.SUPERVISOR]
    
    def get_role_display(self) -> str:
        """Get a human-readable role name"""
        role_names = {
            UserRole.ADMIN: "Administrator",
            UserRole.MUNICIPAL_STAFF: "Municipal Staff",
            UserRole.SUPERVISOR: "Supervisor",
            UserRole.CITIZEN: "Citizen"
        }
        return role_names.get(self.role, self.role.value.title())
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "phone_number": self.phone_number,
            "full_name": self.full_name,
            "role": self.role.value,
            "municipality": self.municipality,
            "department": self.department,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }