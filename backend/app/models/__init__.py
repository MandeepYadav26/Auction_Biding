"""
Import all models here so SQLAlchemy knows about them
when creating tables via Base.metadata.create_all()
"""

from app.models.user       import User, UserRole
from app.models.category   import Category
from app.models.auction    import Auction, AuctionStatus, ItemCondition
from app.models.bid        import Bid, BidType
from app.models.proxy_bid  import ProxyBid
from app.models.watchlist  import Watchlist
from app.models.won_auction import WonAuction, PaymentStatus
from app.models.invoice    import Invoice

__all__ = [
    "User", "UserRole",
    "Category",
    "Auction", "AuctionStatus", "ItemCondition",
    "Bid", "BidType",
    "ProxyBid",
    "Watchlist",
    "WonAuction", "PaymentStatus",
    "Invoice",
]
