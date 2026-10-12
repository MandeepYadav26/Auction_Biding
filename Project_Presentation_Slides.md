# PROJECT PRESENTATION SLIDE DECK (TEXT & WORD FORMAT)

## REAL-TIME CONCURRENT AUCTION & BIDDING PLATFORM
**Project Code:** CS-PRJ-2026-29  
**Full-Stack Architecture:** PostgreSQL / SQLite → FastAPI (Python) → HTML5 / JS / WebSockets  

---

```
================================================================================
                                SLIDE 1: TITLE SLIDE
================================================================================
```

### 🏢 Real-Time Concurrent Auction & Bidding Platform
**Subtitle:** A Scalable, High-Concurrency Marketplace for Competitive Auctions  

* **Presenter / Student Name:** [Your Name]  
* **Roll Number:** [Your Roll Number]  
* **Branch / Department:** Computer Science & Engineering  
* **Institution:** [Your College / University Name]  
* **Guide:** [Guide / Supervisor Name]  

> **Speaker Notes:**  
> "Good morning respected guide and evaluators. Today I am presenting my project — a Real-Time Concurrent Auction & Bidding Platform built with Python FastAPI, PostgreSQL, and WebSockets. This system addresses fundamental engineering challenges in time-sensitive, high-concurrency online bidding."

---

```
================================================================================
                        SLIDE 2: EXECUTIVE SUMMARY & TAGLINE
================================================================================
```

### 📌 Project Tagline
> *"List items for auction, place competitive bids, watch the clock, win and pay — a complete real-time auction marketplace."*

### 🚀 Key Highlights
* **Time-Limited Competitive Bidding:** Ascending price auctions modeled after eBay & government e-procurement portals.
* **Concurrency Engine:** Eliminates race conditions via `SELECT FOR UPDATE` atomic database locks.
* **Automated Proxy Bidding:** System auto-bids on behalf of users up to their secret maximum limits.
* **Anti-Sniping Protection:** Dynamic end-time extension when bids arrive in final minutes.
* **Automated Settlement:** Invoicing, 18% GST calculation, and seller payout management.

> **Speaker Notes:**  
> "Auctions differ fundamentally from regular e-commerce. In standard shopping carts, stock is deducted. In auctions, multiple buyers compete over the exact same item in real-time, requiring zero stale prices and exact state synchronization."

---

```
================================================================================
                      SLIDE 3: PROBLEM STATEMENT & MOTIVATION
================================================================================
```

### ⚠️ The Problem with Traditional Web Applications
1. **Lost Update Anomaly / Race Conditions:**  
   When two bidders click 'Place Bid' simultaneously, naive `UPDATE` queries overwrite each other, causing invalid bid amounts and corrupted logs.
2. **Auction Sniping:**  
   Automated bots place bids in the last 0.5 seconds, depriving human bidders of a fair chance to respond.
3. **Stale Price Displays:**  
   Polling-based HTTP requests fail to update prices instantly, causing users to submit bids against outdated numbers.

### 💡 Motivation & Solution
* Build an **atomic concurrency validation pipeline** using row-level locking.
* Implement **dynamic clock extension** (Anti-sniping).
* Broadcast instant bid updates via **WebSockets**.

---

```
================================================================================
                        SLIDE 4: SYSTEM ARCHITECTURE
================================================================================
```

### 🏗️ High-Level System Architecture

```
+-------------------------------------------------------------------+
|                           CLIENT LAYER                            |
|    Admin Portal    |    Seller Dashboard    |    Bidder UI        |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        FASTAPI API GATEWAY                        |
|   - OAuth2 / JWT Auth     - Pydantic Schemas     - REST Endpoints  |
+-------------------------------------------------------------------+
          |                                            |
          v                                            v
+-----------------------+                    +----------------------+
| BUSINESS LOGIC ENGINE |                    |  WEBSOCKET BROADCAST |
| - SELECT FOR UPDATE   |                    |  - Live Bid Stream   |
| - Proxy Auto-Bids     |                    |  - Clock Extension   |
| - Auto-Extension      |                    +----------------------+
+-----------------------+                              ^
          |                                            |
          +-------------------+------------------------+
                              v
+-------------------------------------------------------------------+
|                       DATABASE LAYER (Postgres)                   |
|  - auctions   - bids (immutable log)   - proxy_bids (secret)     |
+-------------------------------------------------------------------+
```

---

```
================================================================================
                      SLIDE 5: USER ROLES & CAPABILITIES
================================================================================
```

### 👥 Role-Based Access Control & Capabilities

* **Platform Admin Role:**
  * Listing Approval: Review, approve, or reject new auction listings before they go live.
  * Commission Settings: Configure platform fee percentages per category (e.g., Electronics 8%, Antiques 12%).
  * System Analytics: View Gross Merchandise Value (GMV), total auctions ended, sell-through rate, and average bids.

* **Seller Role:**
  * Create Listing: Define title, description, starting bid, secret reserve price, Buy-It-Now price, and duration.
  * Manage Auctions: Monitor live bidding and current leading bid. (Editing is locked once bids arrive).
  * Fulfilment: Enter shipment tracking numbers once winning bidder completes payment.

* **Bidder Role:**
  * Browse & Search: Filter auctions by category, price range, condition, and ending-soon status.
  * Atomic Bid Placement: Place manual bids with real-time minimum increment verification.
  * Proxy Bidding: Set secret maximum budget; system automatically counter-bids when outbid.
  * Payment & Invoicing: Pay for won auctions, provide shipping address, and download tax invoices.

---

```
================================================================================
               SLIDE 6: CORE FEATURE 1 — CONCURRENCY & ATOMIC BIDS
================================================================================
```

### 🔒 Atomic Bid Placement via `SELECT FOR UPDATE`

```
  Bidder A ($150)           FastAPI API            Database (Auction Row)
        |                        |                            |
        |--- POST /bid ($150) -->|                            |
        |                        |--- BEGIN TRANSACTION ----->|
        |                        |--- SELECT ... FOR UPDATE ->| [LOCK ACQUIRED]
        |                        |                            |
  Bidder B ($150)                |                            |
        |--- POST /bid ($150) -->|                            | (Waits for Lock)
        |                        |                            |
        |                        |<-- Row Data Returned ------|
        |                        |--- Validate $150 >= $150 --| (Passed)
        |                        |--- INSERT Into bids -------|
        |                        |--- UPDATE current_bid=$150-|
        |                        |--- COMMIT TRANSACTION ---->| [LOCK RELEASED]
        |                        |                            |
        |                        |<-- Lock Acquired (B) ------|
        |                        |--- Validate $150 >= $200 --| (REJECTED: Min $200)
```

* **Key Engineering Rule:** The `bids` table is an **append-only immutable log**. Bid records are never modified or deleted.

---

```
================================================================================
               SLIDE 7: CORE FEATURE 2 — SECRET PROXY BIDDING
================================================================================
```

### 🤖 Secret Proxy Auto-Bidding Mechanics

* **Concept:** A bidder inputs their *secret maximum budget* (e.g., $5,000).
* **Privacy:** The `max_amount` is strictly secret and **never returned in any public API response**.
* **Auto-Advancement Step-by-Step:**
  1. Bidder A sets Proxy Max = **$5,000** (Current displayed price remains $1,000).
  2. Bidder B places a manual bid of **$2,000**.
  3. System automatically evaluates Proxy A and places a counter-bid of **$2,100** ($2,000 + $100 minimum increment) on behalf of Bidder A.
  4. Bidder B receives instant notification: *"You were outbid by proxy."*

---

```
================================================================================
            SLIDE 8: CORE FEATURE 3 — ANTI-SNIPING AUTO-EXTENSION
================================================================================
```

### ⏱️ Dynamic End-Time Extensions

```
Normal Auction End: 05:00 PM
Extension Window: 5 Minutes | Extension Duration: 10 Minutes

   04:50 PM                  04:57 PM (Bid Arrives!)                 05:07 PM
------+-------------------------+----------------------------------------+------>
   Active Bidding       [BID PLACED IN WINDOW]                    New Auction End
                        Auto-Extension Triggered!                 (Extended +10m)
```

* Eliminates last-second sniper bot advantages.
* Ensures human participants have adequate time to respond.
* Logged in audit table `auction_extensions`.

---

```
================================================================================
             SLIDE 9: CORE FEATURE 4 — SETTLEMENT & INVOICING
================================================================================
```

### 🧾 Auction Closure & Legal Invoicing Workflow

1. **Background Closing Worker:** Evaluates expired auctions every 5 seconds.
2. **Reserve Price Check:**  
   * If `highest_bid >= reserve_price` → Status set to `sold`.  
   * If `highest_bid < reserve_price` → Status set to `reserve_not_met` (No sale).
3. **Financial Invoice Breakdown:**
   * Winning Bid Amount: $10,000.00
   * Platform Commission (8%): $800.00
   * GST on Platform Fee (18%): $144.00
   * Total Invoice Amount Payable: $10,144.00
   * Net Seller Payout ($10,000 - $800): $9,200.00

---

```
================================================================================
                 SLIDE 10: DATABASE SCHEMA & ENTITY MODEL
================================================================================
```

### 📊 Relational Database Architecture (PostgreSQL)

```
+---------------+       1:N       +-------------------+       1:N       +---------------+
|     USERS     |--------------->|     AUCTIONS      |--------------->|     BIDS      |
+---------------+                 +-------------------+                 +---------------+
| id (PK)       |                 | id (PK)           |                 | id (PK)       |
| email         |                 | title             |                 | auction_id(FK)|
| role          |                 | current_bid       |                 | bidder_id (FK)|
+---------------+                 | reserve_price(SEC)|                 | amount        |
                                  | status            |                 | bid_type      |
                                  +-------------------+                 +---------------+
                                            |
                                  1:1       v
                                  +-------------------+       1:1       +---------------+
                                  |   WON_AUCTIONS    |--------------->|   INVOICES    |
                                  +-------------------+                 +---------------+
```

* **Core Entities:**
  * `auctions`: Header record with denormalized `current_bid` and `bid_count`.
  * `bids`: Append-only immutable log of every bid placed.
  * `proxy_bids`: Secret proxy max limits per bidder.
  * `won_auctions` & `invoices`: Settled order details and tax invoice records.

---

```
================================================================================
                     SLIDE 11: DEMO SCENARIO & SCREENSHOTS
================================================================================
```

### 💻 Step-by-Step Live Demonstration Flow

1. **Seller Workflow:**  
   Log in as Seller → Create Listing (Starting: $500, Reserve: $1,200, End: 10 mins).
2. **Admin Approval:**  
   Log in as Admin → Approve listing in Queue → Status becomes `active`.
3. **Bidder 1 (Proxy Setup):**  
   Set Proxy Max = $2,500. Current price displayed = $500.
4. **Bidder 2 (Manual Bid):**  
   Places manual bid of $1,000. System instantly places Proxy auto-bid of $1,100 for Bidder 1.
5. **Auction Close & Payment:**  
   Clock reaches end time → Auction closes as `sold` → Bidder 1 receives invoice & submits payment.

---

```
================================================================================
                    SLIDE 12: CONCLUSION & FUTURE SCOPE
================================================================================
```

### 🎯 Key Project Achievements
* **100% Atomic Bid Handling:** Zero lost updates or price inconsistencies under concurrency.
* **Full-Stack Implementation:** Complete RESTful API, WebSocket integration, and responsive UI.
* **Production Engineering Features:** Proxy auto-bidding, dynamic extensions, and automated GST invoicing.

### 🔮 Future Roadmap
1. Integration with Live Payment Gateways (Stripe / Razorpay).
2. Support for Dutch (Descending Price) Auction Formats.
3. Mobile Native App development using React Native.

---

```
================================================================================
                        SLIDE 13: THANK YOU & Q/A
================================================================================
```

### ❓ Questions & Answers

Thank you for your time and attention!  

**Project Artifacts Available:**
* 📄 Full Academic Synopsis (`Project_Synopsis.md`)
* 💻 Backend & Frontend Source Code
* 📜 OpenAPI / Swagger Interactive Documentation
