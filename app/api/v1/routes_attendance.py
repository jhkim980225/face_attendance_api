"""
Attendance logging endpoint (optional)
POST /attendance - Directly log attendance record
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.dto import AttendanceRequest, AttendanceResponse
from app.services import attendance_service
from app.core.logging import app_logger

router = APIRouter()


@router.post("/attendance", response_model=AttendanceResponse)
async def log_attendance(
    request: AttendanceRequest,
    db: Session = Depends(get_db)
):
    """
    Directly log attendance record
    
    This endpoint allows direct attendance logging without face recognition.
    Useful for manual entries or integration with other systems.
    
    Request body:
    {
        "employee_id": "EMP001",
        "type": "IN" | "OUT",
        "device_id": "DEVICE_01",  // optional
        "distance": 0.35,           // optional
        "image_ref": "path/to/image.jpg",  // optional
        "ts_client": "2025-01-01T12:00:00Z"  // optional
    }
    """
    try:
        app_logger.info(f"Attendance log request: {request.employee_id} - {request.type}")
        
        success = attendance_service.record_success(
            db=db,
            employee_id=request.employee_id,
            type=request.type,
            device_id=request.device_id,
            distance=request.distance,
            image_ref=request.image_ref,
            ts_client=request.ts_client
        )
        
        if success:
            return {
                "success": True,
                "message": "출퇴근 기록이 저장되었습니다"
            }
        else:
            return {
                "success": False,
                "message": "출퇴근 기록 저장에 실패했습니다"
            }
            
    except Exception as e:
        app_logger.error(f"Error in attendance endpoint: {e}")
        return {
            "success": False,
            "message": "내부 오류가 발생했습니다"
        }
