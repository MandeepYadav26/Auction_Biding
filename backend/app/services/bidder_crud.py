"""
Phase 11 — Bidder CRUD Services

Covers:
- Watchlist: add, remove, list
- My Bids: list all bids placed by the bidder with current win/lose status
- Won Auctions: list auctions the bidder has won
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.models.watchlist   import Watchlist
from app.models.bid         import Bid
from app.models.won_auction import WonAuction
from app.models.auction     import Auction, AuctionStatus


# ── Watchlist ─────────────────────────────────────────────────

def add_to_watchlist(db: Session, bidder_id: int, auction_id: int) -> Watchlist:
    """Add an auction to the bidder's watchlist. Raises ValueError if already added."""
    # Check auction exists
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise ValueError(f"Auction {auction_id} not found.")

    # Guard: prevent watching own auction (seller's)
    if auction.seller_id == bidder_id:
        raise ValueError("You cannot watch your own auction listing.")

    entry = Watchlist(auction_id=auction_id, bidder_id=bidder_id)
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
        return entry
    except IntegrityError:
        db.rollback()
        raise ValueError("Auction is already in your watchlist.")


def remove_from_watchlist(db: Session, bidder_id: int, watchlist_id: int) -> bool:
    """Remove an entry from the bidder's watchlist. Returns True if removed, False if not found."""
    entry = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.bidder_id == bidder_id)
        .first()
    )
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def remove_from_watchlist_by_auction(db: Session, bidder_id: int, auction_id: int) -> bool:
    """Remove an auction from watchlist using auction_id (alternative to watchlist_id)."""
    entry = (
        db.query(Watchlist)
        .filter(Watchlist.auction_id == auction_id, Watchlist.bidder_id == bidder_id)
        .first()
    )
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def get_watchlist(db: Session, bidder_id: int) -> List[Watchlist]:
    """Get all watchlist entries for a bidder, with auction eagerly loaded."""
    return (
        db.query(Watchlist)
        .options(joinedload(Watchlist.auction).joinedload(Auction.category))
        .filter(Watchlist.bidder_id == bidder_id)
        .order_by(Watchlist.created_at.desc())
        .all()
    )


# ── My Bids ───────────────────────────────────────────────────

def get_my_bids(
    db: Session,
    bidder_id: int,
    skip: int = 0,
    limit: int = 50,
) -> List[Bid]:
    """
    Get all bids placed by the bidder, with auction info eagerly loaded.
    Shows the most recent bid per auction (useful for UI), ordered newest first.
    """
    return (
        db.query(Bid)
        .options(joinedload(Bid.auction).joinedload(Auction.category))
        .filter(Bid.bidder_id == bidder_id)
        .order_by(Bid.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ── Won Auctions ──────────────────────────────────────────────

def get_my_won_auctions(db: Session, bidder_id: int) -> List[WonAuction]:
    """Get all auctions won by the bidder."""
    return (
        db.query(WonAuction)
        .options(
            joinedload(WonAuction.auction).joinedload(Auction.category),
        )
        .filter(WonAuction.bidder_id == bidder_id)
        .order_by(WonAuction.created_at.desc())
        .all()
    )


def get_won_auction_by_id(db: Session, won_auction_id: int, bidder_id: int) -> Optional[WonAuction]:
    """Get a specific won auction (must belong to the bidder)."""
    return (
        db.query(WonAuction)
        .options(joinedload(WonAuction.auction))
        .filter(WonAuction.id == won_auction_id, WonAuction.bidder_id == bidder_id)
        .first()
    )
