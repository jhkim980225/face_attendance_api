"""
Path utilities for managing storage locations
"""
import os
from datetime import datetime
from typing import Optional
from app.core.config import settings


def ensure_dir(directory: str) -> None:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory: Directory path
    """
    os.makedirs(directory, exist_ok=True)


def get_images_dir() -> str:
    """Get images storage directory"""
    path = settings.IMAGE_DIR
    ensure_dir(path)
    return path


def get_encodings_dir() -> str:
    """Get encodings storage directory"""
    path = settings.ENCODING_DIR
    ensure_dir(path)
    return path


def generate_timestamp_filename(prefix: str, extension: str) -> str:
    """
    Generate filename with timestamp
    
    Args:
        prefix: Filename prefix
        extension: File extension (with or without dot)
        
    Returns:
        Filename in format: prefix_YYYYMMDD_HHMMSS_microseconds.ext
    """
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{timestamp}{extension}"


def get_image_path(employee_id: str, suffix: str = "") -> str:
    """
    Get path for saving employee image
    
    Args:
        employee_id: Employee ID
        suffix: Optional suffix to add to filename
        
    Returns:
        Full path to image file
    """
    images_dir = get_images_dir()
    suffix_str = f"_{suffix}" if suffix else ""
    filename = generate_timestamp_filename(f"{employee_id}{suffix_str}", "jpg")
    return os.path.join(images_dir, filename)


def get_encoding_path(employee_id: str, index: Optional[int] = None) -> str:
    """
    Get path for saving employee face encoding
    
    Args:
        employee_id: Employee ID
        index: Optional index for multiple encodings
        
    Returns:
        Full path to .npy file
    """
    encodings_dir = get_encodings_dir()
    index_str = f"_{index}" if index is not None else ""
    filename = generate_timestamp_filename(f"{employee_id}{index_str}", "npy")
    return os.path.join(encodings_dir, filename)


def get_thumbnail_path(employee_id: str) -> str:
    """
    Get path for saving employee thumbnail
    
    Args:
        employee_id: Employee ID
        
    Returns:
        Full path to thumbnail file
    """
    return get_image_path(employee_id, suffix="thumb")


def get_relative_path(full_path: str) -> str:
    """
    Convert absolute path to relative path (for database storage)
    
    Args:
        full_path: Absolute file path
        
    Returns:
        Relative path from project root
    """
    # Get current working directory
    cwd = os.getcwd()
    try:
        return os.path.relpath(full_path, cwd)
    except ValueError:
        # If paths are on different drives (Windows), return full path
        return full_path
