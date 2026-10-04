"""
CRUD operations for Auction model
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from datetime import datetime, timezone
from typing import Optional, List

from app.models.auction   import Auction, AuctionStatus
from app.schemas.auction  import AuctionCreate, AuctionUpdate


def get_auction_by_id(db: Session, auction_id: int) -> Optional[Auction]:
    """Fetch auction with category loaded (for detail page)."""
    return (
        db.query(Auction)
        .options(joinedload(Auction.category))
        .filter(Auction.id == auction_id)
        .first()
    )


def get_all_auctions(
    db: Session,
    status: Optional[AuctionStatus] = AuctionStatus.active,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Auction]:
    """Browse auctions with optional filters."""
    query = db.query(Auction)

    if status:
        query = query.filter(Auction.status == status)
    if category_id:
        query = query.filter(Auction.category_id == category_id)
    if search:
        query = query.filter(Auction.title.ilike(f"%{search}%"))

    return query.order_by(Auction.end_time.asc()).offset(skip).limit(limit).all()


def get_seller_auctions(db: Session, seller_id: int) -> List[Auction]:
    """All auctions by a specific seller."""
    return (
        db.query(Auction)
        .filter(Auction.seller_id == seller_id)
        .order_by(Auction.created_at.desc())
        .all()
    )


def create_auction(db: Session, seller_id: int, data: AuctionCreate) -> Auction:
    """Create a new auction as draft."""
    auction = Auction(
        seller_id=seller_id,
        category_id=data.category_id,
        title=data.title,
        description=data.description,
        condition=data.condition,
        starting_bid=data.starting_bid,
        current_bid=None,                 # no bids yet
        minimum_increment=data.minimum_increment,
        reserve_price=data.reserve_price,
        buy_it_now_price=data.buy_it_now_price,
        start_time=data.start_time,
        end_time=data.end_time,
        status=AuctionStatus.pending,     # goes to admin for approval
        total_bids=0,
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction


def update_auction(db: Session, auction_id: int, data: AuctionUpdate) -> Optional[Auction]:
    """Seller updates a draft auction."""
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(auction, field, value)
    db.commit()
    db.refresh(auction)
    return auction


def update_auction_status(db: Session, auction_id: int, status: AuctionStatus) -> Optional[Auction]:
    """Admin approves/rejects — or system marks ended/sold."""
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        return None
    auction.status = status
    db.commit()
    db.refresh(auction)
    return auction


def update_auction_image(db: Session, auction_id: int, image_path: str) -> Optional[Auction]:
    """Save uploaded image path."""
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        return None
    auction.image = image_path
    db.commit()
    db.refresh(auction)
    return auction


def get_ending_soon_auctions(db: Session, limit: int = 6) -> List[Auction]:
    """Active auctions ending soonest — for homepage."""
    return (
        db.query(Auction)
        .filter(Auction.status == AuctionStatus.active)
        .order_by(Auction.end_time.asc())
        .limit(limit)
        .all()
    )


def get_pending_auctions(db: Session) -> List[Auction]:
    """All auctions waiting for admin approval."""
    return (
        db.query(Auction)
        .filter(Auction.status == AuctionStatus.pending)
        .order_by(Auction.created_at.asc())
        .all()
    )
