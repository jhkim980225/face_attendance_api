from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Base 정의 (여기서!)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    profile_image = Column(String(255), nullable=True)  # 프로필 이미지 경로    
    created_at = Column(DateTime, nullable=False, server_default=func.now())    
    __table_args__ = (
        Index('idx_employee_id', 'employee_id'),
    )


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), index=True, nullable=True)
    type = Column(String(10), nullable=False)  # IN, OUT
    device_id = Column(String(50), nullable=True)
    distance = Column(Float, nullable=True)
    ts_server = Column(DateTime, nullable=False, server_default=func.now())
    ts_client = Column(DateTime, nullable=True)
    image_ref = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_attendance_employee_id', 'employee_id'),
        Index('idx_attendance_ts_server', 'ts_server'),
    )