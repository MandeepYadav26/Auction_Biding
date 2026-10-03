"""
Auction model — the core of the platform
"""

from sqlalchemy import (
    Column, Integer, String, Text, Enum,
    Numeric, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
import enum


class AuctionStatus(str, enum.Enum):
    draft    = "draft"
    pending  = "pending"    # waiting for admin approval
    active   = "active"     # live, bidding open
    ended    = "ended"      # time expired
    sold     = "sold"       # winner determined
    cancelled = "cancelled"


class ItemCondition(str, enum.Enum):
    new         = "new"
    like_new    = "like_new"
    good        = "good"
    fair        = "fair"
    poor        = "poor"


class Auction(Base):
    __tablename__ = "auctions"

    id               = Column(Integer, primary_key=True, index=True)
    seller_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id      = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Product details
    title            = Column(String(200), nullable=False)
    description      = Column(Text, nullable=True)
    condition        = Column(Enum(ItemCondition), nullable=False)
    image            = Column(String(500), nullable=True)   # file path

    # Pricing
    starting_bid     = Column(Numeric(12, 2), nullable=False)
    current_bid      = Column(Numeric(12, 2), nullable=True)   # updated on each bid
    minimum_increment = Column(Numeric(12, 2), nullable=False, default=50)
    reserve_price    = Column(Numeric(12, 2), nullable=True)   # optional
    buy_it_now_price = Column(Numeric(12, 2), nullable=True)   # optional

    # Timing
    start_time       = Column(DateTime(timezone=True), nullable=False)
    end_time         = Column(DateTime(timezone=True), nullable=False)

    # Status & meta
    status           = Column(Enum(AuctionStatus), default=AuctionStatus.draft, nullable=False)
    winner_id        = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_bids       = Column(Integer, default=0)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    seller      = relationship("User",     back_populates="auctions", foreign_keys=[seller_id])
    winner      = relationship("User",     foreign_keys=[winner_id])
    category    = relationship("Category", back_populates="auctions")
    bids        = relationship("Bid",      back_populates="auction", cascade="all, delete-orphan")
    proxy_bids  = relationship("ProxyBid", back_populates="auction", cascade="all, delete-orphan")
    watchlist   = relationship("Watchlist", back_populates="auction", cascade="all, delete-orphan")
    won_auction = relationship("WonAuction", back_populates="auction", uselist=False)

    def __repr__(self):
        return f"<Auction id={self.id} title={self.title} status={self.status}>"
