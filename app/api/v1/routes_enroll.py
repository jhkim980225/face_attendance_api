"""
User enrollment endpoint
POST /enroll - Register new user with auto-generated employee_id
"""
from fastapi import APIRouter, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.db.base import get_db
from app.services import inference
from app.core.logging import app_logger
from app.utils.image_io import validate_image_extension


router = APIRouter()


@router.post("/enroll")
async def enroll_user(
    name: str = Form(..., description="User name (required)"),
    image: UploadFile = File(..., description="Profile image (required)"),
    db: Session = Depends(get_db)
):
    print("<< enroll ")
    try:
        app_logger.info(f"Enroll request: name={name}, filename={image.filename}")
        
        # Validate image extension
        if not validate_image_extension(image.filename):
            return {
                "success": False,
                "message": "지원하지 않는 이미지 형식입니다. JPG, PNG, BMP, WEBP 형식을 사용해주세요.",
                "reason": "invalid_format"
            }
        
        # Read image bytes
        file_bytes = await image.read()
        
        if len(file_bytes) == 0:
            return {
                "success": False,
                "message": "이미지 파일이 비어있습니다",
                "reason": "empty_file"
            }
        
        # Enroll user (employee_id will be auto-generated)
        result = inference.enroll_user_with_image(
            db=db,
            name=name,
            file_bytes=file_bytes
        )
        
        return result.to_dict()
        
    except Exception as e:
        app_logger.error(f"Error in enroll endpoint: {e}")
        return {
            "success": False,
            "message": "내부 오류가 발생했습니다",
            "reason": "internal_error"
        }
