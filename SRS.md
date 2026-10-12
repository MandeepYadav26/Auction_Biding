# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)

## Auction Bidding Platform
**Project Type:** University Semester Project
**Technology:** Python, FastAPI, MySQL, HTML, CSS, JavaScript
**Document Version:** 2.0

---

### Document Details
* **Project Title:** Auction Bidding Platform
* **Author / Student:** [Your Name]
* **Roll Number:** [Your Roll Number]
* **Department:** Department of Computer Science & Engineering
* **Institution:** [Your College / University Name]
* **Guide / Supervisor:** [Supervisor Name]

---

## 1. Introduction

### 1.1 Purpose

The purpose of the Auction Bidding Platform is to develop a web-based system where sellers can create auctions for their products and bidders can participate by placing bids.

The system will allow users to register, login, browse auctions, place bids, use proxy bidding, watch auctions and view their bidding history.

The project is designed as a university-level full-stack application and focuses on understanding database management, backend APIs, authentication and basic auction logic.

### 1.2 Project Scope

The system will provide three main types of users:
* **Admin** — Manages the platform, approves listings, manages categories.
* **Seller** — Creates and manages auction listings.
* **Bidder** — Browses products, places bids, wins auctions.

The system will use MySQL as the relational database, FastAPI as the backend framework, and HTML/CSS/JavaScript for the frontend.

### 1.3 References
* InterviewCafe Project Specification Guide (Project #29: Auction Platform)
* FastAPI Official Documentation: https://fastapi.tiangolo.com/
* MySQL Documentation: https://dev.mysql.com/doc/
* SQLAlchemy Documentation: https://docs.sqlalchemy.org/

---

## 2. User Roles

### 2.1 Admin

The Admin manages the platform.

Admin can:
* Login to the admin panel
* View all users (sellers and bidders)
* Manage categories (add, edit, delete)
* Approve or reject auction listings
* View all auctions and their details
* View basic platform statistics (total users, total auctions, active auctions, ended auctions)

### 2.2 Seller

The Seller is the person who wants to sell an item through an auction.

Seller can:
* Register and login
* Create an auction listing with product details
* Add product image
* Set starting bid and minimum bid increment
* Set auction start time and end time
* Set optional reserve price (hidden from bidders)
* Set optional Buy-It-Now price
* View own auctions and bids received
* View auction results (sold / unsold)

### 2.3 Bidder

The Bidder is the user who participates in auctions.

Bidder can:
* Register and login
* Browse available auctions
* Search auctions by keyword or category
* View auction details and current highest bid
* Place a manual bid
* Set a proxy/maximum bid (secret auto-bidding)
* Use Buy-It-Now to purchase instantly
* Add auctions to watchlist
* View own bids with status (Winning / Outbid / Won / Lost)
* View won auctions
* Make simulated payment and view invoice

---

## 3. Functional Requirements

### 3.1 User Registration

The system shall allow new users to create an account.

Required information:
* Name
* Email
* Password
* Role (Seller or Bidder)

Passwords shall be hashed using bcrypt before storing. Plain text passwords shall never be stored.

### 3.2 Login

Users shall be able to login using their email and password.

After login, the user will receive a JWT authentication token and be redirected according to their role:
* Admin → Admin Dashboard
* Seller → Seller Dashboard
* Bidder → Home / Auction Browse Page

---

## 4. Auction Management

### 4.1 Create Auction

A Seller shall be able to create an auction with the following fields:
* Product title
* Description
* Category
* Condition (New / Used / Refurbished)
* Product image
* Starting bid amount
* Minimum bid increment
* Optional reserve price (hidden from bidders)
* Optional Buy-It-Now price
* Start time
* End time

### 4.2 Auction Status

An auction can have the following statuses:
* **Draft** — Created but not yet submitted.
* **Pending** — Submitted for admin approval.
* **Active** — Approved and open for bidding.
* **Ended** — End time reached, no bids or reserve not met.
* **Sold** — Auction completed with a winner.
* **Cancelled** — Cancelled by admin or seller.

### 4.3 Admin Approval

When a seller submits an auction listing, it enters `Pending` status. An Admin reviews and either approves (status becomes `Active`) or rejects the listing.

---

## 5. Bidding

### 5.1 Manual Bidding

A bidder can enter a bid amount.

The bid must satisfy:
* `New Bid >= Current Bid + Minimum Increment`

Example:
* Current Bid = ₹1000, Minimum Increment = ₹50
* Minimum next bid = ₹1050
* If user enters ₹1020, the system rejects the bid.

Bids are never deleted or modified — the `bids` table serves as an append-only log.

### 5.2 Current Highest Bid

The auction record shall maintain:
* Current highest bid amount
* Current highest bidder identity
* Total number of bids placed

### 5.3 Bid Validation Rules
* Bid amount must be >= current_bid + minimum_increment.
* A seller cannot bid on their own auction.
* Bids cannot be placed on ended or cancelled auctions.
* Bids cannot be placed before auction start time.

---

## 6. Proxy Bidding

The bidder can specify a maximum amount they are willing to pay.

Example:
* Current bid = ₹1000, Minimum increment = ₹100
* Bidder A sets maximum = ₹2000
* Bidder B places ₹1100
* System automatically bids ₹1200 on behalf of Bidder A
* This continues until Bidder A's maximum (₹2000) is exceeded

Rules:
* The maximum amount of a proxy bid shall remain hidden from all other users.
* Each bidder can have only one proxy bid per auction (UNIQUE constraint on auction_id + bidder_id).
* Proxy bids are stored in the `proxy_bids` table.

---

## 7. Buy It Now

If an auction has a Buy-It-Now price, a bidder may purchase the item instantly.

When Buy-It-Now is used:
* The auction ends immediately.
* The bidder becomes the winner.
* A `won_auctions` record is created with the BIN price as the winning amount.

---

## 8. Watchlist

A bidder can add auctions to their watchlist for easy tracking.

The watchlist view shall display:
* Auction title
* Current bid
* Time remaining
* Auction status

---

## 9. Auction Ending

When the auction reaches its end time:
* Bidding stops — no new bids are accepted.
* The highest bidder is identified.
* If a reserve price is set and the highest bid is below it → status = `ended` (reserve not met, no sale).
* If the highest bid meets or exceeds the reserve (or no reserve is set) → status = `sold`.
* If no bids were placed → status = `ended`.
* A `won_auctions` record is created for the winner.

Auction ending will be handled by a background task/checker in the backend.

---

## 10. Winner and Payment

After winning an auction, the bidder can:
* View the winning auction details
* Enter delivery address
* Make a simulated payment (status changes from `Pending` to `Paid`)
* View and download an invoice

Actual online payment integration is outside the scope of this university project. Payment is simulated.

Invoice contains:
* Invoice number
* Auction title / Product name
* Winner name
* Winning amount
* Date of issue

---

## 11. Admin Module

Admin dashboard shall display:
* Total users
* Total sellers
* Total bidders
* Total auctions
* Active auctions count
* Ended auctions count

Admin can also:
* Add, edit, and delete categories
* Approve auction listings
* Reject auction listings with a reason
* View auction details

---

## 12. Database Requirements

MySQL shall be used as the database engine.

### Main Entities and Fields

**users**
* id, name, email, password (hashed), role, created_at

**categories**
* id, name

**auctions**
* id, seller_id (FK → users), category_id (FK → categories), title, description, condition, image, starting_bid, current_bid, minimum_increment, reserve_price, buy_it_now_price, start_time, end_time, status, created_at

**bids** (append-only log)
* id, auction_id (FK → auctions), bidder_id (FK → users), amount, bid_type (manual / proxy_auto), created_at

**proxy_bids**
* id, auction_id (FK → auctions), bidder_id (FK → users), max_amount (secret), created_at
* UNIQUE constraint on (auction_id, bidder_id)

**watchlist**
* id, auction_id (FK → auctions), bidder_id (FK → users), created_at

**won_auctions**
* id, auction_id (FK → auctions), bidder_id (FK → users), winning_amount, payment_status (pending / paid), delivery_address, created_at

**invoices**
* id, won_auction_id (FK → won_auctions), invoice_number, amount, created_at

---

## 13. API Requirements

The FastAPI backend shall provide the following API endpoints:

### Authentication
* `POST /register` — Register a new user.
* `POST /login` — Authenticate user and return JWT token.

### Auctions
* `GET /auctions` — Browse all active auctions (with search and category filters).
* `GET /auctions/{id}` — Get auction details.
* `POST /auctions` — Create a new auction (Seller only).
* `PUT /auctions/{id}` — Update an auction (Seller only, if not yet active).
* `DELETE /auctions/{id}` — Delete a draft auction.

### Bidding
* `POST /auctions/{id}/bid` — Place a manual bid.
* `GET /auctions/{id}/bids` — Get bid history for an auction.
* `POST /auctions/{id}/proxy-bid` — Set or update proxy bid.

### Buy It Now
* `POST /auctions/{id}/buy-now` — Purchase instantly at BIN price.

### Watchlist
* `POST /watchlist` — Add auction to watchlist.
* `GET /watchlist` — View watchlist.
* `DELETE /watchlist/{id}` — Remove from watchlist.

### Bidder Dashboard
* `GET /bidder/my-bids` — View all bids with status.
* `GET /bidder/won-auctions` — View won auctions.

### Seller Dashboard
* `GET /seller/auctions` — View own auctions.

### Admin
* `GET /admin/auctions` — View all auctions.
* `PUT /admin/auctions/{id}/approve` — Approve listing.
* `PUT /admin/auctions/{id}/reject` — Reject listing.
* `GET /admin/stats` — Platform statistics.

### Payment
* `POST /won-auctions/{id}/pay` — Simulate payment.
* `GET /invoices/{id}` — View/download invoice.

---

## 14. Frontend Requirements

The application shall contain the following pages:

### Public / User Pages
* Home page with featured auctions
* Login page
* Register page
* Auction listing page (browse all active auctions)
* Auction details page (with bid form, proxy bid, Buy It Now, watchlist button, bid history, countdown timer)

### Bidder Pages
* My Bids dashboard (with Winning / Outbid status badges)
* Watchlist page
* Won Auctions page
* Payment page

### Seller Pages
* Seller Dashboard
* Create Auction form
* My Auctions list

### Admin Pages
* Admin Dashboard with statistics
* Manage Users
* Manage Categories
* Auction Approval queue

---

## 15. Non-Functional Requirements

### Performance
* The application shall respond reasonably quickly for normal university-project usage.

### Security
* Passwords shall be hashed using bcrypt.
* Login shall use JWT authentication tokens.
* Users shall only access features allowed for their role.
* Proxy bid `max_amount` shall never be exposed in public API responses.

### Reliability
* A bid shall not be accepted if it is lower than the required minimum.
* The system shall correctly determine the auction winner when the auction ends.

### Usability
* The interface shall be simple, clean, and easy to understand.

---

## 16. Project Limitations

This project is developed as a university semester project. The following advanced features are not included:
* Microservices architecture
* Kubernetes / Docker deployment
* Cloud infrastructure
* Real payment gateway integration
* Advanced recommendation / AI system
* Large-scale distributed database
* Complex analytics dashboards
* Mobile application
* Advanced notification infrastructure

Real-time WebSocket updates may be added later if sufficient development time is available.

---

## 17. Expected Outcome

The completed system shall demonstrate the following end-to-end flow:

```
Seller registers and creates auction
          ↓
Admin approves the listing
          ↓
Auction goes live (Active)
          ↓
Bidders browse and place bids
          ↓
Other bidders compete (manual + proxy bidding)
          ↓
Auction reaches end time
          ↓
Highest bidder wins
          ↓
Winner makes simulated payment
          ↓
Invoice is generated
```

The project will demonstrate practical understanding of: Full-stack development, Python, FastAPI, MySQL, REST APIs, JWT Authentication, Database relationships, Auction bidding logic, Basic concurrent bid handling, and Frontend-backend integration.
