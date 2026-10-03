"""
Database connection setup using SQLAlchemy
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# MySQL connection URL format:
# mysql+pymysql://user:password@host:port/database
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8mb4"
)

# Engine — manages connection pool to MySQL
engine = create_engine(
    DATABASE_URL,
    echo=settings.DEBUG,       # prints SQL queries in dev mode
    pool_pre_ping=True,        # checks connection is alive before using
    pool_recycle=3600,         # recycle connections every 1 hour
)

# SessionLocal — each request gets its own session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base — all SQLAlchemy models will inherit from this
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — provides a database session per request.
    Usage in routes:
        def my_route(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test that we can actually connect to MySQL."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection: OK")
        return True
    except Exception as e:
        print(f"Database connection FAILED: {e}")
        return False
