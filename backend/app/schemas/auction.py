"""
Pydantic schemas for Auction
"""

from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.auction import AuctionStatus, ItemCondition
from app.schemas.category import CategoryResponse


# ── Request schemas ────────────────────────────────────────────

class AuctionCreate(BaseModel):
    """Seller creates a new auction"""
    category_id:       int
    title:             str
    description:       Optional[str]    = None
    condition:         ItemCondition
    starting_bid:      Decimal
    minimum_increment: Decimal          = Decimal("50.00")
    reserve_price:     Optional[Decimal] = None
    buy_it_now_price:  Optional[Decimal] = None
    start_time:        datetime
    end_time:          datetime

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("starting_bid")
    @classmethod
    def starting_bid_positive(cls, v):
        if v <= 0:
            raise ValueError("Starting bid must be greater than 0")
        return v

    @field_validator("minimum_increment")
    @classmethod
    def increment_positive(cls, v):
        if v <= 0:
            raise ValueError("Minimum increment must be greater than 0")
        return v

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("End time must be after start time")
        return v


class AuctionUpdate(BaseModel):
    """Seller updates a draft auction"""
    title:             Optional[str]     = None
    description:       Optional[str]     = None
    condition:         Optional[ItemCondition] = None
    starting_bid:      Optional[Decimal] = None
    minimum_increment: Optional[Decimal] = None
    reserve_price:     Optional[Decimal] = None
    buy_it_now_price:  Optional[Decimal] = None
    start_time:        Optional[datetime] = None
    end_time:          Optional[datetime] = None
    category_id:       Optional[int]     = None


# ── Response schemas ───────────────────────────────────────────

class AuctionListItem(BaseModel):
    """Compact info for auction list/cards"""
    id:                int
    title:             str
    condition:         ItemCondition
    image:             Optional[str]
    starting_bid:      Decimal
    current_bid:       Optional[Decimal]
    buy_it_now_price:  Optional[Decimal]
    end_time:          datetime
    status:            AuctionStatus
    total_bids:        int
    category_id:       int
    seller_id:         int

    class Config:
        from_attributes = True


class AuctionDetail(BaseModel):
    """Full auction info for the detail page"""
    id:                int
    seller_id:         int
    title:             str
    description:       Optional[str]
    condition:         ItemCondition
    image:             Optional[str]
    starting_bid:      Decimal
    current_bid:       Optional[Decimal]
    minimum_increment: Decimal
    reserve_price:     Optional[Decimal]   # hidden from non-sellers
    buy_it_now_price:  Optional[Decimal]
    start_time:        datetime
    end_time:          datetime
    status:            AuctionStatus
    total_bids:        int
    winner_id:         Optional[int]
    created_at:        datetime
    category:          Optional[CategoryResponse] = None

    class Config:
        from_attributes = True
