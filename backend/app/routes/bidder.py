"""
Phase 11 — Bidder Routes

Endpoints:
  Watchlist:
    POST   /watchlist                     → Add auction to watchlist
    GET    /watchlist                     → View my watchlist
    DELETE /watchlist/{id}               → Remove by watchlist entry id
    DELETE /watchlist/auction/{auction_id} → Remove by auction id

  My Bids:
    GET    /bidder/my-bids               → All bids I have placed

  Won Auctions:
    GET    /bidder/won-auctions          → Auctions I have won
    GET    /bidder/won-auctions/{id}     → Single won auction detail
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.models.user import User
from app.models.auction import Auction
from app.schemas.bidding import (
    WatchlistCreate,
    WatchlistResponse,
    MyBidItem,
    WonAuctionResponse,
)
from app.services.bidder_crud import (
    add_to_watchlist,
    remove_from_watchlist,
    remove_from_watchlist_by_auction,
    get_watchlist,
    get_my_bids,
    get_my_won_auctions,
    get_won_auction_by_id,
)
from app.utils.auth_dependency import get_current_user

router = APIRouter(tags=["Bidder"])


# ── Watchlist ─────────────────────────────────────────────────

@router.post("/watchlist", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_watchlist(
    data: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an auction to your watchlist. Each auction can be added only once."""
    try:
        return add_to_watchlist(db, bidder_id=current_user.id, auction_id=data.auction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/watchlist", response_model=List[WatchlistResponse])
def view_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all auctions in your watchlist with current bid, time remaining, and status."""
    return get_watchlist(db, bidder_id=current_user.id)


@router.delete("/watchlist/{watchlist_id}", status_code=status.HTTP_200_OK)
def remove_watchlist_entry(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a watchlist entry by its watchlist entry id."""
    removed = remove_from_watchlist(db, bidder_id=current_user.id, watchlist_id=watchlist_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist entry not found or does not belong to you.",
        )
    return {"message": "Removed from watchlist."}


@router.delete("/watchlist/auction/{auction_id}", status_code=status.HTTP_200_OK)
def remove_watchlist_by_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove an auction from your watchlist using the auction's id."""
    removed = remove_from_watchlist_by_auction(db, bidder_id=current_user.id, auction_id=auction_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This auction is not in your watchlist.",
        )
    return {"message": "Removed from watchlist."}


# ── My Bids ───────────────────────────────────────────────────

@router.get("/bidder/my-bids", response_model=List[MyBidItem])
def my_bids(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    View all bids you have placed across all auctions, newest first.
    Each item shows the auction title, your bid amount, and whether you are currently winning.
    """
    bids = get_my_bids(db, bidder_id=current_user.id, skip=skip, limit=limit)

    result = []
    for bid in bids:
        auction: Auction = bid.auction
        is_winning = (auction.winner_id == current_user.id) if auction else False
        result.append(MyBidItem(
            id=bid.id,
            auction_id=bid.auction_id,
            auction_title=auction.title if auction else None,
            auction_status=auction.status if auction else None,
            amount=bid.amount,
            bid_type=bid.bid_type,
            created_at=bid.created_at,
            is_winning=is_winning,
        ))
    return result


# ── Won Auctions ──────────────────────────────────────────────

@router.get("/bidder/won-auctions", response_model=List[WonAuctionResponse])
def my_won_auctions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View all auctions you have won. Shows payment status and delivery info."""
    return get_my_won_auctions(db, bidder_id=current_user.id)


@router.get("/bidder/won-auctions/{won_auction_id}", response_model=WonAuctionResponse)
def won_auction_detail(
    won_auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full details of a specific won auction (must be yours)."""
    won = get_won_auction_by_id(db, won_auction_id=won_auction_id, bidder_id=current_user.id)
    if not won:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Won auction not found or does not belong to you.",
        )
    return won
