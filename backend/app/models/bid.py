"""
Bid model — every bid placed by a bidder
"""

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
import enum


class BidType(str, enum.Enum):
    manual = "manual"       # bidder typed an amount
    proxy  = "proxy"        # system auto-bid from proxy


class Bid(Base):
    __tablename__ = "bids"

    id         = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)
    bidder_id  = Column(Integer, ForeignKey("users.id"),    nullable=False)
    amount     = Column(Numeric(12, 2), nullable=False)
    bid_type   = Column(Enum(BidType), default=BidType.manual, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    auction = relationship("Auction", back_populates="bids")
    bidder  = relationship("User",    back_populates="bids")

    @property
    def bidder_name(self) -> str:
        return self.bidder.name if self.bidder else "Unknown"

    def __repr__(self):
        return f"<Bid id={self.id} auction_id={self.auction_id} amount={self.amount}>"
