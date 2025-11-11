"""
Capture endpoint
GET /capture - Capture current frame from camera
"""
from fastapi import APIRouter, Query
from fastapi.responses import Response, JSONResponse
import cv2

from app.services.camera_worker import camera_worker
from app.core.logging import app_logger

router = APIRouter()


@router.get("/capture")
async def capture_frame(preview: int = Query(0, description="1 for preview, 0 for base64")):
    """
    Capture current frame from server camera
    
    Query params:
    - preview: 1 to return JPEG image, 0 to return base64 encoded image
    
    Returns:
        preview=1: JPEG image
        preview=0: {"success": true, "image": "base64_string"}
    """
    try:
        # Check if camera is available
        if not camera_worker.is_alive():
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "카메라를 사용할 수 없습니다"
                }
            )
        
        # Get latest frame
        frame = camera_worker.get_latest_frame()
        
        if frame is None:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "카메라 프레임을 가져올 수 없습니다"
                }
            )
        
        # Encode frame as JPEG
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        if not success:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "이미지 인코딩 실패"
                }
            )
        
        if preview == 1:
            # Return JPEG image directly
            return Response(
                content=buffer.tobytes(),
                media_type="image/jpeg"
            )
        else:
            # Return base64 encoded image
            import base64
            image_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
            return {
                "success": True,
                "image": f"data:image/jpeg;base64,{image_base64}"
            }
        
    except Exception as e:
        app_logger.error(f"Error in capture endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "캡처 중 오류가 발생했습니다"
            }
        )
