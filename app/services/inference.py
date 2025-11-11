"""
Inference service
High-level logic for identify and enroll operations
"""
from typing import Optional, Dict, Any, List
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.core.logging import app_logger
from app.services import face_service
from app.services.camera_worker import camera_worker
from app.db.models import User
from app.utils.image_io import validate_image_size, resize_image


class IdentifyResult:
    """Result of face identification"""
    def __init__(
        self,
        success: bool,
        employee_id: Optional[str] = None,
        name: Optional[str] = None,
        distance: Optional[float] = None,
        message: str = "",
        reason: Optional[str] = None
    ):
        self.success = success
        self.employee_id = employee_id
        self.name = name
        self.distance = distance
        self.message = message
        self.reason = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "success": self.success,
            "message": self.message
        }
        
        if self.success:
            result["employee_id"] = self.employee_id
            result["name"] = self.name
            result["user"] = self.name  # Alias for compatibility
            result["distance"] = self.distance
            result["decided_threshold"] = settings.TOLERANCE
        else:
            if self.reason:
                result["reason"] = self.reason
            if self.distance is not None:
                result["min_distance"] = self.distance
        
        return result


class EnrollResult:
    """Result of face enrollment"""
    def __init__(
        self,
        success: bool,
        employee_id: Optional[str] = None,
        message: str = "",
        reason: Optional[str] = None
    ):
        self.success = success
        self.employee_id = employee_id
        self.message = message
        self.reason = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        result = {
            "success": self.success,
            "message": self.message
        }
        
        if self.success:
            result["employee_id"] = self.employee_id
        else:
            if self.reason:
                result["reason"] = self.reason
        
        return result


def identify_from_camera(db: Session) -> IdentifyResult:
    """
    Identify face from camera (MODE_A)
    
    Args:
        db: Database session
        
    Returns:
        IdentifyResult
    """
    try:
        # Check if camera worker is running
        if not camera_worker.is_alive():
            return IdentifyResult(
                success=False,
                message="카메라를 사용할 수 없습니다",
                reason="camera_unavailable"
            )
        
        # Get latest frame
        frame = camera_worker.get_latest_frame()
        
        if frame is None:
            return IdentifyResult(
                success=False,
                message="카메라 프레임을 가져올 수 없습니다",
                reason="camera_unavailable"
            )
        
        # Process frame
        return identify_from_image(db, frame)
        
    except Exception as e:
        app_logger.error(f"Error in identify_from_camera: {e}")
        return IdentifyResult(
            success=False,
            message="내부 오류가 발생했습니다",
            reason="internal_error"
        )


def identify_from_upload(db: Session, file_bytes: bytes) -> IdentifyResult:
    """
    
    """
    try:
        # Decode image
        image = face_service.decode_image(file_bytes)
        
        if image is None:
            return IdentifyResult(
                success=False,
                message="이미지를 디코딩할 수 없습니다",
                reason="bad_quality"
            )
        
        # Validate and resize
        if not validate_image_size(image):
            return IdentifyResult(
                success=False,
                message="이미지가 너무 작습니다",
                reason="bad_quality"
            )
        
        image = resize_image(image)
        
        # Process image
        return identify_from_image(db, image)
        
    except Exception as e:
        app_logger.error(f"Error in identify_from_upload: {e}")
        return IdentifyResult(
            success=False,
            message="내부 오류가 발생했습니다",
            reason="internal_error"
        )


def identify_from_image(db: Session, image: np.ndarray) -> IdentifyResult:
    """
    Identify face from image array (common logic)
    
    Args:
        db: Database session
        image: Image in BGR format
        
    Returns:
        IdentifyResult
    """
    try:
        # 프레임 크기
        h, w = image.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # 타원 영역 정의 (중앙) - 크기 축소
        ellipse_width = int(w * 0.35)  # 화면 너비의 35% (편의성 향상)
        ellipse_height = int(h * 0.50)  # 화면 높이의 50% (편의성 향상)
        
        # Detect face
        face_result = face_service.detect_single_face(image)
        
        if face_result is None:
            return IdentifyResult(
                success=False,
                message="얼굴을 감지할 수 없습니다",
                reason="no_face"
            )
        
        bbox, face_image = face_result
        top, right, bottom, left = bbox
        
        # 얼굴 중심점 계산
        face_center_x = (left + right) // 2
        face_center_y = (top + bottom) // 2
        
        # 타원 내부 체크 (타원 방정식 사용)
        normalized_x = (face_center_x - center_x) / (ellipse_width / 2)
        normalized_y = (face_center_y - center_y) / (ellipse_height / 2)
        distance_from_center = normalized_x ** 2 + normalized_y ** 2
        is_inside = distance_from_center <= 1
        
        app_logger.debug(f"Face center: ({face_center_x}, {face_center_y}), " 
                        f"Screen center: ({center_x}, {center_y}), "
                        f"Ellipse: {ellipse_width}x{ellipse_height}, "
                        f"Distance from center: {distance_from_center:.2f}, "
                        f"Inside: {is_inside}")
        
        if not is_inside:
            app_logger.warning(f"Face detected but outside guide area: center=({face_center_x}, {face_center_y}), distance={distance_from_center:.2f}")
            return IdentifyResult(
                success=False,
                message="가이드 영역 안에서 인증해주세요",
                reason="out_of_area"
            )
        
        # Generate embedding
        embedding = face_service.embed(face_image)
        
        if embedding is None:
            return IdentifyResult(
                success=False,
                message="얼굴 임베딩 생성 실패",
                reason="bad_quality"
            )
        
        # Compare with all registered embeddings
        best_match = find_best_match(db, embedding)
        
        if best_match is None:
            return IdentifyResult(
                success=False,
                message="등록된 얼굴이 없습니다",
                reason="unknown"
            )
        
        employee_id, name, min_distance = best_match
        
        # Best match 무조건 통과 (TOLERANCE 체크 제거)
        app_logger.info(f"Best match accepted: {employee_id} ({name}), distance: {min_distance:.4f}")
        
        # Success
        return IdentifyResult(
            success=True,
            employee_id=employee_id,
            name=name,
            distance=min_distance,
            message="인증 성공"
        )
        
    except Exception as e:
        app_logger.error(f"Error in identify_from_image: {e}")
        return IdentifyResult(
            success=False,
            message="내부 오류가 발생했습니다",
            reason="internal_error"
        )


def find_best_match(db: Session, embedding: np.ndarray) -> Optional[tuple]:
    """
    Find best matching user for given embedding
    
    Args:
        db: Database session
        embedding: Face embedding to match
        
    Returns:
        Tuple of (employee_id, name, distance) if match found, None otherwise
    """
    try:
        # profile_image가 있는 모든 사용자 조회 (임베딩 경로로 사용)
        users_with_embeddings = db.query(User).filter(User.profile_image.isnot(None)).all()
        
        app_logger.info(f"Total users with embeddings in DB: {len(users_with_embeddings)}")
        
        if not users_with_embeddings:
            app_logger.warning("No users with embeddings found in database")
            return None
        
        best_employee_id = None
        best_name = None
        best_distance = float('inf')
        
        # 각 등록된 임베딩과 비교
        for user in users_with_embeddings:
            app_logger.debug(f"Checking user: {user.employee_id}, path: {user.profile_image}")
            
            # 임베딩 로드
            stored_embedding = face_service.load_embedding(user.profile_image)
            
            if stored_embedding is None:
                app_logger.warning(f"Failed to load embedding from {user.profile_image}")
                continue
            
            # 거리 계산
            distance = face_service.l2_distance(embedding, stored_embedding)
            app_logger.debug(f"Distance for {user.employee_id}: {distance:.4f}")
            
            # 최고 매칭 업데이트
            if distance < best_distance:
                best_distance = distance
                best_employee_id = user.employee_id
                best_name = user.name
        
        if best_employee_id is None:
            app_logger.warning("No valid embeddings could be loaded")
            return None
        
        app_logger.info(f"Best match: {best_employee_id} ({best_name}), distance: {best_distance:.4f}")
        return (best_employee_id, best_name, best_distance)
        
    except Exception as e:
        app_logger.error(f"Error finding best match: {e}", exc_info=True)
        return None


def generate_employee_id(db: Session) -> str:
    """
    Generate new employee_id in format EMP001, EMP002, ...
    """
    # Get last employee_id
    last_user = db.query(User).filter(
        User.employee_id.like('EMP%')
    ).order_by(User.employee_id.desc()).first()
    
    if last_user is None:
        return "EMP001"
    
    # Extract number from last employee_id
    try:
        last_num = int(last_user.employee_id[3:])
        new_num = last_num + 1
        return f"EMP{new_num:03d}"
    except:
        return "EMP001"


def enroll_user_simple(
    db: Session,
    name: str
) -> EnrollResult:
    """
    Enroll new user with auto-generated employee_id (no image upload)
    
    Args:
        db: Database session
        name: User name (required)
        
    Returns:
        EnrollResult
    """
    try:
        # Auto-generate employee_id
        employee_id = generate_employee_id(db)
        app_logger.info(f"Auto-generated employee_id: {employee_id}")
        
        # Create new user
        user = User(employee_id=employee_id, name=name)
        db.add(user)
        db.commit()
        
        app_logger.info(f"Successfully enrolled user: {employee_id} ({name})")
        
        return EnrollResult(
            success=True,
            employee_id=employee_id,
            message="등록 완료"
        )
        
    except Exception as e:
        db.rollback()
        app_logger.error(f"Error in enroll_user_simple: {e}")
        return EnrollResult(
            success=False,
            message="등록 중 오류가 발생했습니다",
            reason="internal_error"
        )


def enroll_user_with_image(
    db: Session,
    name: str,
    file_bytes: bytes
) -> EnrollResult:
    """
    Enroll new user with profile image and auto-generated employee_id
    
    Args:
        db: Database session
        name: User name (required)
        file_bytes: Profile image file bytes
        
    Returns:
        EnrollResult
    """
    try:
        # Auto-generate employee_id
        employee_id = generate_employee_id(db)
        app_logger.info(f"Auto-generated employee_id: {employee_id}")
        
        # Decode and validate image
        app_logger.info(f"Image data length: {len(file_bytes)} bytes")
        image = face_service.decode_image(file_bytes)
        
        if image is None:
            app_logger.error(f"Failed to decode image (data length: {len(file_bytes)})")
            return EnrollResult(
                success=False,
                message="이미지를 디코딩할 수 없습니다",
                reason="bad_quality"
            )
        
        # Validate and resize
        if not validate_image_size(image):
            return EnrollResult(
                success=False,
                message="이미지가 너무 작습니다",
                reason="bad_quality"
            )
        
        image = resize_image(image)
        
        app_logger.info(f"Image successfully decoded and resized: {image.shape}")
        
        # Save profile image
        profile_image_path = face_service.save_thumbnail(image, employee_id)
        
        if profile_image_path is None:
            return EnrollResult(
                success=False,
                message="프로필 이미지 저장 실패",
                reason="internal_error"
            )
        
        # Detect face and generate embedding
        app_logger.info(f"Attempting to detect face for {employee_id}")
        face_result = face_service.detect_single_face(image)
        
        embedding_saved = False
        embedding_path = None
        
        if face_result is not None:
            # Face detected - generate and save embedding
            bbox, face_image = face_result
            app_logger.info(f"Face detected for {employee_id} at bbox: {bbox}")
            
            embedding = face_service.embed(face_image)
            
            if embedding is not None:
                app_logger.info(f"Embedding generated for {employee_id}, shape: {embedding.shape}")
                
                # Save embedding
                embedding_path = face_service.save_embedding(employee_id, embedding)
                
                if embedding_path:
                    embedding_saved = True
                    app_logger.info(f"Face embedding saved for {employee_id} at {embedding_path}")
                else:
                    app_logger.error(f"Failed to save embedding file for {employee_id}")
            else:
                app_logger.warning(f"Failed to generate embedding for {employee_id}")
        else:
            app_logger.warning(f"No face detected in image for {employee_id}")
        
        # Create user with profile image (임베딩 경로 저장)
        user = User(
            employee_id=employee_id,
            name=name,
            profile_image=embedding_path  # .npy 파일 경로 (없으면 None)
        )
        db.add(user)
        db.commit()
        
        app_logger.info(f"Successfully enrolled user with image: {employee_id} ({name}), embedding_saved: {embedding_saved}")
        
        # Return with warning if no face detected
        if not embedding_saved:
            return EnrollResult(
                success=True,
                employee_id=employee_id,
                message="등록 완료 (얼굴 인식 실패 - 사진만 저장됨)"
            )
        
        return EnrollResult(
            success=True,
            employee_id=employee_id,
            message="등록 완료"
        )
        
    except Exception as e:
        db.rollback()
        app_logger.error(f"Error in enroll_user_with_image: {e}")
        return EnrollResult(
            success=False,
            message="등록 중 오류가 발생했습니다",
            reason="internal_error"
        )


def enroll_user(
    db: Session,
    employee_id: str,
    file_bytes: bytes,
    name: Optional[str] = None
) -> EnrollResult:
    """
    Enroll new user or add embedding to existing user
    
    Args:
        db: Database session
        employee_id: Employee ID
        file_bytes: Image file bytes
        name: Optional user name (required for new users)
        
    Returns:
        EnrollResult
    """
    try:
        # Decode image
        image = face_service.decode_image(file_bytes)
        
        if image is None:
            return EnrollResult(
                success=False,
                message="이미지를 디코딩할 수 없습니다",
                reason="bad_quality"
            )
        
        # Validate and resize
        if not validate_image_size(image):
            return EnrollResult(
                success=False,
                message="이미지가 너무 작습니다",
                reason="bad_quality"
            )
        
        image = resize_image(image)
        
        # Detect face
        face_result = face_service.detect_single_face(image)
        
        if face_result is None:
            return EnrollResult(
                success=False,
                message="얼굴을 감지할 수 없습니다. 정면 사진을 사용해주세요",
                reason="no_face"
            )
        
        bbox, face_image = face_result
        
        # Generate embedding
        embedding = face_service.embed(face_image)
        
        if embedding is None:
            return EnrollResult(
                success=False,
                message="얼굴 임베딩 생성 실패",
                reason="bad_quality"
            )
        
        # Check if user exists
        user = db.query(User).filter(User.employee_id == employee_id).first()
        
        if user is None:
            # New user - name is required
            if not name:
                return EnrollResult(
                    success=False,
                    message="새 사용자 등록 시 이름이 필요합니다",
                    reason="missing_name"
                )
            
            # Create user
            user = User(employee_id=employee_id, name=name)
            db.add(user)
            db.flush()
            
            app_logger.info(f"Created new user: {employee_id} ({name})")
        
        # Save thumbnail (나중에 사용할 수도 있음)
        thumbnail_path = face_service.save_thumbnail(image, employee_id)
        
        # Save embedding
        embedding_path = face_service.save_embedding(employee_id, embedding)
        
        if embedding_path is None:
            db.rollback()
            return EnrollResult(
                success=False,
                message="임베딩 저장 실패",
                reason="internal_error"
            )
        
        # User의 profile_image에 embedding_path 저장 (.npy 파일)
        user.profile_image = embedding_path
        
        # Commit
        db.commit()
        
        app_logger.info(f"Enrolled embedding for {employee_id} at {embedding_path}")
        
        return EnrollResult(
            success=True,
            employee_id=employee_id,
            message="등록 완료"
        )
        
    except Exception as e:
        app_logger.error(f"Error enrolling user: {e}")
        db.rollback()
        return EnrollResult(
            success=False,
            message="내부 오류가 발생했습니다",
            reason="internal_error"
        )
