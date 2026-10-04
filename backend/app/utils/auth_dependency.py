"""
Authentication dependency for FastAPI routes.
Phase 3: skeleton ready — Phase 4 will add full logic.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.config.database  import get_db
from app.models.user      import User, UserRole
from app.utils.jwt_handler import decode_token
from app.services.user_crud import get_user_by_id

# This tells FastAPI where the login endpoint is (for Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str   = Depends(oauth2_scheme),
    db:  Session = Depends(get_db),
) -> User:
    """
    Extract user from JWT token.
    Raises 401 if token is missing/invalid/expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: UserRole):
    """
    Factory that returns a dependency checking user role.

    Usage:
        @router.get("/admin/...", dependencies=[Depends(require_role(UserRole.admin))])
    """
    def _check(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {[r.value for r in roles]}",
            )
        return current_user
    return _check
