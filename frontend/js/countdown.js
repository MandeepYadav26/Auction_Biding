// ============================================================
// countdown.js — Reusable Countdown Timer Utility
// AuctionHub — Phase 14
// ============================================================

/**
 * CountdownTimer class
 * Usage:
 * const timer = new CountdownTimer(endTimeIso, {
 * onTick: (info) => { ... },
 * onEnd: () => { ... }
 * });
 * timer.start();
 * timer.stop();
 */
class CountdownTimer {
 constructor(endTimeIso, callbacks = {}) {
 this.endTime = new Date(endTimeIso);
 this.onTick = callbacks.onTick || (() => {});
 this.onEnd = callbacks.onEnd || (() => {});
 this._interval = null;
 this._ended = false;
 }

 /** Call once to begin ticking every second */
 start() {
 this._tick();
 this._interval = setInterval(() => this._tick(), 1000);
 return this;
 }

 stop() {
 if (this._interval) clearInterval(this._interval);
 this._interval = null;
 }

 _tick() {
 const now = new Date();
 const diff = this.endTime - now;

 if (diff <= 0) {
 if (!this._ended) {
 this._ended = true;
 this.stop();
 this.onTick(this._buildInfo(0));
 this.onEnd();
 }
 return;
 }

 this.onTick(this._buildInfo(diff));
 }

 _buildInfo(diff) {
 const days = Math.floor(diff / 86400000);
 const hours = Math.floor((diff % 86400000) / 3600000);
 const mins = Math.floor((diff % 3600000) / 60000);
 const secs = Math.floor((diff % 60000) / 1000);

 // Urgency level: "normal" | "warning" | "critical" | "ended"
 let urgency = "ended";
 if (diff > 0) {
 if (diff > 3600000) urgency = "normal"; // > 1 hour
 else if (diff > 600000) urgency = "warning"; // 10 min – 1 hour
 else urgency = "critical"; // < 10 min
 }

 return { diff, days, hours, mins, secs, urgency };
 }
}

// ── Standalone helpers (used by cards, lists) ─────────────────

/**
 * Format countdown info into display string
 */
function formatCountdownInfo(info) {
 if (info.urgency === "ended") return " Ended";
 if (info.days > 0) return `${info.days}d ${info.hours}h ${info.mins}m`;
 if (info.hours > 0) return `${info.hours}h ${info.mins}m ${info.secs}s`;
 return `${info.mins}m ${info.secs}s`;
}

/**
 * Returns Bootstrap CSS class based on urgency
 */
function urgencyClass(urgency) {
 return {
 normal: "text-success",
 warning: "text-warning",
 critical: "text-danger",
 ended: "text-secondary",
 }[urgency] || "text-secondary";
}

/**
 * Attach a live countdown to an element with [data-end] attribute.
 * Automatically updates text + color. Calls onEnd if provided.
 * @param {HTMLElement} el
 * @param {function} [onEnd]
 */
function attachCountdown(el, onEnd) {
 const endIso = el.dataset.end;
 if (!endIso) return;

 const timer = new CountdownTimer(endIso, {
 onTick: (info) => {
 el.textContent = formatCountdownInfo(info);
 el.className = el.className.replace(/text-(success|warning|danger|secondary)/g, "");
 el.classList.add(urgencyClass(info.urgency));
 },
 onEnd: () => { if (typeof onEnd === "function") onEnd(); },
 });
 timer.start();
 return timer;
}

/**
 * Attach countdowns to ALL [data-end] elements in document.
 * Returns array of timer instances.
 */
function attachAllCountdowns(onEndCallback) {
 const timers = [];
 document.querySelectorAll("[data-end]").forEach(el => {
 timers.push(attachCountdown(el, onEndCallback));
 });
 return timers;
}

// ── Big countdown display (used on auction-detail) ────────────

/**
 * Update a 4-block countdown display (days / hours / mins / secs boxes).
 * Expects HTML structure created by renderCountdownBlocks().
 */
function updateCountdownDisplay(containerId, info) {
 const c = document.getElementById(containerId);
 if (!c) return;

 const set = (id, val, label) => {
 const el = c.querySelector(`[data-unit="${id}"]`);
 if (el) {
 el.querySelector(".cd-value").textContent = String(val).padStart(2, "0");
 el.querySelector(".cd-label").textContent = label;
 }
 };

 if (info.urgency === "ended") {
 c.innerHTML = `<div class="cd-ended text-secondary fw-bold fs-5"> Auction Ended</div>`;
 return;
 }

 set("days", info.days, info.days === 1 ? "Day" : "Days");
 set("hours", info.hours, info.hours === 1 ? "Hour" : "Hours");
 set("mins", info.mins, info.mins === 1 ? "Minute" : "Minutes");
 set("secs", info.secs, info.secs === 1 ? "Second" : "Seconds");

 // Color entire block based on urgency
 c.dataset.urgency = info.urgency;
}

/**
 * Render the 4-block countdown HTML into a container element.
 */
function renderCountdownBlocks(containerId) {
 const c = document.getElementById(containerId);
 if (!c) return;
 c.innerHTML = `
 <div class="cd-blocks d-flex gap-2 justify-content-center flex-wrap">
 <div class="cd-block text-center" data-unit="days">
 <div class="cd-value fw-bold fs-2">00</div>
 <div class="cd-label small text-muted">Days</div>
 </div>
 <div class="cd-sep fw-bold fs-2 pt-1">:</div>
 <div class="cd-block text-center" data-unit="hours">
 <div class="cd-value fw-bold fs-2">00</div>
 <div class="cd-label small text-muted">Hours</div>
 </div>
 <div class="cd-sep fw-bold fs-2 pt-1">:</div>
 <div class="cd-block text-center" data-unit="mins">
 <div class="cd-value fw-bold fs-2">00</div>
 <div class="cd-label small text-muted">Minutes</div>
 </div>
 <div class="cd-sep fw-bold fs-2 pt-1">:</div>
 <div class="cd-block text-center" data-unit="secs">
 <div class="cd-value fw-bold fs-2">00</div>
 <div class="cd-label small text-muted">Seconds</div>
 </div>
 </div>`;
}
