import os
import uuid
import requests
from typing import Optional, List
from datetime import datetime
from src.config import Config

class MediaService:
    def __init__(self):
        self.media_dir = "data/media"
        self._ensure_media_dir_exists()
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def _ensure_media_dir_exists(self):
        os.makedirs(self.media_dir, exist_ok=True)
    
    def _generate_filename(self, original_filename: str = None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        if original_filename:
            name, ext = os.path.splitext(original_filename)
            return f"{timestamp}_{unique_id}{ext.lower()}"
        else:
            return f"{timestamp}_{unique_id}"
    
    def _is_allowed_file(self, filename: str) -> bool:
        if not filename:
            return False
        _, ext = os.path.splitext(filename.lower())
        return ext in self.allowed_extensions
    
    def download_media_from_twilio(self, media_url: str, auth_token: str, account_sid: str) -> Optional[str]:
        try:
            response = requests.get(
                media_url,
                auth=(account_sid, auth_token),
                timeout=30
            )
            response.raise_for_status()
            
            if len(response.content) > self.max_file_size:
                print(f"File too large: {len(response.content)} bytes")
                return None
            
            content_type = response.headers.get('content-type', '')
            extension = self._get_extension_from_content_type(content_type)
            
            filename = self._generate_filename() + extension
            file_path = os.path.join(self.media_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except requests.RequestException as e:
            print(f"Error downloading media: {e}")
            return None
        except Exception as e:
            print(f"Error saving media: {e}")
            return None
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'video/mp4': '.mp4',
            'video/quicktime': '.mov',
            'video/x-msvideo': '.avi'
        }
        return content_type_map.get(content_type.lower(), '.jpg')
    
    def save_uploaded_file(self, file_content: bytes, filename: str = None) -> Optional[str]:
        try:
            if len(file_content) > self.max_file_size:
                print(f"File too large: {len(file_content)} bytes")
                return None
            
            if filename and not self._is_allowed_file(filename):
                print(f"File type not allowed: {filename}")
                return None
            
            save_filename = self._generate_filename(filename)
            file_path = os.path.join(self.media_dir, save_filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            return file_path
            
        except Exception as e:
            print(f"Error saving uploaded file: {e}")
            return None
    
    def get_media_info(self, file_path: str) -> Optional[dict]:
        try:
            if not os.path.exists(file_path):
                return None
            
            stats = os.stat(file_path)
            filename = os.path.basename(file_path)
            _, ext = os.path.splitext(filename.lower())
            
            media_type = "image" if ext in {'.jpg', '.jpeg', '.png', '.gif'} else "video"
            
            return {
                "filename": filename,
                "file_path": file_path,
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime),
                "media_type": media_type,
                "extension": ext
            }
            
        except Exception as e:
            print(f"Error getting media info: {e}")
            return None
    
    def delete_media_file(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting media file: {e}")
            return False
    
    def get_media_url(self, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            return None
        
        filename = os.path.basename(file_path)
        return f"/media/{filename}"
    
    def cleanup_old_media(self, days_old: int = 30):
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            for filename in os.listdir(self.media_dir):
                file_path = os.path.join(self.media_dir, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            print(f"Error deleting old file {filename}: {e}")
            
            print(f"Cleaned up {deleted_count} old media files")
            return deleted_count
            
        except Exception as e:
            print(f"Error during media cleanup: {e}")
            return 0

media_service = MediaService()