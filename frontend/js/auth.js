// ============================================================
// auth.js — Authentication helpers for Auction Bidding Platform
// Login, logout, role guard, token management
// ============================================================

// ── Token helpers ─────────────────────────────────────────────

function saveToken(token) {
  localStorage.setItem("token", token);
}

function getToken() {
  return localStorage.getItem("token");
}

function removeToken() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

function saveUser(user) {
  localStorage.setItem("user", JSON.stringify(user));
}

function getUser() {
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
}

function isLoggedIn() {
  return !!getToken();
}

function getUserRole() {
  const user = getUser();
  return user ? user.role : null;
}

// ── Login ─────────────────────────────────────────────────────

async function login(email, password) {
  const data = await AuthAPI.login(email, password);
  saveToken(data.access_token);

  // Fetch user profile and save
  const user = await AuthAPI.me();
  saveUser(user);

  return user;
}

// ── Logout ────────────────────────────────────────────────────

function logout() {
  removeToken();
  window.location.href = getBasePath() + "login.html";
}

// ── Role-based redirect after login ──────────────────────────

function redirectByRole(role) {
  const base = getBasePath();
  if (role === "admin") {
    window.location.href = base + "pages/admin-dashboard.html";
  } else if (role === "seller") {
    window.location.href = base + "pages/seller-dashboard.html";
  } else {
    window.location.href = base + "pages/auction-list.html";
  }
}

// ── Route guard — call at top of protected pages ─────────────
// requiredRole: "admin" | "seller" | "bidder" | null (any logged in)

function requireAuth(requiredRole = null) {
  if (!isLoggedIn()) {
    window.location.href = getBasePath() + "login.html";
    return false;
  }

  if (requiredRole) {
    const role = getUserRole();
    if (role !== requiredRole) {
      // Wrong role — send to their own dashboard
      redirectByRole(role);
      return false;
    }
  }
  return true;
}

// ── Base path helper (works from root or /pages/) ─────────────

function getBasePath() {
  // If we're inside /pages/, go up one level
  const path = window.location.pathname;
  if (path.includes("/pages/")) {
    return "../";
  }
  return "";
}

// ── Navbar injection ──────────────────────────────────────────
// Call renderNav() in every page's <body onload> or DOMContentLoaded

function renderNav() {
  const navEl = document.getElementById("main-nav");
  if (!navEl) return;

  const user = getUser();
  const base = getBasePath();

  if (!user) {
    // Guest nav
    navEl.innerHTML = `
      <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
          <a class="navbar-brand fw-bold" href="${base}index.html">🔨 AuctionHub</a>
          <div class="navbar-nav ms-auto">
            <a class="nav-link" href="${base}pages/auction-list.html">Browse</a>
            <a class="nav-link" href="${base}login.html">Login</a>
            <a class="nav-link" href="${base}register.html">Register</a>
          </div>
        </div>
      </nav>`;
    return;
  }

  let roleLinks = "";
  if (user.role === "admin") {
    roleLinks = `
      <a class="nav-link" href="${base}pages/admin-dashboard.html">Dashboard</a>
      <a class="nav-link" href="${base}pages/admin-users.html">Users</a>
      <a class="nav-link" href="${base}pages/admin-categories.html">Categories</a>`;
  } else if (user.role === "seller") {
    roleLinks = `
      <a class="nav-link" href="${base}pages/seller-dashboard.html">Dashboard</a>
      <a class="nav-link" href="${base}pages/create-auction.html">Create Auction</a>`;
  } else {
    roleLinks = `
      <a class="nav-link" href="${base}pages/my-bids.html">My Bids</a>
      <a class="nav-link" href="${base}pages/watchlist.html">Watchlist</a>
      <a class="nav-link" href="${base}pages/won-auctions.html">Won Auctions</a>`;
  }

  navEl.innerHTML = `
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <a class="navbar-brand fw-bold" href="${base}index.html">🔨 AuctionHub</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMenu">
          <div class="navbar-nav me-auto">
            <a class="nav-link" href="${base}pages/auction-list.html">Browse Auctions</a>
            ${roleLinks}
          </div>
          <div class="navbar-nav ms-auto align-items-center">
            <span class="nav-link text-warning">👤 ${user.name} <small class="badge bg-secondary">${user.role}</small></span>
            <a class="nav-link text-danger" href="#" onclick="logout()">Logout</a>
          </div>
        </div>
      </div>
    </nav>`;
}

// ── Toast notification helper ─────────────────────────────────

function showToast(message, type = "info") {
  // type: success | danger | warning | info
  const container = document.getElementById("toast-container");
  if (!container) return;

  const id = "toast-" + Date.now();
  const bg = {
    success: "bg-success",
    danger: "bg-danger",
    warning: "bg-warning text-dark",
    info: "bg-info text-dark",
  }[type] || "bg-secondary";

  container.insertAdjacentHTML("beforeend", `
    <div id="${id}" class="toast align-items-center text-white ${bg} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`);

  const toastEl = document.getElementById(id);
  const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
  bsToast.show();
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

// ── Format helpers ────────────────────────────────────────────

function formatCurrency(amount) {
  return "₹" + Number(amount).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(isoString) {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatCountdown(endTimeIso) {
  const diff = new Date(endTimeIso) - new Date();
  if (diff <= 0) return "⏰ Ended";

  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  const secs = Math.floor((diff % 60000) / 1000);

  if (days > 0) return `${days}d ${hours}h ${mins}m`;
  if (hours > 0) return `${hours}h ${mins}m ${secs}s`;
  return `${mins}m ${secs}s`;
}

function statusBadge(status) {
  const map = {
    pending: "bg-warning text-dark",
    approved: "bg-success",
    active: "bg-success",
    ended: "bg-secondary",
    sold: "bg-primary",
    rejected: "bg-danger",
    cancelled: "bg-danger",
  };
  const cls = map[status] || "bg-secondary";
  return `<span class="badge ${cls}">${status.toUpperCase()}</span>`;
}
