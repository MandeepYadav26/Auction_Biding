"""
CRUD and aggregation services for Admin module
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.models.user import User, UserRole
from app.models.auction import Auction, AuctionStatus


def get_admin_stats(db: Session) -> dict:
    """Fetch count statistics for the admin dashboard."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_sellers = db.query(func.count(User.id)).filter(User.role == UserRole.seller).scalar() or 0
    total_bidders = db.query(func.count(User.id)).filter(User.role == UserRole.bidder).scalar() or 0

    total_auctions = db.query(func.count(Auction.id)).scalar() or 0
    active_auctions = db.query(func.count(Auction.id)).filter(Auction.status == AuctionStatus.active).scalar() or 0
    pending_auctions = db.query(func.count(Auction.id)).filter(Auction.status == AuctionStatus.pending).scalar() or 0
    ended_auctions = db.query(func.count(Auction.id)).filter(
        Auction.status.in_([AuctionStatus.ended, AuctionStatus.sold])
    ).scalar() or 0
    cancelled_auctions = db.query(func.count(Auction.id)).filter(
        Auction.status == AuctionStatus.cancelled
    ).scalar() or 0

    return {
        "total_users": total_users,
        "total_sellers": total_sellers,
        "total_bidders": total_bidders,
        "total_auctions": total_auctions,
        "active_auctions": active_auctions,
        "pending_auctions": pending_auctions,
        "ended_auctions": ended_auctions,
        "cancelled_auctions": cancelled_auctions,
    }


def get_all_users_admin(
    db: Session,
    role: Optional[UserRole] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[User]:
    """List users with optional role filtering."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.id.asc()).offset(skip).limit(limit).all()


def set_user_active_status(db: Session, user_id: int, is_active: bool) -> Optional[User]:
    """Activate or deactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def get_admin_auctions(
    db: Session,
    status: Optional[AuctionStatus] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Auction]:
    """Fetch auctions for admin review with optional status filter."""
    query = db.query(Auction)
    if status:
        query = query.filter(Auction.status == status)
    return query.order_by(Auction.created_at.desc()).offset(skip).limit(limit).all()
