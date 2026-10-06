"""
Authentication routes: Register, Login, and current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserResponse, TokenResponse
from app.services.user_crud import get_user_by_email, create_user
from app.utils.hashing import verify_password
from app.utils.jwt_handler import create_access_token
from app.utils.auth_dependency import get_current_user

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user. 
    Role can be 'seller' or 'bidder'. 'admin' is usually restricted, but for this project we'll allow it or rely on seed data.
    """
    # Check if email is already taken
    existing_user = get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
    
    # Create user (password will be hashed inside create_user)
    new_user = create_user(db, user_data)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint. 
    NOTE: OAuth2PasswordRequestForm uses 'username' and 'password' fields.
    Send the user's email in the 'username' field. Form-Data is expected here.
    """
    # Authenticate user
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )
    
    # Generate JWT Token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get the currently logged-in user's profile.
    Requires a valid JWT Bearer token in the Authorization header.
    """
    return current_user
