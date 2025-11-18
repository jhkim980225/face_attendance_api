"""
Camera worker for MODE_A (server-side camera)
Manages single camera capture in background thread for MJPEG streaming
"""
import cv2
import threading
import time
import numpy as np
import os
from typing import Optional
from app.core.config import settings
from app.core.logging import app_logger

# OpenCV 경고 메시지 완전히 숨기기
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
cv2.setLogLevel(0)



class CameraWorker:
    """
    서버 측 카메라를 백그라운드 스레드로 계속 캡처하고, 최신 프레임을 MJPEG 스트리밍에 제공
    OpenCV 카메라 -> frame read -> latest_frame
    """
    
    def __init__(self, device_index: int = None, fps: int = None):        
        self.device_index = device_index or settings.CAMERA_DEVICE_INDEX # 사용할 카메라 장치 번호
        self.target_fps = fps or settings.STREAM_FPS # 목표 fps
        self.frame_interval = 1.0 / self.target_fps # 프레임 간격 (1/FPS)
        
        self.cap: Optional[cv2.VideoCapture] = None # OpenCV VideoCapture 객체
        self.latest_frame: Optional[np.ndarray] = None # 최신 프레임 (numpy array)
        self.latest_frame_time: float = 0  # 프레임 캡처 시간
        self.thread: Optional[threading.Thread] = None # 캡처 스레드
        self.running = False # 스레드 동작 여부
        self.lock = threading.Lock() # 프레임 lock
        self.last_error: Optional[str] = None # 에러 메세지
        
    def start(self) -> bool:
        """
        카메라 on / 백그라운드 캡처
        """
        if self.running:
            app_logger.warning("Camera worker already running")
            return True
        
        try:
            # Open camera
            self.cap = cv2.VideoCapture(self.device_index)
            
            if not self.cap.isOpened():
                self.last_error = f"Failed to open camera device {self.device_index}"
                app_logger.error(self.last_error)
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Start capture thread
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
            app_logger.info(f"Camera worker started (device={self.device_index}, fps={self.target_fps})")
            return True
            
        except Exception as e:
            self.last_error = f"Camera initialization error: {e}"
            app_logger.error(self.last_error)
            return False
    
    def stop(self):
        """Stop camera capture thread"""
        if not self.running:
            return
        
        app_logger.info("Stopping camera worker...")
        self.running = False
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        # Release camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        with self.lock:
            self.latest_frame = None
        
        app_logger.info("Camera worker stopped")
    
    def is_alive(self) -> bool:
        """카메라 캡처 스레드 정상 동작 확인"""
        return self.running and self.thread and self.thread.is_alive()
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        캡처된 프레임 반환
        """
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return None
    
    def _capture_loop(self):
        """
        Main capture loop (runs in background thread)
        Continuously captures frames at target FPS
        """
        app_logger.debug("Camera capture loop started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Capture frame
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    self.last_error = "Failed to capture frame"                    
                    # 프레임 캡처 실패 시 latest_frame 무효화
                    with self.lock:
                        self.latest_frame = None
                        self.latest_frame_time = 0
                    time.sleep(0.1)
                    continue
                
                # Update latest frame with timestamp
                with self.lock:
                    self.latest_frame = frame
                    self.latest_frame_time = time.time()
                
                # Maintain target FPS
                elapsed = time.time() - start_time
                sleep_time = max(0, self.frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                self.last_error = f"Capture loop error: {e}"
                app_logger.error(self.last_error)
                time.sleep(0.5)
        
        app_logger.debug("Camera capture loop ended")
    
    def get_last_error(self) -> Optional[str]:
        """Get last error message"""
        return self.last_error


# Global camera worker instance
camera_worker = CameraWorker()
