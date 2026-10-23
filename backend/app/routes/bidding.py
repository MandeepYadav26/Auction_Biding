"""
Bidding routes: Placing bids and viewing bid history
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.models.user import User, UserRole
from app.schemas.bidding import BidCreate, BidResponse, BidHistoryItem
from app.services.bidding_crud import place_bid, get_auction_bids
from app.services.auction_crud import get_auction_by_id
from app.utils.auth_dependency import get_current_user

router = APIRouter(tags=["Bidding"])


@router.post("/auctions/{auction_id}/bid", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
def place_new_bid(
    auction_id: int,
    bid_data: BidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Place a manual bid on an active auction.
    Enforces minimum increment, start/end timing, self-bid restriction, and highest bidder checks.
    """
    return place_bid(
        db=db,
        auction_id=auction_id,
        bidder=current_user,
        amount=bid_data.amount,
    )


@router.get("/auctions/{auction_id}/bids", response_model=List[BidHistoryItem])
def list_auction_bids(
    auction_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get the complete bid history for an auction, newest first.
    """
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found."
        )
    return get_auction_bids(db=db, auction_id=auction_id, skip=skip, limit=limit)
