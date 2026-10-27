"""
CRUD and business logic for Bidding (Phase 7 Normal + Phase 8 Proxy)
"""

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid, BidType
from app.models.user import User


def place_bid(
    db: Session,
    auction_id: int,
    bidder: User,
    amount: Decimal,
) -> Bid:
    """
    Validate and place a manual bid on an auction atomically.
    """
    # 1. Fetch auction with row lock (concurrency protection)
    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .with_for_update()
        .first()
    )

    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )

    # 2. Check auction status
    if auction.status != AuctionStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot bid on auction with status '{auction.status.value}'.",
        )

    # 3. Check timing
    now = datetime.now(timezone.utc)

    start_time = auction.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if now < start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has not started yet.",
        )

    end_time = auction.end_time
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    if now >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has already ended.",
        )

    # 4. Check self-bidding (seller cannot bid on own listing)
    if auction.seller_id == bidder.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot bid on your own auction listing.",
        )

    # 5. Check if bidder is already the highest bidder
    if auction.winner_id == bidder.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already the highest bidder on this auction.",
        )

    # 6. Minimum required bid validation
    # If no bids yet: minimum is starting_bid.
    # If bids exist: minimum is current_bid + minimum_increment.
    if auction.current_bid is None:
        min_required = auction.starting_bid
    else:
        min_required = auction.current_bid + auction.minimum_increment

    if amount < min_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid amount must be at least ₹{min_required:.2f}.",
        )

    # 7. Create new bid record (append-only log)
    new_bid = Bid(
        auction_id=auction.id,
        bidder_id=bidder.id,
        amount=amount,
        bid_type=BidType.manual,
    )
    db.add(new_bid)

    # 8. Update auction highest bid, winner_id, total_bids
    auction.current_bid = amount
    auction.winner_id = bidder.id
    auction.total_bids = (auction.total_bids or 0) + 1

    # 9. Phase 8: Trigger proxy counter-bid if any proxy exists
    from app.services.proxy_bid_service import trigger_proxy_after_manual_bid
    trigger_proxy_after_manual_bid(db, auction, bidder.id, amount)

    db.commit()
    db.refresh(new_bid)
    return new_bid


def get_auction_bids(
    db: Session,
    auction_id: int,
    skip: int = 0,
    limit: int = 50,
) -> List[Bid]:
    """
    Get all bids for an auction in reverse chronological order (newest first).
    Eager loads the bidder relationship for display.
    """
    return (
        db.query(Bid)
        .options(joinedload(Bid.bidder))
        .filter(Bid.auction_id == auction_id)
        .order_by(Bid.created_at.desc(), Bid.amount.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
