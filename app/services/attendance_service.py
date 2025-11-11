"""
Attendance service
Handles attendance logging to database
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.models import Attendance
from app.core.logging import app_logger


def check_already_checked_in_today(db: Session, employee_id: str) -> bool:
    """
    Check if employee already checked in today
    
    Args:
        db: Database session
        employee_id: Employee ID
        
    Returns:
        True if already checked in today
    """
    try:
        today = date.today()
        
        # 오늘 날짜의 IN 기록 조회
        existing = db.query(Attendance)\
            .filter(
                and_(
                    Attendance.employee_id == employee_id,
                    Attendance.type == 'IN',
                    func.date(Attendance.ts_server) == today
                )
            )\
            .first()
        
        return existing is not None
        
    except Exception as e:
        app_logger.error(f"Error checking attendance: {e}")
        return False


def check_already_checked_out_today(db: Session, employee_id: str) -> bool:
    """
    Check if employee already checked out today
    
    Args:
        db: Database session
        employee_id: Employee ID
        
    Returns:
        True if already checked out today
    """
    try:
        today = date.today()
        
        # 오늘 날짜의 OUT 기록 조회
        existing = db.query(Attendance)\
            .filter(
                and_(
                    Attendance.employee_id == employee_id,
                    Attendance.type == 'OUT',
                    func.date(Attendance.ts_server) == today
                )
            )\
            .first()
        
        return existing is not None
        
    except Exception as e:
        app_logger.error(f"Error checking attendance: {e}")
        return False


def record_success(
    db: Session,
    employee_id: str,
    type: str,
    device_id: Optional[str] = None,
    distance: Optional[float] = None,
    image_ref: Optional[str] = None,
    ts_client: Optional[datetime] = None
) -> bool:
    """
    Record successful attendance (check-in/check-out)
    
    Args:
        db: Database session
        employee_id: Employee ID
        type: Attendance type ('IN' or 'OUT')
        device_id: Optional device identifier
        distance: Optional face recognition distance
        image_ref: Optional reference to saved image
        ts_client: Optional client timestamp
        
    Returns:
        True if recorded successfully
    """
    try:
        attendance = Attendance(
            employee_id=employee_id,
            type=type.upper(),
            device_id=device_id,
            distance=distance,
            image_ref=image_ref,
            ts_client=ts_client
        )
        
        db.add(attendance)
        db.commit()
        
        app_logger.info(f"Attendance recorded: {employee_id} - {type} (distance: {distance})")
        return True
        
    except Exception as e:
        app_logger.error(f"Error recording attendance: {e}")
        db.rollback()
        return False


def record_unknown(
    db: Session,
    type: str,
    device_id: Optional[str] = None,
    distance: Optional[float] = None,
    image_ref: Optional[str] = None,
    ts_client: Optional[datetime] = None
) -> bool:
    """
    Record unknown face attempt
    Stores with employee_id='UNKNOWN' for audit trail
    
    Args:
        db: Database session
        type: Attempted type ('IN' or 'OUT')
        device_id: Optional device identifier
        distance: Optional minimum distance to known faces
        image_ref: Optional reference to saved image
        ts_client: Optional client timestamp
        
    Returns:
        True if recorded successfully
    """
    try:
        attendance = Attendance(
            employee_id="UNKNOWN",
            type=type.upper(),
            device_id=device_id,
            distance=distance,
            image_ref=image_ref,
            ts_client=ts_client
        )
        
        db.add(attendance)
        db.commit()
        
        app_logger.warning(f"Unknown face attempt recorded - {type} (distance: {distance})")
        return True
        
    except Exception as e:
        app_logger.error(f"Error recording unknown attempt: {e}")
        db.rollback()
        return False


def record_fail(
    db: Session,
    reason: str,
    type: str,
    device_id: Optional[str] = None,
    ts_client: Optional[datetime] = None
) -> bool:
    """
    Record failed attendance attempt
    Stores with employee_id='FAILED_{reason}' for audit trail
    
    Args:
        db: Database session
        reason: Failure reason (no_face, multi_face, bad_quality, etc.)
        type: Attempted type ('IN' or 'OUT')
        device_id: Optional device identifier
        ts_client: Optional client timestamp
        
    Returns:
        True if recorded successfully
    """
    try:
        attendance = Attendance(
            employee_id=f"FAILED_{reason.upper()}",
            type=type.upper(),
            device_id=device_id,
            ts_client=ts_client
        )
        
        db.add(attendance)
        db.commit()
        
        app_logger.warning(f"Failed attendance recorded: {reason} - {type}")
        return True
        
    except Exception as e:
        app_logger.error(f"Error recording failed attempt: {e}")
        db.rollback()
        return False


def get_recent_attendance(
    db: Session,
    employee_id: str,
    limit: int = 10
) -> list:
    """
    Get recent attendance records for an employee
    
    Args:
        db: Database session
        employee_id: Employee ID
        limit: Maximum number of records to return
        
    Returns:
        List of Attendance records
    """
    try:
        records = db.query(Attendance)\
            .filter(Attendance.employee_id == employee_id)\
            .order_by(Attendance.ts_server.desc())\
            .limit(limit)\
            .all()
        
        return records
    except Exception as e:
        app_logger.error(f"Error querying attendance: {e}")
        return []
