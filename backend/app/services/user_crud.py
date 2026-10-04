"""
CRUD operations for User model
"""

from sqlalchemy.orm import Session
from app.models.user  import User, UserRole
from app.schemas.user import UserRegister
from app.utils.hashing import hash_password
from typing import Optional


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def get_users_by_role(db: Session, role: UserRole):
    return db.query(User).filter(User.role == role).all()


def create_user(db: Session, data: UserRegister) -> User:
    hashed_pw = hash_password(data.password)
    user = User(
        name=data.name,
        email=data.email,
        password=hashed_pw,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user
