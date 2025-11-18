"""
Image I/O utilities
Handles image validation, resizing, encoding, and format conversion
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from app.core.logging import app_logger

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

# Image size constraints
MAX_IMAGE_SIZE = (1280, 720)  # 720p max
MIN_IMAGE_SIZE = (160, 120)    # Minimum for face detection
JPEG_QUALITY = 75               # JPEG compression quality


def validate_image_extension(filename: str) -> bool:
    """

    """
    import os
    ext = os.path.splitext(filename.lower())[1]
    return ext in SUPPORTED_FORMATS


def decode_image(file_bytes: bytes) -> Optional[np.ndarray]:
    """
    
    """
    try:
        # byte -> numpy array
        nparr = np.frombuffer(file_bytes, np.uint8)

        # numpy -> bgr 복원
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            app_logger.error("Failed to decode image")
            return None
            
        return img
    except Exception as e:
        app_logger.error(f"Error decoding image: {e}")
        return None


def resize_image(img: np.ndarray, max_size: Tuple[int, int] = MAX_IMAGE_SIZE) -> np.ndarray:
    """

    """
    h, w = img.shape[:2]
    max_w, max_h = max_size
    
    # Calculate scaling factor
    scale = min(max_w / w, max_h / h, 1.0)
    
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        app_logger.debug(f"Resized image from {w}x{h} to {new_w}x{new_h}")
    
    return img


def validate_image_size(img: np.ndarray) -> bool:
    """

    """
    h, w = img.shape[:2]
    min_w, min_h = MIN_IMAGE_SIZE
    
    if w < min_w or h < min_h:
        app_logger.warning(f"Image too small: {w}x{h} (min: {min_w}x{min_h})")
        return False
    
    return True


def encode_jpeg(img: np.ndarray, quality: int = JPEG_QUALITY) -> Optional[bytes]:
    """

    """
    try:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, buffer = cv2.imencode('.jpg', img, encode_param)
        
        if not success:
            app_logger.error("Failed to encode image to JPEG")
            return None
        
        return buffer.tobytes()
    except Exception as e:
        app_logger.error(f"Error encoding JPEG: {e}")
        return None


def save_image(img: np.ndarray, filepath: str, quality: int = JPEG_QUALITY) -> bool:
    """

    """
    try:
        if filepath.lower().endswith(('.jpg', '.jpeg')):
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success = cv2.imwrite(filepath, img, encode_param)
        else:
            success = cv2.imwrite(filepath, img)
        
        if success:
            app_logger.debug(f"Saved image to {filepath}")
        else:
            app_logger.error(f"Failed to save image to {filepath}")
        
        return success
    except Exception as e:
        app_logger.error(f"Error saving image: {e}")
        return False


def create_thumbnail(img: np.ndarray, max_size: Tuple[int, int] = (300, 300)) -> np.ndarray:
    """

    """
    return resize_image(img, max_size)
