# Photo/Video Support Setup Guide

This guide explains how to set up and configure the Photo/Video Support feature in Muni-Info.

## 🚀 Quick Setup

### 1. Install Dependencies

The photo/video feature requires the Pillow library for image processing:

```bash
pip install Pillow
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

Run the test script to verify everything is working:

```bash
python test_photo_video_support.py
```

### 3. Check Media Service Status

You can check if image processing is available:

```python
from src.services.media_service import media_service
print(f"Image processing available: {media_service.is_image_processing_available()}")
```

## 📁 Directory Structure

The system will automatically create these directories:

```
uploads/
├── images/           # Compressed images organized by complaint ID
├── videos/           # Videos organized by complaint ID  
├── thumbnails/       # Auto-generated image thumbnails
└── temp/            # Temporary files during processing
```

## ⚙️ Configuration

### File Size Limits

Default limits (can be modified in `src/services/media_service.py`):
- **Images**: 10MB maximum
- **Videos**: 100MB maximum

### Supported Formats

**Images**:
- JPG/JPEG
- PNG
- GIF
- BMP
- WebP

**Videos**:
- MP4
- AVI
- MOV
- WMV
- FLV
- WebM
- 3GP

### Image Processing Settings

```python
IMAGE_QUALITY = 85           # JPEG compression quality (1-100)
MAX_IMAGE_DIMENSION = 1920   # Max width/height in pixels
THUMBNAIL_SIZE = (300, 300)  # Thumbnail dimensions
```

## 🌐 Web Portal Usage

### For Users

1. **Submit Complaint**: Go to `/portal/complaints/submit`
2. **Upload Media**: 
   - Click the upload area or drag & drop files
   - Select up to 5 files (images + videos)
   - Files are validated and previewed before submission
3. **View Media**: Check complaint status to see attached media

### File Upload Features

- **Drag & Drop**: Drag files directly onto upload area
- **Multiple Files**: Upload multiple images and videos together
- **Preview**: See file names, sizes, and types before submission
- **Validation**: Client-side and server-side file validation
- **Progress**: Visual feedback during upload process

## 📱 WhatsApp Integration

### Media Message Handling

The system automatically:
1. **Receives** images and videos sent via WhatsApp
2. **Downloads** media from Twilio servers
3. **Processes** files (compression, thumbnails)
4. **Associates** media with complaints
5. **Provides** feedback to users

### WhatsApp Media Flow

```
User sends photo → Twilio webhook → Media processing → Complaint creation
```

## 🔧 Advanced Configuration

### Twilio Settings

For WhatsApp media download, configure in your environment:

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
```

### Storage Options

By default, files are stored locally. For production, consider:

1. **Cloud Storage**: AWS S3, Google Cloud Storage
2. **CDN Integration**: For faster media delivery
3. **Backup Strategy**: Regular media file backups

### Performance Optimization

For high-volume deployments:

1. **Async Processing**: Use Celery for background image processing
2. **Caching**: Cache thumbnails and compressed images
3. **Database**: Use dedicated media metadata database

## 🐛 Troubleshooting

### PIL/Pillow Not Found

```bash
# Install Pillow
pip install Pillow

# Verify installation
python -c "from PIL import Image; print('PIL available')"
```

### Upload Directory Permissions

Ensure the application has write permissions:

```bash
# Linux/Mac
chmod 755 uploads/
chmod -R 644 uploads/*

# Windows - ensure write permissions for the application user
```

### File Upload Failures

Check these common issues:

1. **File size exceeds limits**
2. **Unsupported file format**
3. **Disk space insufficient**
4. **Network timeout during upload**

### Memory Issues with Large Images

For very large images, consider:

```python
# Increase PIL memory limits
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Remove limit (use with caution)
```

## 📊 Monitoring

### Log Files

Media processing logs are written to the application log:

```python
import logging
logging.getLogger('src.services.media_service').setLevel(logging.INFO)
```

### Storage Usage

Monitor disk space usage in the uploads directory:

```bash
# Linux/Mac
du -sh uploads/

# Windows
dir uploads /s
```

### Database Size

Media metadata is stored in the complaints collection. Monitor:
- Number of media files per complaint
- Total media metadata size
- Database growth over time

## 🔒 Security Considerations

### File Validation

The system includes multiple security layers:

1. **Extension checking**: Only allowed file types
2. **Content validation**: Verify file headers match extensions  
3. **Size limits**: Prevent oversized uploads
4. **Filename sanitization**: Clean filenames for security

### Access Control

- Media files are served through the application
- Direct file access can be restricted
- Authentication can be added to media endpoints

### Virus Scanning

For production environments, consider:
- Integrating with antivirus scanning services
- Scanning uploaded files before processing
- Quarantine suspicious files

## 🎯 Performance Tips

1. **Image Optimization**: Enable compression for faster loading
2. **Thumbnail Usage**: Use thumbnails for listing views
3. **Lazy Loading**: Load images on demand in the UI
4. **CDN Integration**: Serve media files from CDN
5. **Database Indexing**: Index media metadata fields

## 📈 Usage Statistics

Track photo/video feature usage:

```python
# Example metrics to collect
total_uploads = complaint_service.count_complaints_with_media()
avg_media_per_complaint = calculate_avg_media_files()
storage_used = calculate_total_storage_usage()
```

## 🆘 Support

If you encounter issues:

1. **Check logs** for error messages
2. **Verify dependencies** are installed correctly
3. **Test with sample files** to isolate problems
4. **Review file permissions** and storage access

For additional help, refer to the main project documentation or create an issue in the project repository.