from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from src.models.user import User, UserRole
from flask_login import LoginManager

class UserRepository:
    def __init__(self, data_file: str = "data/users.json"):
        self.data_file = data_file
        self._ensure_data_file_exists()
        self._create_default_admin()
    
    def _ensure_data_file_exists(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"users": []}, f)
    
    def _create_default_admin(self):
        """Create default admin user if none exists"""
        if not self.get_user_by_username("admin"):
            admin_user = User(
                username="admin",
                email="admin@muniinfo.gov.za",
                phone_number="+27123456789",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                municipality="System",
                department="IT"
            )
            admin_user.set_password("admin123")  # Change this in production!
            self.save_user(admin_user)
    
    def _load_users(self) -> List[Dict[str, Any]]:
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return data.get("users", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_users(self, users: List[Dict[str, Any]]):
        with open(self.data_file, 'w') as f:
            json.dump({"users": users}, f, indent=2)
    
    def _dict_to_user(self, data: Dict[str, Any]) -> User:
        user = User(
            username=data["username"],
            email=data["email"],
            phone_number=data["phone_number"],
            full_name=data["full_name"],
            password_hash=data.get("password_hash", ""),
            user_id=data.get("user_id", str(datetime.now().timestamp()).replace('.', ''))
        )
        
        user.role = UserRole(data.get("role", "citizen"))
        user.municipality = data.get("municipality")
        user.department = data.get("department")
        user.is_active = data.get("is_active", True)
        user.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        
        if data.get("last_login"):
            user.last_login = datetime.fromisoformat(data["last_login"])
        
        return user
    
    def save_user(self, user: User) -> User:
        users = self._load_users()
        
        existing_index = None
        for i, user_data in enumerate(users):
            if user_data["user_id"] == user.user_id:
                existing_index = i
                break
        
        user_dict = user.to_dict()
        user_dict["password_hash"] = user.password_hash
        
        if existing_index is not None:
            users[existing_index] = user_dict
        else:
            users.append(user_dict)
        
        self._save_users(users)
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        users = self._load_users()
        for user_data in users:
            if user_data["user_id"] == user_id:
                return self._dict_to_user(user_data)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        users = self._load_users()
        for user_data in users:
            if user_data["username"].lower() == username.lower():
                return self._dict_to_user(user_data)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        users = self._load_users()
        for user_data in users:
            if user_data["email"].lower() == email.lower():
                return self._dict_to_user(user_data)
        return None
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        users = self._load_users()
        role_users = []
        
        for user_data in users:
            if user_data.get("role") == role.value:
                role_users.append(self._dict_to_user(user_data))
        
        return role_users
    
    def get_all_users(self) -> List[User]:
        users = self._load_users()
        return [self._dict_to_user(user_data) for user_data in users]
    
    def update_last_login(self, user_id: str):
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.now()
            self.save_user(user)
    
    def deactivate_user(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = False
            self.save_user(user)
            return True
        return False
    
    def activate_user(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = True
            self.save_user(user)
            return True
        return False

class UserService:
    def __init__(self):
        self.repository = UserRepository()
        self.login_manager = LoginManager()
        self.login_manager.login_view = 'admin.login'
        self.login_manager.login_message = 'Please log in to access this page.'
    
    def init_app(self, app):
        self.login_manager.init_app(app)
        
        @self.login_manager.user_loader
        def load_user(user_id):
            return self.repository.get_user_by_id(user_id)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.repository.get_user_by_username(username)
        if user and user.is_active and user.check_password(password):
            self.repository.update_last_login(user.user_id)
            return user
        return None
    
    def create_user(self, username: str, email: str, phone_number: str, 
                   full_name: str, password: str, role: UserRole = UserRole.CITIZEN,
                   municipality: str = None, department: str = None) -> Optional[User]:
        
        # Check if username or email already exists
        if self.repository.get_user_by_username(username):
            raise ValueError("Username already exists")
        
        if self.repository.get_user_by_email(email):
            raise ValueError("Email already exists")
        
        user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            role=role,
            municipality=municipality,
            department=department
        )
        user.set_password(password)
        
        return self.repository.save_user(user)
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        all_users = self.repository.get_all_users()
        
        return {
            "total_users": len(all_users),
            "active_users": len([u for u in all_users if u.is_active]),
            "admin_users": len([u for u in all_users if u.role == UserRole.ADMIN]),
            "staff_users": len([u for u in all_users if u.role == UserRole.MUNICIPAL_STAFF]),
            "citizen_users": len([u for u in all_users if u.role == UserRole.CITIZEN]),
        }

user_service = UserService()