"""
Face recognition service
Handles face detection, embedding generation, and comparison
"""
import cv2
import numpy as np
from typing import Optional, Tuple
from app.core.config import settings
from app.core.logging import app_logger
from app.utils.image_io import save_image, create_thumbnail
from app.utils.paths import get_encoding_path, get_thumbnail_path, get_relative_path

"""
얼굴 인식에 필요한 모든 핵심 기능
얼굴 이미지 디코딩
얼굴 감지 (DeepFace → SSD → fallback Haar)
임베딩 생성 (DeepFace Facenet → fallback HOG)
L2 거리 기반 사용자 매칭
임베딩 저장/로딩
썸네일 저장
"""

try:
    # 서버 시작 시 Facenet 모델 미리 로드 (첫 인식 속도 개선)
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    app_logger.info("DeepFace library loaded successfully")        
    try:
        app_logger.info("Pre-loading Facenet model...")
        DeepFace.build_model("Facenet")
        app_logger.info("Facenet model pre-loaded successfully")
    except Exception as e:
        app_logger.warning(f"Failed to pre-load Facenet model: {e}")
        
except ImportError:
    DEEPFACE_AVAILABLE = False
    app_logger.warning("DeepFace library not available, using fallback embedding method")


def decode_image(file_bytes: bytes) -> Optional[np.ndarray]:
    """
    byte -> OpenCV BGR 이미지 전환
    """
    from app.utils.image_io import decode_image as decode_img
    return decode_img(file_bytes)


def detect_single_face(bgr_image: np.ndarray) -> Optional[Tuple[Tuple[int, int, int, int], np.ndarray]]:
    """
    DeepFace 내장 얼굴 감지 사용 (ssd 백엔드 - 속도와 정확도 균형)
    """
    try:
        if DEEPFACE_AVAILABLE:
            try:
                # 이미지 품질 사전 체크 (검은 화면 필터링)
                gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
                mean_brightness = np.mean(gray)
                std_brightness = np.std(gray)
                
                app_logger.debug(f"Image quality: mean_brightness={mean_brightness:.1f}, std={std_brightness:.1f}")
                
                # 너무 어둡거나 변화가 없는 이미지는 거부 (임계값 완화)
                if mean_brightness < 40 or std_brightness < 20:
                    app_logger.warning(f"Image rejected: too dark or uniform (mean={mean_brightness:.1f}, std={std_brightness:.1f})")
                    return None
                
                # DeepFace.extract_faces: 얼굴 감지 + 크롭
                rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
                
                faces = DeepFace.extract_faces(
                    img_path=rgb_image,
                    detector_backend='ssd',  # 속도와 정확도 균형 (Single Shot Detector)
                    enforce_detection=False,
                    align=True
                )
                
                if not faces or len(faces) == 0:
                    app_logger.debug("No face detected (DeepFace SSD)")
                    return None
                
                # 여러 얼굴 감지 시 가장 큰 것 선택
                if len(faces) > 1:
                    app_logger.info(f"Multiple faces detected: {len(faces)}, selecting largest")
                    faces = sorted(faces, key=lambda f: f['facial_area']['w'] * f['facial_area']['h'], reverse=True)
                
                face = faces[0]
                facial_area = face['facial_area']
                
                # 좌표 추출
                x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
                
                # bbox 형식 변환
                top, left = max(0, y), max(0, x)
                bottom = min(bgr_image.shape[0], y + h)
                right = min(bgr_image.shape[1], x + w)
                bbox = (top, right, bottom, left)
                
                # 얼굴 영역 크롭
                face_image = bgr_image[top:bottom, left:right]
                
                # 얼굴 영역 밝기 체크
                face_gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
                face_brightness = np.mean(face_gray)
                face_std = np.std(face_gray)
                
                app_logger.debug(f"Face quality: brightness={face_brightness:.1f}, std={face_std:.1f}")
                
                # 얼굴 영역이 너무 어둡거나 변화가 없으면 거부 (임계값 완화)
                if face_brightness < 30 or face_std < 15:
                    app_logger.warning(f"Face rejected: too dark or uniform (brightness={face_brightness:.1f}, std={face_std:.1f})")
                    return None
                
                app_logger.debug(f"Face detected (DeepFace SSD) at bbox: {bbox}")
                return (bbox, face_image)
                
            except Exception as e:
                app_logger.warning(f"DeepFace SSD detection failed: {e}, using Haar Cascade")
        
        # Fallback: OpenCV Haar Cascade
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            app_logger.warning("No face detected (Haar Cascade)")
            return None
        
        if len(faces) > 1:
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[:1]
        
        x, y, w, h = faces[0]
        bbox = (y, x + w, y + h, x)
        face_image = bgr_image[y:y+h, x:x+w]
        
        app_logger.debug(f"Face detected (Haar) at bbox: {bbox}")
        return (bbox, face_image)
            
    except Exception as e:
        app_logger.error(f"Error detecting face: {e}", exc_info=True)
        return None


def embed(face_bgr: np.ndarray) -> Optional[np.ndarray]:
    """

    """
    try:
        if DEEPFACE_AVAILABLE:
            # Convert BGR to RGB for DeepFace
            face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
            
            # DeepFace.represent: 얼굴 임베딩 생성
            # model_name 옵션: VGG-Face, Facenet, Facenet512, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace
            # Facenet: 128D, 정확도 높음, 속도 빠름 (권장)
            embeddings = DeepFace.represent(
                img_path=face_rgb,
                model_name="Facenet",  # 128차원, LFW 99.65% 정확도
                enforce_detection=False,  # 이미 얼굴 크롭된 이미지 사용
                detector_backend="skip"  # 감지 스킵 (이미 감지됨)
            )
            
            if not embeddings or len(embeddings) == 0:
                app_logger.warning("No face embedding generated by DeepFace")
                return None
            
            # Return first embedding
            embedding = np.array(embeddings[0]["embedding"])
            app_logger.debug(f"Generated DeepFace embedding (model: Facenet, shape: {embedding.shape})")
            return embedding
        
        else:
            # Fallback: 개선된 임베딩 방법
            app_logger.debug("Using improved fallback embedding method")
            
            # 1. Resize to fixed size
            face_resized = cv2.resize(face_bgr, (128, 128))
            
            # 2. 히스토그램 평활화로 조명 정규화
            gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            # 3. HOG 특징 추출 (더 나은 얼굴 특징)
            win_size = (128, 128)
            block_size = (16, 16)
            block_stride = (8, 8)
            cell_size = (8, 8)
            nbins = 9
            
            hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
            hog_features = hog.compute(gray)
            
            if hog_features is None:
                # HOG 실패 시 원래 방법 사용
                flat = gray.flatten().astype(np.float32)
            else:
                flat = hog_features.flatten().astype(np.float32)
            
            # 4. L2 normalize
            norm = np.linalg.norm(flat)
            if norm > 0:
                embedding = flat / norm
            else:
                embedding = flat
            
            # 5. 고정 차원으로 조정 (512D)
            target_dim = 512
            if len(embedding) < target_dim:
                embedding = np.pad(embedding, (0, target_dim - len(embedding)), mode='constant')
            else:
                embedding = embedding[:target_dim]
            
            app_logger.debug(f"Generated improved fallback embedding (shape: {embedding.shape})")
            return embedding
            
    except Exception as e:
        app_logger.error(f"Error generating embedding: {e}", exc_info=True)
        return None


def l2_distance(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """

    """
    try:
        distance = np.linalg.norm(embedding1 - embedding2)
        return float(distance)
    except Exception as e:
        app_logger.error(f"Error calculating distance: {e}")
        return float('inf')


def save_thumbnail(bgr_image: np.ndarray, employee_id: str) -> Optional[str]:
    """
    Save thumbnail image
    
    Args:
        bgr_image: Input image in BGR format
        employee_id: Employee ID
        
    Returns:
        Relative path to saved thumbnail, or None if failed
    """
    try:
        thumbnail = create_thumbnail(bgr_image, max_size=(300, 300))
        filepath = get_thumbnail_path(employee_id)
        
        if save_image(thumbnail, filepath):
            relative_path = get_relative_path(filepath)
            app_logger.debug(f"Saved thumbnail: {relative_path}")
            return relative_path
        
        return None
    except Exception as e:
        app_logger.error(f"Error saving thumbnail: {e}")
        return None


def save_embedding(employee_id: str, embedding: np.ndarray) -> Optional[str]:
    """

    """
    try:
        filepath = get_encoding_path(employee_id)
        np.save(filepath, embedding)
        
        relative_path = get_relative_path(filepath)
        app_logger.debug(f"Saved embedding: {relative_path}")
        return relative_path
    except Exception as e:
        app_logger.error(f"Error saving embedding: {e}")
        return None


def load_embedding(filepath: str) -> Optional[np.ndarray]:
    """

    """
    try:
        embedding = np.load(filepath)
        return embedding
    except Exception as e:
        app_logger.error(f"Error loading embedding from {filepath}: {e}")
        return None
