"""
Bidding routes: Placing bids, proxy bids, and viewing bid history
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.models.user import User, UserRole
from app.schemas.bidding import BidCreate, BidResponse, BidHistoryItem, ProxyBidCreate, ProxyBidResponse
from app.services.bidding_crud import place_bid, get_auction_bids
from app.services.proxy_bid_service import set_proxy_bid
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


# ── Phase 8: Proxy Bid ─────────────────────────────────────────

@router.post("/auctions/{auction_id}/proxy-bid", response_model=ProxyBidResponse, status_code=status.HTTP_201_CREATED)
def set_proxy_bid_endpoint(
    auction_id: int,
    proxy_data: ProxyBidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set or update a proxy (automatic) bid on an auction.

    The system will automatically bid on your behalf up to your secret max amount.
    Your max amount is NEVER shown to other bidders.

    - If you're not yet bidding, the system immediately places an opening bid.
    - If someone outbids you (but under your max), the system automatically counters.
    - If someone bids over your max, you'll be outbid and your proxy deactivated.
    """
    return set_proxy_bid(
        db=db,
        auction_id=auction_id,
        bidder=current_user,
        max_amount=proxy_data.max_amount,
    )

