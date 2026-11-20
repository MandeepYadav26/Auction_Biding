// ============================================================
// api.js — Shared API utility for Auction Bidding Platform
// All endpoints matched to actual backend routes
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (!response.ok) {
    let errorMsg = `HTTP ${response.status}`;
    try { const e = await response.json(); errorMsg = e.detail || JSON.stringify(e); } catch (_) {}
    throw new Error(errorMsg);
  }
  if (response.status === 204) return null;
  return response.json();
}

const API = {
  get:    (ep)       => apiFetch(ep, { method: "GET" }),
  post:   (ep, body) => apiFetch(ep, { method: "POST",   body: JSON.stringify(body) }),
  put:    (ep, body) => apiFetch(ep, { method: "PUT",    body: JSON.stringify(body) }),
  patch:  (ep, body) => apiFetch(ep, { method: "PATCH",  body: JSON.stringify(body) }),
  delete: (ep)       => apiFetch(ep, { method: "DELETE" }),
};

// ── Auth (/register, /login, /me) ───────────────────────────
// /login uses OAuth2PasswordRequestForm (form-data, username field = email)
const AuthAPI = {
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);
    return apiFetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });
  },
  register: (name, email, password, role) => API.post("/register", { name, email, password, role }),
  me:       ()                            => API.get("/me"),
};

// ── Public (/auctions, /categories) ──────────────────────────
const PublicAPI = {
  getAuctions:  (params = {}) => { const qs = new URLSearchParams(params).toString(); return API.get(`/auctions${qs ? "?" + qs : ""}`); },
  getAuction:   (id)          => API.get(`/auctions/${id}`),
  getCategories:()            => API.get("/categories"),
  getEndingSoon:()            => API.get("/auctions/ending-soon"),
};

// ── Bidding (/auctions/{id}/bid, proxy-bid, buy-now) ─────────
const BiddingAPI = {
  placeBid:      (auctionId, amount)    => API.post(`/auctions/${auctionId}/bid`,       { amount }),
  setProxyBid:   (auctionId, maxAmount) => API.post(`/auctions/${auctionId}/proxy-bid`, { max_amount: maxAmount }),
  buyItNow:      (auctionId)            => API.post(`/auctions/${auctionId}/buy-now`,   {}),
  getBidHistory: (auctionId)            => API.get(`/auctions/${auctionId}/bids`),
};

// ── Watchlist (/watchlist) ────────────────────────────────────
const WatchlistAPI = {
  getWatchlist:          ()                   => API.get("/watchlist"),
  addToWatchlist:        (auctionId)          => API.post("/watchlist", { auction_id: auctionId }),
  removeFromWatchlist:   (watchlistId)        => API.delete(`/watchlist/${watchlistId}`),
  removeFromWatchlistByAuction: (auctionId)   => API.delete(`/watchlist/auction/${auctionId}`),
};

// ── Bidder (/bidder/my-bids, won-auctions, pay, invoice) ─────
const BidderAPI = {
  getMyBids:     () => API.get("/bidder/my-bids"),
  getWonAuctions:() => API.get("/bidder/won-auctions"),
  getWonAuction: (id)=> API.get(`/bidder/won-auctions/${id}`),
  makePayment:   (wonAuctionId, deliveryAddress) =>
    API.post(`/bidder/won-auctions/${wonAuctionId}/pay`, { delivery_address: deliveryAddress }),
  getInvoice:    (wonAuctionId) => API.get(`/bidder/won-auctions/${wonAuctionId}/invoice`),

  // Watchlist helpers
  getWatchlist:                 ()          => WatchlistAPI.getWatchlist(),
  addToWatchlist:               (auctionId) => WatchlistAPI.addToWatchlist(auctionId),
  removeFromWatchlist:          (auctionId) => WatchlistAPI.removeFromWatchlistByAuction(auctionId),
};

// ── Seller (/seller/auctions) ─────────────────────────────────
const SellerAPI = {
  createAuction:  (data)                 => API.post("/seller/auctions",           data),
  getMyAuctions:  ()                     => API.get("/seller/auctions"),
  updateAuction:  (auctionId, data)      => API.put(`/seller/auctions/${auctionId}`, data),
  getAuctionBids: (auctionId)            => BiddingAPI.getBidHistory(auctionId),
};

// ── Admin (/admin/*) ──────────────────────────────────────────
const AdminAPI = {
  getStats:          ()                  => API.get("/admin/stats"),
  getPendingAuctions:()                  => API.get("/admin/auctions?status=pending"),
  approveAuction:    (id)                => API.put(`/admin/auctions/${id}/approve`, {}),
  rejectAuction:     (id, reason)        => API.put(`/admin/auctions/${id}/reject`,  { reason }),
  getUsers:          ()                  => API.get("/admin/users"),
  toggleUser:        (id, isActive)      => API.put(`/admin/users/${id}/status`,     { is_active: isActive }),
  getCategories:     ()                  => API.get("/admin/categories"),
  createCategory:    (name, description) => API.post("/admin/categories",            { name, description }),
  deleteCategory:    (id)                => API.delete(`/admin/categories/${id}`),
};
