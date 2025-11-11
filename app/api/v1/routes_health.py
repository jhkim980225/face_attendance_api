"""
Health check endpoint
GET /health - Returns service status and database connectivity
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.base import get_db, check_db_connection
from app.schemas.dto import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    
    Returns service status and verifies database connection
    """
    # Check database connection
    db_ok = check_db_connection()
    
    status = "ok" if db_ok else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
