import os
from werkzeug.utils import secure_filename
from flask import current_app
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
        
        # Return relative path for database storage
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
        if file_path.startswith('uploads/'):
            full_path = os.path.join('static', file_path)
        elif file_path.startswith('/static/'):
            full_path = file_path[1:]  # Remove leading /
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

def get_image_url(image_path):
    """
    Get URL for image (local storage version)
    """
    if not image_path or image_path == 'images/no-image.png':
        return '/static/images/no-image.png'
    
    if image_path.startswith('http'):
        return image_path
    
    if image_path.startswith('/'):
        return image_path
    
    return f"/static/{image_path}"

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