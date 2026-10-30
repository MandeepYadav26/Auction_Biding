"""
Admin routes: Dashboard statistics, Auction approval/rejection, Category management, User management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.models.user import User, UserRole
from app.models.auction import AuctionStatus
from app.schemas.admin import AdminStats, UserStatusUpdate
from app.schemas.user import UserResponse
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.auction import AuctionListItem, AuctionDetail
from app.services.admin_crud import (
    get_admin_stats,
    get_all_users_admin,
    set_user_active_status,
    get_admin_auctions,
)
from app.services.auction_crud import (
    get_auction_by_id,
    update_auction_status,
)
from app.services.category_crud import (
    get_category_by_id,
    get_all_categories,
    create_category,
    update_category,
    delete_category,
)
from app.services.auction_end_service import close_expired_auctions  # Phase 9
from app.utils.auth_dependency import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])

# Ensure only users with admin role can access these endpoints
get_admin_user = require_role(UserRole.admin)


# ── Statistics ─────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStats)
def get_platform_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get platform overview statistics for admin dashboard."""
    return get_admin_stats(db)


# ── Auction Approvals & Management ─────────────────────────────

@router.get("/auctions", response_model=List[AuctionListItem])
def list_admin_auctions(
    status: Optional[AuctionStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List auctions for admin review with optional status filter."""
    return get_admin_auctions(db, status=status, skip=skip, limit=limit)


@router.get("/auctions/{auction_id}", response_model=AuctionDetail)
def get_admin_auction_detail(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get full details of any auction for admin inspection."""
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found."
        )
    return auction


@router.put("/auctions/{auction_id}/approve", response_model=AuctionDetail)
def approve_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Approve a pending auction listing, making it active for bidding."""
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found."
        )

    if auction.status not in [AuctionStatus.pending, AuctionStatus.draft]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve auction with status '{auction.status.value}'."
        )

    updated = update_auction_status(db, auction_id, AuctionStatus.active)
    return updated


@router.put("/auctions/{auction_id}/reject", response_model=AuctionDetail)
def reject_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Reject an auction listing, setting its status to cancelled."""
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found."
        )

    if auction.status in [AuctionStatus.ended, AuctionStatus.sold]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject auction with status '{auction.status.value}'."
        )

    updated = update_auction_status(db, auction_id, AuctionStatus.cancelled)
    return updated


# ── Category Management ───────────────────────────────────────

@router.get("/categories", response_model=List[CategoryResponse])
def get_all_categories_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get all categories (including inactive ones) for admin management."""
    return get_all_categories(db, active_only=False)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_new_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new auction category."""
    return create_category(db, category_data)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_existing_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update category name, description, or active status."""
    category = update_category(db, category_id, category_data)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
def delete_existing_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Soft delete (deactivate) a category."""
    success = delete_category(db, category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )
    return {"message": "Category successfully deactivated."}


# ── User Management ───────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
def list_users(
    role: Optional[UserRole] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List users with optional role filtering."""
    return get_all_users_admin(db, role=role, skip=skip, limit=limit)


@router.put("/users/{user_id}/status", response_model=UserResponse)
def toggle_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Activate or deactivate a user account."""
    if user_id == current_user.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot deactivate their own account."
        )

    user = set_user_active_status(db, user_id, status_data.is_active)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user


# ── Phase 9: Manual auction closer (for testing / emergency) ──

@router.post("/run-auction-closer", tags=["Admin"])
def run_auction_closer_manually(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Manually trigger the auction-ending process.
    Closes all active auctions whose end_time has passed.
    (The background scheduler runs this automatically every 60 seconds.)
    """
    summary = close_expired_auctions(db)
    return {"message": "Auction closer completed.", "summary": summary}
