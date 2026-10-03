"""
ProxyBid model — stores a bidder's maximum willing amount (hidden from others)
"""

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class ProxyBid(Base):
    __tablename__ = "proxy_bids"

    id         = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)
    bidder_id  = Column(Integer, ForeignKey("users.id"),    nullable=False)
    max_amount = Column(Numeric(12, 2), nullable=False)   # NEVER shown to others
    is_active  = Column(Boolean, default=True)            # False when outbid beyond max
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    auction = relationship("Auction", back_populates="proxy_bids")
    bidder  = relationship("User",    back_populates="proxy_bids")

    def __repr__(self):
        return f"<ProxyBid id={self.id} auction_id={self.auction_id} bidder_id={self.bidder_id}>"
