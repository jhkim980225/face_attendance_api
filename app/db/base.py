"""
Database connection and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from app.core.config import settings
from app.core.logging import app_logger

# Database URL
DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
    f"?charset=utf8mb4"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.MYSQL_POOL_SIZE,
    max_overflow=settings.MYSQL_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Check if database connection is alive
    Returns True if connection is successful
    """
    try:
        with engine.connect() as conn:
            # Use text() wrapper for raw SQL
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        app_logger.error(f"Database connection check failed: {e}")
        return False


def init_db():
    """
    Initialize database tables
    Creates all tables defined in models
    """
    try:
        from app.db.models import Base
        
        app_logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        app_logger.info("Database tables created successfully")
        
        # Verify connection
        if check_db_connection():
            app_logger.info("Database connection verified")
        else:
            app_logger.warning("Database connection verification failed")
            
    except Exception as e:
        app_logger.error(f"Failed to initialize database: {e}")
        raise