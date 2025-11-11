"""
Face Attendance API - Main Application
FastAPI backend for face recognition attendance system
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging

from app.core.config import settings
from app.core.cors import get_cors_origins, CORS_CONFIG
from app.core.logging import setup_logging, app_logger
from app.db.base import init_db
from app.services.camera_worker import camera_worker

# Import routers
from app.api.v1 import routes_health, routes_stream, routes_identify, routes_enroll, routes_attendance, routes_capture


# Health 체크 로그 필터
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "GET /health" not in record.getMessage()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    app_logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Setup logging
    setup_logging()
    
    # Health 체크 로그 제거
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())
    
    # Initialize database
    try:
        init_db()
        app_logger.info("Database initialized successfully")
    except Exception as e:
        app_logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup - allow app to run even if DB init fails
    
    # Start camera worker (MODE_A)
    # Note: Camera may not be available - app should still work in upload mode
    camera_started = camera_worker.start()
    if camera_started:
        app_logger.info("Camera worker started successfully")
    else:
        app_logger.warning("Camera worker failed to start - MODE_A (camera) features will be unavailable")
        app_logger.warning("Server will operate in MODE_B (upload) only")
    
    app_logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down application...")
    
    # Stop camera worker
    if camera_worker.is_alive():
        camera_worker.stop()
        app_logger.info("Camera worker stopped")
    
    app_logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Face recognition attendance system API with MJPEG streaming and multi-mode support",
    lifespan=lifespan
)

# Configure CORS
cors_origins = get_cors_origins(debug=settings.DEBUG)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    **CORS_CONFIG
)

# Mount static files
if os.path.exists(settings.IMAGE_DIR):
    app.mount("/static/images", StaticFiles(directory=settings.IMAGE_DIR), name="images")

# Include routers
app.include_router(routes_health.router, tags=["Health"])
app.include_router(routes_stream.router, tags=["Stream"])
app.include_router(routes_capture.router, tags=["Capture"])
app.include_router(routes_identify.router, tags=["Identify"])
app.include_router(routes_enroll.router, tags=["Enroll"])
app.include_router(routes_attendance.router, tags=["Attendance"])


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "stream": "/stream.mjpeg",
            "identify": "/identify (POST)",
            "enroll": "/enroll (POST)",
            "attendance": "/attendance (POST)",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=settings.DEBUG
    )
