"""
Phase 8 — Proxy Bidding Service

Proxy Bidding Logic:
1. Bidder sets a secret max_amount (not visible to others).
2. When a manual bid comes in, system checks if any existing proxy bidder
   can be auto-incremented to beat the new manual bid.
3. System places proxy bids automatically (bid_type='proxy') just enough to
   stay ahead by minimum_increment, up to the proxy's max_amount.
4. If the new manual bid exceeds all proxy max_amounts, the manual bidder wins.
5. If two proxy bidders compete, higher max_amount wins at the lowest possible increment.

Example Flow:
  Auction: starting_bid=1000, min_increment=100
  Bidder A sets proxy max=3000  → system auto-bids 1000 (opening)
  Bidder B manually bids 1200   → proxy fires: A auto-bids 1300, B is outbid
  Bidder B sets proxy max=2500  → A auto-bids 2600 (B max+100), B exhausted
  Bidder C manually bids 3100   → C beats A's proxy max (3000), C wins
"""

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional, List

from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid, BidType
from app.models.proxy_bid import ProxyBid
from app.models.user import User
from fastapi import HTTPException, status
from datetime import datetime, timezone


# ── Internal helpers ────────────────────────────────────────────

def _get_min_required(auction: Auction) -> Decimal:
    """Calculate the minimum valid bid for the current auction state."""
    if auction.current_bid is None:
        return Decimal(str(auction.starting_bid))
    return Decimal(str(auction.current_bid)) + Decimal(str(auction.minimum_increment))


def _record_bid(db: Session, auction: Auction, bidder_id: int, amount: Decimal, bid_type: BidType):
    """Append a bid record and update auction state atomically (no commit — caller commits)."""
    bid = Bid(
        auction_id=auction.id,
        bidder_id=bidder_id,
        amount=amount,
        bid_type=bid_type,
    )
    db.add(bid)
    auction.current_bid = amount
    auction.winner_id = bidder_id
    auction.total_bids = (auction.total_bids or 0) + 1
    return bid


def _get_active_proxy(db: Session, auction_id: int, bidder_id: int) -> Optional[ProxyBid]:
    """Get an active proxy bid for a specific bidder on an auction."""
    return (
        db.query(ProxyBid)
        .filter(
            ProxyBid.auction_id == auction_id,
            ProxyBid.bidder_id == bidder_id,
            ProxyBid.is_active == True,
        )
        .first()
    )


def _get_highest_proxy(db: Session, auction_id: int, exclude_bidder_id: int) -> Optional[ProxyBid]:
    """
    Get the single highest active proxy bid on an auction,
    excluding a specific bidder (used when a new manual/proxy bid fires).
    """
    return (
        db.query(ProxyBid)
        .filter(
            ProxyBid.auction_id == auction_id,
            ProxyBid.bidder_id != exclude_bidder_id,
            ProxyBid.is_active == True,
        )
        .order_by(ProxyBid.max_amount.desc())
        .first()
    )


def _deactivate_proxy(db: Session, proxy: ProxyBid):
    """Mark a proxy as exhausted / outbid beyond max."""
    proxy.is_active = False


# ── Main proxy fire function ────────────────────────────────────

def _fire_proxy_counter(
    db: Session,
    auction: Auction,
    incoming_bidder_id: int,
    incoming_amount: Decimal,
) -> Optional[Decimal]:
    """
    After a new bid lands, check if an existing proxy bidder can counter it.
    Returns the proxy counter-bid amount if fired, else None.
    """
    # Find the highest active proxy from someone other than the incoming bidder
    counter_proxy = _get_highest_proxy(db, auction.id, exclude_bidder_id=incoming_bidder_id)
    if not counter_proxy:
        return None  # No proxy to counter

    counter_max = Decimal(str(counter_proxy.max_amount))
    min_inc = Decimal(str(auction.minimum_increment))
    needed = incoming_amount + min_inc  # proxy needs to beat incoming by 1 increment

    if counter_max >= needed:
        # Proxy can counter — bid just enough to win
        proxy_bid_amount = needed
        _record_bid(db, auction, counter_proxy.bidder_id, proxy_bid_amount, BidType.proxy)
        return proxy_bid_amount
    else:
        # Proxy is exhausted — deactivate it
        _deactivate_proxy(db, counter_proxy)
        return None  # incoming bidder wins


# ── Public API: Set / Update Proxy Bid ─────────────────────────

def set_proxy_bid(
    db: Session,
    auction_id: int,
    bidder: User,
    max_amount: Decimal,
) -> ProxyBid:
    """
    Set or update a proxy bid for a bidder on an auction.
    If the bidder sets a proxy, the system immediately places a bid on their
    behalf if needed to establish them as the current winner.
    """
    # 1. Lock the auction row
    auction = (
        db.query(Auction)
        .filter(Auction.id == auction_id)
        .with_for_update()
        .first()
    )
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found.")

    # 2. Auction must be active
    if auction.status != AuctionStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot set proxy bid on auction with status '{auction.status.value}'.",
        )

    # 3. Timing checks
    now = datetime.now(timezone.utc)
    end_time = auction.end_time
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    if now >= end_time:
        raise HTTPException(status_code=400, detail="Auction has already ended.")

    start_time = auction.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if now < start_time:
        raise HTTPException(status_code=400, detail="Auction has not started yet.")

    # 4. Seller cannot proxy-bid on own auction
    if auction.seller_id == bidder.id:
        raise HTTPException(status_code=400, detail="You cannot bid on your own auction.")

    # 5. max_amount must exceed current highest bid (or starting bid)
    floor = _get_min_required(auction)
    if max_amount < floor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proxy max amount must be at least ₹{floor:.2f} (current minimum bid).",
        )

    # 6. Upsert proxy record
    existing_proxy = (
        db.query(ProxyBid)
        .filter(ProxyBid.auction_id == auction_id, ProxyBid.bidder_id == bidder.id)
        .first()
    )
    if existing_proxy:
        # Updating max amount — must be higher than existing
        if max_amount <= Decimal(str(existing_proxy.max_amount)):
            raise HTTPException(
                status_code=400,
                detail=f"New proxy max must be higher than your current proxy (₹{existing_proxy.max_amount:.2f}).",
            )
        existing_proxy.max_amount = max_amount
        existing_proxy.is_active = True
        proxy = existing_proxy
    else:
        proxy = ProxyBid(
            auction_id=auction_id,
            bidder_id=bidder.id,
            max_amount=max_amount,
        )
        db.add(proxy)

    # 7. Now figure out if the new proxy setter needs to place an immediate bid
    #    or if they can take over from the current winner
    current_winner_id = auction.winner_id

    if current_winner_id is None:
        # No bids yet — proxy places opening bid = starting_bid
        opening_bid = Decimal(str(auction.starting_bid))
        _record_bid(db, auction, bidder.id, opening_bid, BidType.proxy)

    elif current_winner_id == bidder.id:
        # This bidder is already winning — proxy just updates their max silently
        pass

    else:
        # Competition: check if this new proxy can outbid current winner's proxy
        current_winner_proxy = _get_active_proxy(db, auction_id, current_winner_id)
        min_required = _get_min_required(auction)

        if current_winner_proxy is None:
            # Current winner has no proxy — our new proxy just places min required bid
            if max_amount >= min_required:
                _record_bid(db, auction, bidder.id, min_required, BidType.proxy)
        else:
            # Both have proxies — winner is whoever has higher max
            existing_max = Decimal(str(current_winner_proxy.max_amount))

            if max_amount > existing_max:
                # New proxy wins: counter the existing at existing_max + increment
                winning_amount = min(max_amount, existing_max + Decimal(str(auction.minimum_increment)))
                _record_bid(db, auction, bidder.id, winning_amount, BidType.proxy)
            elif max_amount < existing_max:
                # New proxy loses: existing proxy counters new proxy's max
                counter_amount = min(existing_max, max_amount + Decimal(str(auction.minimum_increment)))
                _record_bid(db, auction, current_winner_id, counter_amount, BidType.proxy)
                _deactivate_proxy(db, proxy)  # new proxy exhausted
            else:
                # Exact tie — first mover (current winner) keeps the advantage
                counter_amount = existing_max + Decimal(str(auction.minimum_increment))
                _record_bid(db, auction, current_winner_id, counter_amount, BidType.proxy)
                _deactivate_proxy(db, proxy)

    db.commit()
    db.refresh(proxy)
    return proxy


# ── Hook: after a manual bid lands, trigger proxy counter ──────

def trigger_proxy_after_manual_bid(
    db: Session,
    auction: Auction,
    manual_bidder_id: int,
    manual_amount: Decimal,
):
    """
    Called inside place_bid() BEFORE commit.
    Checks if any active proxy exists that can counter the new manual bid.
    If yes, fires the proxy counter bid and commits everything together.
    """
    counter_proxy = _get_highest_proxy(db, auction.id, exclude_bidder_id=manual_bidder_id)
    if not counter_proxy:
        return  # No proxy to fire

    counter_max = Decimal(str(counter_proxy.max_amount))
    min_inc = Decimal(str(auction.minimum_increment))
    needed = manual_amount + min_inc

    if counter_max >= needed:
        # Proxy can counter
        _record_bid(db, auction, counter_proxy.bidder_id, needed, BidType.proxy)
    else:
        # Proxy is outbid beyond its max — deactivate it
        _deactivate_proxy(db, counter_proxy)
