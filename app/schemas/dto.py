"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ===== Health Check =====

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp (ISO format)")


# ===== Identify =====

class IdentifyRequestJSON(BaseModel):
    """Identify request (JSON mode - uses camera)"""
    type: str = Field(..., description="Attendance type: IN or OUT")
    device_id: Optional[str] = Field(None, description="Device identifier")
    ts_client: Optional[datetime] = Field(None, description="Client timestamp")


class IdentifyResponseSuccess(BaseModel):
    """Identify success response"""
    success: bool = True
    employee_id: str = Field(..., description="Employee ID")
    name: str = Field(..., description="Employee name")
    user: str = Field(..., description="Employee name (alias)")
    distance: float = Field(..., description="Face recognition distance")
    decided_threshold: float = Field(..., description="Decision threshold used")
    message: str = Field(..., description="Success message")


class IdentifyResponseFailure(BaseModel):
    """Identify failure response"""
    success: bool = False
    message: str = Field(..., description="Error message")
    reason: Optional[str] = Field(None, description="Failure reason code")
    min_distance: Optional[float] = Field(None, description="Minimum distance to known faces")


# ===== Enroll =====

class EnrollResponseSuccess(BaseModel):
    """Enroll success response"""
    success: bool = True
    employee_id: str = Field(..., description="Employee ID")
    message: str = Field(..., description="Success message")


class EnrollResponseFailure(BaseModel):
    """Enroll failure response"""
    success: bool = False
    message: str = Field(..., description="Error message")
    reason: Optional[str] = Field(None, description="Failure reason code")


# ===== Attendance (optional) =====

class AttendanceRequest(BaseModel):
    """Direct attendance logging request"""
    employee_id: str = Field(..., description="Employee ID")
    type: str = Field(..., description="Attendance type: IN or OUT")
    device_id: Optional[str] = Field(None, description="Device identifier")
    distance: Optional[float] = Field(None, description="Face recognition distance")
    image_ref: Optional[str] = Field(None, description="Image reference path")
    ts_client: Optional[datetime] = Field(None, description="Client timestamp")


class AttendanceResponse(BaseModel):
    """Attendance logging response"""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Response message")


# ===== Error Response =====

class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    message: str = Field(..., description="Error message")
    error: Optional[str] = Field(None, description="Error details")
