"""
Watchlist model — bidders can watch auctions they are interested in
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    id         = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)
    bidder_id  = Column(Integer, ForeignKey("users.id"),    nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # A bidder can only watch an auction once
    __table_args__ = (
        UniqueConstraint("auction_id", "bidder_id", name="uq_watchlist_auction_bidder"),
    )

    # Relationships
    auction = relationship("Auction", back_populates="watchlist")
    bidder  = relationship("User",    back_populates="watchlist")

    def __repr__(self):
        return f"<Watchlist id={self.id} auction_id={self.auction_id} bidder_id={self.bidder_id}>"
