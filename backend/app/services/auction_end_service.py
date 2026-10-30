"""
Phase 9 — Auction Ending Service

Handles the business logic when an auction's end_time passes:
  1. Find all active auctions whose end_time <= now
  2. For each expired auction:
     a. If no bids → status = 'ended'  (no sale)
     b. If bids exist + reserve_price not met → status = 'ended'  (reserve not met)
     c. If bids exist + reserve_price met (or no reserve) → status = 'sold'
        - Create WonAuction record
        - Deactivate all proxy_bids for that auction
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import logging

from sqlalchemy.orm import Session

from app.models.auction   import Auction, AuctionStatus
from app.models.won_auction import WonAuction, PaymentStatus
from app.models.proxy_bid import ProxyBid

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    """Make a datetime timezone-aware (UTC) if it is naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def close_single_auction(db: Session, auction: Auction) -> str:
    """
    Close one expired auction.

    Returns a short string describing the outcome for logging:
        'ended_no_bids' | 'ended_reserve_not_met' | 'sold'
    """
    # ── 1. Determine outcome ──────────────────────────────────────

    if auction.current_bid is None or auction.winner_id is None:
        # No bids were placed
        auction.status = AuctionStatus.ended
        db.commit()
        logger.info("Auction %d closed: no bids → ended", auction.id)
        return "ended_no_bids"

    current_bid = Decimal(str(auction.current_bid))

    # Check reserve price
    if auction.reserve_price is not None:
        reserve = Decimal(str(auction.reserve_price))
        if current_bid < reserve:
            # Reserve not met
            auction.status = AuctionStatus.ended
            db.commit()
            logger.info(
                "Auction %d closed: reserve ₹%s not met (highest bid ₹%s) → ended",
                auction.id, reserve, current_bid
            )
            return "ended_reserve_not_met"

    # ── 2. We have a winner ───────────────────────────────────────

    auction.status = AuctionStatus.sold

    # Create WonAuction record (guard: only if not already created)
    existing = db.query(WonAuction).filter(WonAuction.auction_id == auction.id).first()
    if not existing:
        won = WonAuction(
            auction_id=auction.id,
            bidder_id=auction.winner_id,
            winning_amount=current_bid,
            payment_status=PaymentStatus.pending,
        )
        db.add(won)

    # Deactivate all proxy bids for this auction
    db.query(ProxyBid).filter(ProxyBid.auction_id == auction.id).update(
        {"is_active": False}, synchronize_session=False
    )

    db.commit()
    logger.info(
        "Auction %d closed: winner_id=%d, winning_amount=₹%s → sold",
        auction.id, auction.winner_id, current_bid
    )
    return "sold"


def close_expired_auctions(db: Session) -> dict:
    """
    Scan the DB for all active auctions whose end_time has passed and close them.

    Returns a summary dict:
        { "checked": int, "sold": int, "ended_no_bids": int,
          "ended_reserve_not_met": int, "errors": int }
    """
    now = _now_utc()

    expired = (
        db.query(Auction)
        .filter(
            Auction.status == AuctionStatus.active,
            Auction.end_time <= now,
        )
        .all()
    )

    summary = {
        "checked": len(expired),
        "sold": 0,
        "ended_no_bids": 0,
        "ended_reserve_not_met": 0,
        "errors": 0,
    }

    for auction in expired:
        try:
            result = close_single_auction(db, auction)
            if result in summary:
                summary[result] += 1
        except Exception as exc:
            logger.error("Error closing auction %d: %s", auction.id, exc, exc_info=True)
            summary["errors"] += 1
            db.rollback()  # rollback only this auction's transaction

    return summary
