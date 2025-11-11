"""
MJPEG stream endpoint
GET /stream.mjpeg - Streams video from server camera (MODE_A)
"""
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import cv2
import numpy as np

from app.services.camera_worker import camera_worker
from app.services import face_service
from app.core.logging import app_logger

# MTCNN 임포트
try:
    from mtcnn import MTCNN
    mtcnn_stream_detector = MTCNN()
    MTCNN_STREAM_AVAILABLE = True
    app_logger.info("MTCNN loaded for stream")
except:
    MTCNN_STREAM_AVAILABLE = False
    app_logger.warning("MTCNN not available for stream, using OpenCV")

router = APIRouter()


@router.get("/stream.mjpeg")
async def stream_mjpeg():
    """
    MJPEG video stream endpoint
    
    Streams video frames from server camera in multipart/x-mixed-replace format
    Returns 503 if camera is not available
    """
    # Check if camera worker is running
    if not camera_worker.is_alive():
        error_msg = camera_worker.get_last_error() or "Camera not available"
        app_logger.warning(f"Stream request but camera not available: {error_msg}")
        return Response(
            content=f"Camera not available: {error_msg}",
            status_code=503,
            media_type="text/plain"
        )
    
    def generate_frames():
        """Generator function to yield video frames with face detection overlay"""
        try:
            while True:
                # Get latest frame from camera worker
                frame = camera_worker.get_latest_frame()
                
                if frame is None:
                    # No frame available, skip
                    continue
                
                # 프레임 크기
                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2
                
                # 타원 영역 정의 (중앙) - 크기 축소
                ellipse_width = int(w * 0.35)  # 화면 너비의 35% (기존 50%)
                ellipse_height = int(h * 0.55)  # 화면 높이의 55% (기존 70%)
                
                # 타원 그리기 (굵은 선)
                cv2.ellipse(frame, (center_x, center_y), (ellipse_width // 2, ellipse_height // 2), 
                           0, 0, 360, (100, 100, 100), 3)  # 회색, 굵은 선
                
                # 얼굴 감지 시도
                try:
                    if MTCNN_STREAM_AVAILABLE:
                        # MTCNN 사용 (정확한 얼굴만 감지)
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        detections = mtcnn_stream_detector.detect_faces(rgb_frame)
                        
                        # confidence 0.90 이상만 사용
                        faces = []
                        for det in detections:
                            if det['confidence'] >= 0.90:
                                x, y, w, h = det['box']
                                faces.append((x, y, w, h))
                    else:
                        # OpenCV Fallback
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                        detected = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(20, 20))
                        faces = [(x, y, w, h) for x, y, w, h in detected]
                    
                    # 타원 영역 내의 얼굴만 필터링
                    valid_faces = []
                    for (x, y, w_face, h_face) in faces:
                        face_center_x = x + w_face // 2
                        face_center_y = y + h_face // 2
                        
                        # 타원 내부 체크 (타원 방정식 사용)
                        normalized_x = (face_center_x - center_x) / (ellipse_width / 2)
                        normalized_y = (face_center_y - center_y) / (ellipse_height / 2)
                        is_inside = (normalized_x ** 2 + normalized_y ** 2) <= 1
                        
                        if is_inside:
                            valid_faces.append((x, y, w_face, h_face))
                    
                    if len(valid_faces) == 0:
                        # 타원 영역 내 얼굴 없음
                        cv2.putText(frame, "No face in guide area", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(frame, "Move to center circle", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    elif len(valid_faces) > 1:
                        # 여러 얼굴 - 경고
                        for (x, y, w_face, h_face) in valid_faces:
                            cv2.rectangle(frame, (x, y), (x+w_face, y+h_face), (0, 165, 255), 2)  # 주황색
                        cv2.putText(frame, "Multiple faces in area", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                        cv2.putText(frame, "Only one person allowed", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    else:
                        # 타원 내 얼굴 1개 감지됨
                        x, y, w_face, h_face = valid_faces[0]
                        
                        # 얼굴 크기 체크
                        face_area = w_face * h_face
                        frame_area = frame.shape[0] * frame.shape[1]
                        face_ratio = face_area / frame_area
                        
                        if face_ratio < 0.05:  # 너무 작음
                            cv2.rectangle(frame, (x, y), (x+w_face, y+h_face), (0, 255, 255), 2)  # 노란색
                            cv2.putText(frame, "Face too small", (10, 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            cv2.putText(frame, "Please move closer", (10, 60), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        elif face_ratio > 0.4:  # 너무 큼
                            cv2.rectangle(frame, (x, y), (x+w_face, y+h_face), (0, 255, 255), 2)  # 노란색
                            cv2.putText(frame, "Too close", (10, 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            cv2.putText(frame, "Please move back", (10, 60), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        else:
                            # 적절한 크기 - 초록색 박스
                            cv2.rectangle(frame, (x, y), (x+w_face, y+h_face), (0, 255, 0), 3)  # 초록색, 두꺼운 선
                            cv2.putText(frame, "Good! Face detected", (10, 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            cv2.putText(frame, "Look straight ahead", (10, 60), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # 얼굴 크기 정보 표시
                        cv2.putText(frame, f"Face size: {face_ratio*100:.1f}%", (10, frame.shape[0] - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                except Exception as e:
                    app_logger.debug(f"Face detection overlay error: {e}")
                
                # Encode frame as JPEG
                success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                if not success:
                    app_logger.warning("Failed to encode frame")
                    continue
                
                # Yield frame in multipart format
                frame_bytes = buffer.tobytes()
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                )
                
        except GeneratorExit:
            app_logger.debug("Stream client disconnected")
        except Exception as e:
            app_logger.error(f"Error in stream generator: {e}")
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
