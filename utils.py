import os
from werkzeug.utils import secure_filename
from flask import current_app
import logging

# Set up logger
logger = logging.getLogger(__name__)

def get_image_url(image_path):
    """
    Convert database image path to proper URL for templates
    Handles both single images and comma-separated multiple images
    """
    if not image_path:
        return '/static/images/no-image.png'
    
    # Handle multiple images - return first one
    if ',' in image_path:
        image_path = image_path.split(',')[0].strip()
    
    image_path = image_path.strip()
    
    # If already a full URL (http/https), return as is
    if image_path.startswith('http://') or image_path.startswith('https://'):
        return image_path

    # Normalize path to a filesystem-relative path under static/
    normalized = image_path.strip()

    # If it already starts with /static/, remove the leading slash for FS check
    if normalized.startswith('/static/'):
        fs_path = normalized[1:]
    elif normalized.startswith('static/'):
        fs_path = normalized
    else:
        fs_path = os.path.join('static', normalized)

    # If the file exists on disk, return a URL path; else return no-image
    if os.path.exists(fs_path):
        # Ensure URL starts with /static/
        if fs_path.startswith('static/'):
            return '/' + fs_path
        else:
            return '/' + fs_path.replace('\\', '/')
    else:
        logger.warning(f"Image not found on disk: {fs_path}; falling back to no-image.png")
        return '/static/images/no-image.png'


def upload_to_s3(file, filename, folder='uploads'):
    """
    Local storage version - saves file to local filesystem
    (Function name kept as upload_to_s3 for compatibility)
    """
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Return relative path for database storage (without 'static/')
        return f"uploads/{filename}"
        
    except Exception as e:
        logger.error(f"Error saving file locally: {e}")
        return None


def delete_from_s3(file_path):
    """
    Local storage version - deletes file from local filesystem
    (Function name kept as delete_from_s3 for compatibility)
    """
    try:
        if not file_path:
            return False
            
        # Convert database path to filesystem path
        if file_path.startswith('uploads/'):
            full_path = os.path.join('static', file_path)
        elif file_path.startswith('/static/'):
            full_path = file_path[1:]  # Remove leading /
        elif file_path.startswith('static/'):
            full_path = file_path
        else:
            full_path = file_path
        
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted local file: {full_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {full_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting local file: {e}")
        return False


def validate_s3_config():
    """
    Local storage version - always returns success
    """
    return {
        'status': 'success',
        'message': 'Using local storage configuration'
    }


def migrate_local_to_s3(local_path, s3_folder='uploads'):
    """
    Not needed for local storage, but kept for compatibility
    """
    return None