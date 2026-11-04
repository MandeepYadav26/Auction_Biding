"""
Phase 10 — Buy It Now Service

Logic:
  1. Validate the auction is active, timing is valid, BIN price is set
  2. Seller cannot Buy-It-Now their own auction
  3. Atomically:
     a. Set auction.status = sold
     b. Set auction.winner_id = bidder.id
     c. Set auction.current_bid = buy_it_now_price
     d. Create a Bid record (bid_type = 'manual', amount = bin_price)
     e. Create WonAuction record (payment_status = pending)
     f. Deactivate all proxy_bids for this auction
  4. Return summary response
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone
from decimal import Decimal

from app.models.auction    import Auction, AuctionStatus
from app.models.bid        import Bid, BidType
from app.models.proxy_bid  import ProxyBid
from app.models.won_auction import WonAuction, PaymentStatus
from app.models.user       import User


def buy_it_now(db: Session, auction_id: int, bidder: User) -> dict:
    """
    Instantly purchase an auction at its Buy-It-Now price.

    Returns a dict with auction and WonAuction summary.
    """
    # 1. Lock the auction row
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

    # 2. Must be active
    if auction.status != AuctionStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot Buy-It-Now on auction with status '{auction.status.value}'.",
        )

    # 3. BIN price must be set
    if auction.buy_it_now_price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This auction does not have a Buy-It-Now price.",
        )

    # 4. Timing checks
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

    # 5. Seller cannot BIN their own auction
    if auction.seller_id == bidder.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot Buy-It-Now your own auction.",
        )

    bin_price = Decimal(str(auction.buy_it_now_price))

    # 6. Atomically close the auction at BIN price
    auction.status     = AuctionStatus.sold
    auction.winner_id  = bidder.id
    auction.current_bid = bin_price
    auction.total_bids  = (auction.total_bids or 0) + 1

    # 6a. Create Bid record for the BIN purchase
    bin_bid = Bid(
        auction_id=auction.id,
        bidder_id=bidder.id,
        amount=bin_price,
        bid_type=BidType.manual,
    )
    db.add(bin_bid)

    # 6b. Create WonAuction record
    existing_won = db.query(WonAuction).filter(WonAuction.auction_id == auction.id).first()
    if existing_won:
        # Edge case: somehow already won — update it
        existing_won.bidder_id = bidder.id
        existing_won.winning_amount = bin_price
        existing_won.payment_status = PaymentStatus.pending
        won = existing_won
    else:
        won = WonAuction(
            auction_id=auction.id,
            bidder_id=bidder.id,
            winning_amount=bin_price,
            payment_status=PaymentStatus.pending,
        )
        db.add(won)

    # 6c. Deactivate all proxy bids — auction is now closed
    db.query(ProxyBid).filter(ProxyBid.auction_id == auction.id).update(
        {"is_active": False}, synchronize_session=False
    )

    db.commit()
    db.refresh(won)

    return {
        "auction_id":     auction.id,
        "auction_title":  auction.title,
        "winner_id":      bidder.id,
        "bin_price":      bin_price,
        "status":         auction.status,
        "won_auction_id": won.id,
    }
