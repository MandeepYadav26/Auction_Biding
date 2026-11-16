"""
Phase 11 + 12 — Bidder Routes

Phase 11 — Watchlist + My Bids + Won Auctions
Phase 12 — Payment + Invoice
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
    PaymentCreate,
    PaymentResponse,
    InvoiceDetailResponse,
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
from app.services.payment_service import process_payment, get_invoice
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


# ── Phase 12: Payment + Invoice ───────────────────────────────

@router.post("/bidder/won-auctions/{won_auction_id}/pay", response_model=PaymentResponse)
def make_payment(
    won_auction_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simulate payment for a won auction.

    Submit your delivery address to complete the simulated payment.
    After payment:
    - payment_status changes from 'pending' → 'paid'
    - An invoice is automatically generated (INV-YYYY-NNNN)

    This is a simulated payment for university project purposes.
    No real payment gateway is involved.
    """
    won = process_payment(
        db=db,
        won_auction_id=won_auction_id,
        bidder_id=current_user.id,
        delivery_address=payment_data.delivery_address,
    )
    # Build response with invoice number
    invoice_number = won.invoice.invoice_number if won.invoice else None
    return PaymentResponse(
        won_auction_id=won.id,
        auction_id=won.auction_id,
        winning_amount=won.winning_amount,
        payment_status=won.payment_status,
        delivery_address=won.delivery_address,
        paid_at=won.paid_at,
        invoice_number=invoice_number,
    )


@router.get("/bidder/won-auctions/{won_auction_id}/invoice", response_model=InvoiceDetailResponse)
def get_my_invoice(
    won_auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    View the invoice for a won auction.

    Only available after payment is completed.
    Shows invoice number, amount, auction title, delivery address, and bidder info.
    """
    # First verify this won_auction belongs to the user
    won = get_won_auction_by_id(db, won_auction_id=won_auction_id, bidder_id=current_user.id)
    if not won:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Won auction not found or does not belong to you.",
        )

    invoice = get_invoice(db, won_auction_id=won_auction_id, bidder_id=current_user.id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found. Please complete payment first.",
        )

    return InvoiceDetailResponse(
        invoice_number=invoice.invoice_number,
        amount=invoice.amount,
        created_at=invoice.created_at,
        auction_id=won.auction_id,
        auction_title=won.auction.title if won.auction else None,
        payment_status=won.payment_status,
        delivery_address=won.delivery_address,
        paid_at=won.paid_at,
        bidder_id=current_user.id,
        bidder_name=current_user.name,
    )
