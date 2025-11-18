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
    """업로드 이미지로 인증"""
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
    """등록"""
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
    카메라에서 실시간으로 얼굴을 찍어서 인증하는 모드
    """
    try:
        # 카메라 캡처 스레드가 돌지 않을 때
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
    try:
        # ------------------------
        # 화면 크기, 가이드 계산
        # ------------------------
        h, w = image.shape[:2]
        center_x, center_y = w // 2, h // 2

        # GUIDE_W_RATIO = 170.0 / 640.0  # 프론트 기준 170px
        # GUIDE_H_RATIO = 220.0 / 480.0  # 프론트 기준 220px

        ellipse_width = int(w * (170.0 / 640.0))
        ellipse_height = int(h * (220.0 / 480.0))

        half_w = ellipse_width / 2.0
        half_h = ellipse_height / 2.0        

        # ------------------------
        # 얼굴 감지
        # ------------------------
        face_result = face_service.detect_single_face(image)

        if face_result is None:
            return IdentifyResult(
                success=False,
                message="얼굴을 감지할 수 없습니다",
                reason="no_face"
            )
        
        bbox, face_image = face_result
        # top, right, bottom, left = bbox

        # # 얼굴 중심
        # face_center_x = (left + right) // 2
        # face_center_y = (top + bottom) // 2
        
        # # ---------- 2) 가이드 사각형 계산 ----------
        # guide_left = center_x - half_w
        # guide_right = center_x + half_w
        # guide_top = center_y - half_h
        # guide_bottom = center_y + half_h

        # # ---------- 3) 얼굴 bbox 전체가 가이드 안에 있는지 ----------
        # inside_rect = (
        #     left >= guide_left and
        #     right <= guide_right and
        #     top >= guide_top and
        #     bottom <= guide_bottom
        # )

        # app_logger.debug(
        #     f"face bbox=({left},{top},{right},{bottom}), "
        #     f"guide=({guide_left},{guide_top},{guide_right},{guide_bottom}), "
        #     f"inside_rect={inside_rect}"
        # )

        # # ---------- 4) 가이드 밖이면 실패 ----------
        # if not inside_rect:
        #     return IdentifyResult(
        #         success=False,
        #         message="가이드 영역 안에서 인증해주세요",
        #         reason="out_of_area"
        #     )

        # ------------------------
        # 임베딩 생성
        # ------------------------
        embedding = face_service.embed(face_image)

        if embedding is None:
            return IdentifyResult(
                success=False,
                message="얼굴 임베딩 생성 실패",
                reason="bad_quality"
            )

        # ------------------------
        # DB 사용자와 비교
        # ------------------------
        best_match = find_best_match(db, embedding)

        if best_match is None:
            return IdentifyResult(
                success=False,
                message="등록된 얼굴이 없습니다",
                reason="unknown"
            )

        employee_id, name, min_distance = best_match

        # Log the best match that was found (decision still pending threshold check)
        app_logger.info(f"Best match found: {employee_id} ({name}), distance={min_distance:.4f}")

        # 거리 기준 체크
        if min_distance > settings.TOLERANCE:
            app_logger.warning(
                f"Face detected but similarity too low: distance={min_distance:.4f}, "
                f"threshold={settings.TOLERANCE}"
            )
            return IdentifyResult(
                success=False,
                message="등록된 얼굴이 아닙니다",
                reason="unknown"
            )

        # Accepted -> log acceptance after threshold check
        app_logger.info(
            f"Best match accepted: {employee_id} ({name}), distance={min_distance:.4f}"
        )

        # 통과 → 성공
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
    db 매칭
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
        
        # 각 등록된 임베딩과 비교 (인덱스/총량 로그 포함)
        total = len(users_with_embeddings)
        for idx, user in enumerate(users_with_embeddings, start=1):
            app_logger.debug(f"Checking user [{idx}/{total}]: {user.employee_id}, path: {user.profile_image}")

            # 임베딩 로드
            stored_embedding = face_service.load_embedding(user.profile_image)

            if stored_embedding is None:
                app_logger.warning(f"Failed to load embedding from {user.profile_image} for user {user.employee_id}")
                continue

            # 로그: 로드된 임베딩 형태
            try:
                emb_shape = getattr(stored_embedding, 'shape', None)
                app_logger.debug(f"Loaded embedding for {user.employee_id}, shape={emb_shape}")
            except Exception:
                app_logger.debug(f"Loaded embedding for {user.employee_id}, type={type(stored_embedding)}")

            # 거리 계산
            distance = face_service.l2_distance(embedding, stored_embedding)
            app_logger.debug(f"[{idx}/{total}] Distance for {user.employee_id}: {distance:.4f}, {user.name}")

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



def enroll_user_with_image(db: Session, name: str, file_bytes: bytes) -> EnrollResult:
    try:
        # 1) employee_id 자동 생성
        employee_id = generate_employee_id(db)

        # 2) 이미지 디코딩
        image = face_service.decode_image(file_bytes)
        if image is None:
            return EnrollResult(False, None, "이미지를 디코딩할 수 없습니다", "bad_quality")

        # 3) 이미지 크기 validation
        if not validate_image_size(image):
            return EnrollResult(False, None, "이미지가 너무 작습니다", "bad_quality")

        image = resize_image(image)

        # 4) 썸네일 저장
        profile_image_path = face_service.save_thumbnail(image, employee_id)
        if profile_image_path is None:
            return EnrollResult(False, None, "프로필 이미지 저장 실패", "internal_error")

        # 5) 얼굴 감지
        face_result = face_service.detect_single_face(image)
        if face_result is None:
            return EnrollResult(False, None, "얼굴을 감지할 수 없습니다. 정면 사진을 사용해주세요.", "no_face")

        bbox, face_image = face_result

        # 6) 임베딩 생성
        embedding = face_service.embed(face_image)
        if embedding is None:
            return EnrollResult(False, None, "얼굴 임베딩 생성 실패", "bad_quality")

        # 7) 임베딩 저장
        embedding_path = face_service.save_embedding(employee_id, embedding)
        if embedding_path is None:
            return EnrollResult(False, None, "임베딩 저장 실패", "internal_error")

        # 8) DB에 user 생성
        user = User(
            employee_id=employee_id,
            name=name,
            profile_image=embedding_path
        )
        db.add(user)
        db.commit()

        # 9) 성공 반환
        return EnrollResult(True, employee_id, "등록 완료")

    except Exception as e:
        db.rollback()
        return EnrollResult(False, None, "등록 중 오류가 발생했습니다", "internal_error")



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
