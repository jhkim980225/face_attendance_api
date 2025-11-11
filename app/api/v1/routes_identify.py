"""
Face identification endpoint
POST /identify - Identify face from camera or uploaded image
"""
from fastapi import APIRouter, Depends, File, UploadFile, Form, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.base import get_db
from app.schemas.dto import IdentifyRequestJSON
from app.services import inference
from app.services import attendance_service
from app.core.logging import app_logger

router = APIRouter()


@router.post("/identify")
async def identify_face(
    json_body: Optional[IdentifyRequestJSON] = Body(None),
    image: Optional[UploadFile] = File(None),
    type: Optional[str] = Form(None),
    device_id: Optional[str] = Form(None),
    ts_client: Optional[str] = Form(None),    
    db: Session = Depends(get_db)
):

    try:
        
        if json_body is not None:
            
            app_logger.info(f"Identify request (JSON mode): type={json_body.type}")
            
            attendance_type = json_body.type.upper()
            device_id_val = json_body.device_id
            ts_client_val = json_body.ts_client
            
            
            result = inference.identify_from_camera(db)
            
        elif image is not None and type is not None:
            
            app_logger.info(f"Identify request (multipart mode): type={type}")
            
            attendance_type = type.upper()
            device_id_val = device_id
            
            # Parse client timestamp if provided
            ts_client_val = None
            if ts_client:
                try:
                    ts_client_val = datetime.fromisoformat(ts_client.replace('Z', '+00:00'))
                except Exception as e:
                    app_logger.warning(f"Failed to parse ts_client: {e}")
            
            # Read image file
            file_bytes = await image.read()
            
            # Identify from upload
            result = inference.identify_from_upload(db, file_bytes)
            
        else:
            # Invalid request
            return {
                "success": False,
                "message": "Invalid request. Provide either JSON body or multipart form data with image and type."
            }
        
        # Record attendance if identification succeeded
        if result.success:
            # 출근(IN) 타입이면 오늘 이미 출근했는지 체크
            if attendance_type.upper() == 'IN':
                already_checked_in = attendance_service.check_already_checked_in_today(
                    db=db,
                    employee_id=result.employee_id
                )
                
                if already_checked_in:
                    return {
                        "success": False,
                        "message": "이미 출근 처리되었습니다",
                        "reason": "already_checked_in",
                        "employee_id": result.employee_id,
                        "name": result.name
                    }
            
            # 퇴근(OUT) 타입이면 오늘 이미 퇴근했는지 체크
            elif attendance_type.upper() == 'OUT':
                already_checked_out = attendance_service.check_already_checked_out_today(
                    db=db,
                    employee_id=result.employee_id
                )
                
                if already_checked_out:
                    return {
                        "success": False,
                        "message": "이미 퇴근 처리되었습니다",
                        "reason": "already_checked_out",
                        "employee_id": result.employee_id,
                        "name": result.name
                    }
            
            attendance_service.record_success(
                db=db,
                employee_id=result.employee_id,
                type=attendance_type,
                device_id=device_id_val,
                distance=result.distance,
                ts_client=ts_client_val
            )
        # 실패 시 기록하지 않음 (attendance 테이블에 남기지 않음)
        
        return result.to_dict()
        
    except Exception as e:
        app_logger.error(f"Error in identify endpoint: {e}")
        return {
            "success": False,
            "message": "내부 오류가 발생했습니다",
            "reason": "internal_error"
        }
