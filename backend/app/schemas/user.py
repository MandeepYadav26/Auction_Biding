"""
Pydantic schemas for User — request/response validation
"""

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from app.models.user import UserRole


# ── Request schemas (what frontend sends) ──────────────────────

class UserRegister(BaseModel):
    """Used for POST /register"""
    name:     str
    email:    EmailStr
    password: str
    role:     UserRole = UserRole.bidder

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    """Used for POST /login"""
    email:    EmailStr
    password: str


# ── Response schemas (what backend returns) ────────────────────

class UserResponse(BaseModel):
    """Safe user info — never includes password"""
    id:         int
    name:       str
    email:      str
    role:       UserRole
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True   # allows SQLAlchemy model → Pydantic


class TokenResponse(BaseModel):
    """JWT token returned after login"""
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse
