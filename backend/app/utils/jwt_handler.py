"""
JWT token creation and verification utility
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.config.settings import settings


def create_access_token(data: dict) -> str:
    """
    Create a JWT token.
    data should include: {"sub": user_id, "role": user_role}
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    Returns the payload dict or raises JWTError.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
