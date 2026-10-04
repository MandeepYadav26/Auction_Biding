"""
Pydantic schemas for Bids, ProxyBid, Watchlist, WonAuction, Invoice
"""

from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.bid import BidType
from app.models.won_auction import PaymentStatus


# ── Bid ───────────────────────────────────────────────────────

class BidCreate(BaseModel):
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Bid amount must be greater than 0")
        return v


class BidResponse(BaseModel):
    id:         int
    auction_id: int
    bidder_id:  int
    amount:     Decimal
    bid_type:   BidType
    created_at: datetime

    class Config:
        from_attributes = True


# ── ProxyBid ──────────────────────────────────────────────────

class ProxyBidCreate(BaseModel):
    max_amount: Decimal

    @field_validator("max_amount")
    @classmethod
    def max_positive(cls, v):
        if v <= 0:
            raise ValueError("Max amount must be greater than 0")
        return v


class ProxyBidResponse(BaseModel):
    id:         int
    auction_id: int
    bidder_id:  int
    # NOTE: max_amount NOT returned — it's secret!
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Watchlist ─────────────────────────────────────────────────

class WatchlistCreate(BaseModel):
    auction_id: int


class WatchlistResponse(BaseModel):
    id:         int
    auction_id: int
    bidder_id:  int
    created_at: datetime

    class Config:
        from_attributes = True


# ── WonAuction ────────────────────────────────────────────────

class WonAuctionResponse(BaseModel):
    id:               int
    auction_id:       int
    bidder_id:        int
    winning_amount:   Decimal
    payment_status:   PaymentStatus
    delivery_address: Optional[str]
    created_at:       datetime
    paid_at:          Optional[datetime]

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    delivery_address: str


# ── Invoice ───────────────────────────────────────────────────

class InvoiceResponse(BaseModel):
    id:             int
    won_auction_id: int
    invoice_number: str
    amount:         Decimal
    created_at:     datetime

    class Config:
        from_attributes = True
