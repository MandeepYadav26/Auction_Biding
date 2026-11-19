// ============================================================
// api.js — Shared API utility for Auction Bidding Platform
// Base URL + JWT-authenticated fetch wrapper
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

/**
 * Core fetch wrapper — attaches JWT token if present
 * @param {string} endpoint  — e.g. "/auctions"
 * @param {object} options   — standard fetch options (method, body, etc.)
 * @returns {Promise<any>}   — parsed JSON response
 */
async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle non-200 responses
  if (!response.ok) {
    let errorMsg = `HTTP ${response.status}`;
    try {
      const errData = await response.json();
      errorMsg = errData.detail || JSON.stringify(errData);
    } catch (_) {}
    throw new Error(errorMsg);
  }

  // Return null for No Content
  if (response.status === 204) 
    return null;

  return response.json();
}

// ── Convenience helpers ───────────────────────────────────────

const API = {
  get: (endpoint) => apiFetch(endpoint, { method: "GET" }),

  post: (endpoint, body) =>
    apiFetch(endpoint, { method: "POST", body: JSON.stringify(body) }),

  put: (endpoint, body) =>
    apiFetch(endpoint, { method: "PUT", body: JSON.stringify(body) }),

  patch: (endpoint, body) =>
    apiFetch(endpoint, { method: "PATCH", body: JSON.stringify(body) }),

  delete: (endpoint) => apiFetch(endpoint, { method: "DELETE" }),
};

// ── Auth endpoints ────────────────────────────────────────────
const AuthAPI = {
  login: (email, password) =>
    API.post("/auth/login", { email, password }),

  register: (name, email, password, role) =>
    API.post("/auth/register", { name, email, password, role }),

  me: () => API.get("/auth/me"),
};

// ── Public endpoints ──────────────────────────────────────────
const PublicAPI = {
  getAuctions: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/auctions${qs ? "?" + qs : ""}`);
  },

  getAuction: (id) => API.get(`/auctions/${id}`),

  getCategories: () => API.get("/categories"),

  getEndingSoon: () => API.get("/auctions/ending-soon"),

  search: (q) => API.get(`/auctions?search=${encodeURIComponent(q)}`),
};

// ── Bidding endpoints ─────────────────────────────────────────
const BiddingAPI = {
  placeBid: (auctionId, amount) =>
    API.post(`/bidding/${auctionId}/bid`, { amount }),

  setProxyBid: (auctionId, maxAmount) =>
    API.post(`/bidding/${auctionId}/proxy-bid`, { max_amount: maxAmount }),

  buyItNow: (auctionId) =>
    API.post(`/bidding/${auctionId}/buy-it-now`, {}),

  getBidHistory: (auctionId) =>
    API.get(`/bidding/${auctionId}/bids`),
};

// ── Bidder (self-service) endpoints ──────────────────────────
const BidderAPI = {
  getMyBids: () => API.get("/bidder/my-bids"),

  getWatchlist: () => API.get("/bidder/watchlist"),

  addToWatchlist: (auctionId) =>
    API.post(`/bidder/watchlist/${auctionId}`, {}),

  removeFromWatchlist: (auctionId) =>
    API.delete(`/bidder/watchlist/${auctionId}`),

  getWonAuctions: () => API.get("/bidder/won-auctions"),

  makePayment: (wonAuctionId, deliveryAddress) =>
    API.post(`/bidder/payment/${wonAuctionId}`, {
      delivery_address: deliveryAddress,
    }),

  getInvoice: (invoiceId) => API.get(`/bidder/invoice/${invoiceId}`),
};

// ── Seller endpoints ──────────────────────────────────────────
const SellerAPI = {
  createAuction: (data) => API.post("/seller/auctions", data),

  getMyAuctions: () => API.get("/seller/auctions"),

  getAuctionBids: (auctionId) =>
    API.get(`/seller/auctions/${auctionId}/bids`),

  updateAuction: (auctionId, data) =>
    API.put(`/seller/auctions/${auctionId}`, data),
};

// ── Admin endpoints ───────────────────────────────────────────
const AdminAPI = {
  getStats: () => API.get("/admin/stats"),

  getPendingAuctions: () => API.get("/admin/auctions/pending"),

  approveAuction: (id) => API.post(`/admin/auctions/${id}/approve`, {}),

  rejectAuction: (id, reason) =>
    API.post(`/admin/auctions/${id}/reject`, { reason }),

  getUsers: () => API.get("/admin/users"),

  toggleUser: (id) => API.post(`/admin/users/${id}/toggle`, {}),

  getCategories: () => API.get("/admin/categories"),

  createCategory: (name, description) =>
    API.post("/admin/categories", { name, description }),

  deleteCategory: (id) => API.delete(`/admin/categories/${id}`),
};
