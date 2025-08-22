import os
import uuid
import hashlib
import requests
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
import io
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import mimetypes
import logging
from src.config import Config

# Try to import PIL, but gracefully handle if it's not available
try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    # Create mock classes for when PIL is not available
    class Image:
        @staticmethod
        def open(*args, **kwargs):
            raise ImportError("PIL/Pillow not available")
        
        @staticmethod
        def new(*args, **kwargs):
            raise ImportError("PIL/Pillow not available")
    
    class ImageOps:
        @staticmethod
        def exif_transpose(*args, **kwargs):
            raise ImportError("PIL/Pillow not available")

logger = logging.getLogger(__name__)

class MediaService:
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', '3gp'}
    ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS
    
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Image compression settings
    IMAGE_QUALITY = 85
    MAX_IMAGE_DIMENSION = 1920
    THUMBNAIL_SIZE = (300, 300)
    
    def __init__(self, upload_folder: str = 'uploads'):
        self.upload_folder = upload_folder
        self.media_dir = "data/media"  # Keep for backward compatibility
        self._ensure_media_dir_exists()
        self.ensure_upload_directories()
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not available - image compression and thumbnails disabled")
    
    def is_image_processing_available(self) -> bool:
        """Check if image processing (PIL/Pillow) is available"""
        return PIL_AVAILABLE
    
    def _ensure_media_dir_exists(self):
        os.makedirs(self.media_dir, exist_ok=True)
    
    def ensure_upload_directories(self):
        """Create necessary upload directories"""
        directories = [
            self.upload_folder,
            os.path.join(self.upload_folder, 'images'),
            os.path.join(self.upload_folder, 'videos'),
            os.path.join(self.upload_folder, 'thumbnails'),
            os.path.join(self.upload_folder, 'temp')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS)
    
    def get_file_type(self, filename: str) -> str:
        """Determine if file is image or video"""
        if not filename:
            return 'unknown'
        
        extension = filename.rsplit('.', 1)[1].lower()
        if extension in self.ALLOWED_IMAGE_EXTENSIONS:
            return 'image'
        elif extension in self.ALLOWED_VIDEO_EXTENSIONS:
            return 'video'
        return 'unknown'
    
    def validate_file(self, file: FileStorage) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not file:
            return False, "No file provided"
        
        if file.filename == '':
            return False, "No file selected"
        
        if not self.is_allowed_file(file.filename):
            return False, f"File type not allowed. Supported types: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        file_type = self.get_file_type(file.filename)
        
        if file_type == 'image' and file_size > self.MAX_IMAGE_SIZE:
            return False, f"Image file too large. Maximum size: {self.MAX_IMAGE_SIZE // (1024*1024)}MB"
        
        if file_type == 'video' and file_size > self.MAX_VIDEO_SIZE:
            return False, f"Video file too large. Maximum size: {self.MAX_VIDEO_SIZE // (1024*1024)}MB"
        
        # Validate image content if PIL is available
        if file_type == 'image' and PIL_AVAILABLE:
            try:
                file.seek(0)
                Image.open(file.stream).verify()
                file.seek(0)
            except Exception as e:
                return False, f"Invalid image file: {str(e)}"
        
        return True, "File is valid"
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename while preserving extension"""
        name, ext = os.path.splitext(secure_filename(original_filename))
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{unique_id}{ext}"
    
    def compress_image(self, image_data: bytes, filename: str) -> Tuple[bytes, Dict[str, Any]]:
        """Compress and optimize image"""
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not available - returning original image data")
            return image_data, {'error': 'PIL/Pillow not available for image compression'}
        
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert RGBA to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Auto-rotate based on EXIF orientation
            image = ImageOps.exif_transpose(image)
            
            # Resize if too large
            original_size = image.size
            if max(image.size) > self.MAX_IMAGE_DIMENSION:
                image.thumbnail((self.MAX_IMAGE_DIMENSION, self.MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
            
            # Compress image
            output = io.BytesIO()
            format = 'JPEG'
            if filename.lower().endswith('.png'):
                format = 'PNG'
            
            image.save(output, format=format, quality=self.IMAGE_QUALITY, optimize=True)
            compressed_data = output.getvalue()
            
            metadata = {
                'original_size': original_size,
                'compressed_size': image.size,
                'original_bytes': len(image_data),
                'compressed_bytes': len(compressed_data),
                'compression_ratio': len(image_data) / len(compressed_data) if len(compressed_data) > 0 else 1,
                'format': format
            }
            
            return compressed_data, metadata
            
        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            return image_data, {'error': str(e)}
    
    def create_thumbnail(self, image_data: bytes) -> bytes:
        """Create thumbnail from image"""
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not available - returning original image data as thumbnail")
            return image_data
        
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert RGBA to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Create thumbnail
            image.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=80)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return image_data
    
    def save_file(self, file: FileStorage, complaint_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Save uploaded file and return file information"""
        try:
            # Validate file
            is_valid, message = self.validate_file(file)
            if not is_valid:
                return False, {'error': message}
            
            file_type = self.get_file_type(file.filename)
            unique_filename = self.generate_unique_filename(file.filename)
            
            # Create complaint-specific directory
            complaint_dir = os.path.join(self.upload_folder, file_type + 's', complaint_id)
            os.makedirs(complaint_dir, exist_ok=True)
            
            file_path = os.path.join(complaint_dir, unique_filename)
            
            # Read file data
            file.seek(0)
            file_data = file.read()
            file_size = len(file_data)
            
            # Calculate file hash for integrity
            file_hash = hashlib.md5(file_data).hexdigest()
            
            result = {
                'original_filename': file.filename,
                'saved_filename': unique_filename,
                'file_path': file_path,
                'file_type': file_type,
                'file_size': file_size,
                'file_hash': file_hash,
                'upload_timestamp': datetime.now(),
                'complaint_id': complaint_id
            }
            
            if file_type == 'image':
                # Compress image
                compressed_data, compression_metadata = self.compress_image(file_data, file.filename)
                
                # Save compressed image
                with open(file_path, 'wb') as f:
                    f.write(compressed_data)
                
                # Create and save thumbnail
                thumbnail_data = self.create_thumbnail(compressed_data)
                thumbnail_filename = f"thumb_{unique_filename}"
                thumbnail_path = os.path.join(self.upload_folder, 'thumbnails', complaint_id)
                os.makedirs(thumbnail_path, exist_ok=True)
                thumbnail_path = os.path.join(thumbnail_path, thumbnail_filename)
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(thumbnail_data)
                
                result.update({
                    'thumbnail_path': thumbnail_path,
                    'thumbnail_filename': thumbnail_filename,
                    'compression_metadata': compression_metadata
                })
            
            else:  # video
                # Save video as-is (no compression for now)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            
            logger.info(f"Successfully saved {file_type} file: {unique_filename}")
            return True, result
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False, {'error': str(e)}
    
    def get_file_url(self, file_path: str) -> str:
        """Generate URL for accessing file (relative to upload folder)"""
        # Remove upload folder prefix and normalize path separators
        relative_path = os.path.relpath(file_path, self.upload_folder)
        return f"/uploads/{relative_path.replace(os.sep, '/')}"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def cleanup_complaint_media(self, complaint_id: str) -> bool:
        """Delete all media files associated with a complaint"""
        try:
            deleted_files = 0
            
            # Delete from images, videos, and thumbnails directories
            for media_type in ['images', 'videos', 'thumbnails']:
                complaint_dir = os.path.join(self.upload_folder, media_type, complaint_id)
                if os.path.exists(complaint_dir):
                    for filename in os.listdir(complaint_dir):
                        file_path = os.path.join(complaint_dir, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            deleted_files += 1
                    os.rmdir(complaint_dir)
            
            logger.info(f"Cleaned up {deleted_files} files for complaint {complaint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up complaint media: {e}")
            return False
    
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
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a media file"""
        try:
            if not os.path.exists(file_path):
                return {'error': 'File not found'}
            
            stat = os.stat(file_path)
            file_type = self.get_file_type(file_path)
            
            info = {
                'file_path': file_path,
                'file_size': stat.st_size,
                'file_type': file_type,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'mime_type': mimetypes.guess_type(file_path)[0]
            }
            
            # Keep backward compatibility
            filename = os.path.basename(file_path)
            _, ext = os.path.splitext(filename.lower())
            media_type = "image" if ext in {'.jpg', '.jpeg', '.png', '.gif'} else "video"
            
            info.update({
                "filename": filename,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "media_type": media_type,
                "extension": ext
            })
            
            if file_type == 'image' and PIL_AVAILABLE:
                try:
                    with Image.open(file_path) as img:
                        info.update({
                            'dimensions': img.size,
                            'format': img.format,
                            'mode': img.mode
                        })
                except Exception as e:
                    info['image_error'] = str(e)
            elif file_type == 'image' and not PIL_AVAILABLE:
                info['image_note'] = 'PIL/Pillow not available for detailed image info'
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
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

# Global service instance
media_service = MediaService()