# Auction Bidding Platform

> University Semester Project — Python · FastAPI · MySQL · HTML · CSS · JavaScript

---

## Project Structure

```
Auction Platform/
│
├── backend/                   # FastAPI Backend
│   ├── venv/                  # Python virtual environment (do not commit)
│   ├── main.py                # App entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment variable template
│   ├── .env                   # Your actual env vars (do NOT commit)
│   │
│   └── app/
│       ├── config/
│       │   └── settings.py    # App settings from .env
│       ├── models/            # SQLAlchemy database models
│       ├── routes/            # FastAPI route handlers
│       ├── schemas/           # Pydantic request/response schemas
│       ├── services/          # Business logic
│       └── utils/             # Helper functions
│
├── frontend/                  # Plain HTML/CSS/JS
│   ├── pages/                 # HTML pages
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript files
│   └── images/                # Static images
│
├── database/                  # SQL scripts
│   └── schema.sql             # Table definitions (added in Phase 2)
│
└── README.md
```

---

## Tech Stack

| Layer          | Technology          |
|----------------|---------------------|
| Frontend       | HTML, CSS, JavaScript |
| Backend        | Python, FastAPI     |
| ORM            | SQLAlchemy          |
| Database       | MySQL               |
| Authentication | JWT                 |

---

## Setup Instructions

### 1. Clone / Open Project

```
cd "Auction Platform"
```

### 2. Backend Setup

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and fill in your MySQL password
copy .env.example .env
```

Edit `.env` and set your MySQL password and a strong `SECRET_KEY`.

### 3. Run Backend

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

Visit: http://127.0.0.1:8000

API Docs: http://127.0.0.1:8000/docs

---

## Development Phases

| Phase | Topic                  | Status  |
|-------|------------------------|---------|
| 0     | Planning               |  Done   |
| 1     | Environment Setup      |  Done   |
| 2     | MySQL Database         |  Done   |
| 3     | FastAPI + SQLAlchemy   |  Done   |
| 4     | Auth (JWT)             |  Done   |
| 5     | Seller Module          |  Done   |
| 6     | Admin Module           |  Done   |
| 7     | Normal Bidding         |  Done   |
| 8     | Proxy Bidding          |  Done   |
| 9     | Auction Ending         |  Done   |
| 10    | Buy It Now             |  Done   |
| 11    | Watchlist + My Bids    |  Done   |
| 12    | Winner + Payment       |  Done   |
| 13    | Frontend Polish        |  Done   |
| 14    | AI Description Gen     |  Done   |
| 15    | ML Price Prediction    |  next   |
| 16    | Testing                | pending |

---

## User Roles

- **Admin** — Manages platform, approves auctions, manages categories
- **Seller** — Creates auction listings, views bids and results
- **Bidder** — Browses auctions, places bids, manages watchlist

---

## Core Auction Flow

```
Register / Login
      ↓
Seller creates auction
      ↓
Admin approves
      ↓
Auction goes ACTIVE
      ↓
Bidder places bid
      ↓
Highest bidder wins
      ↓
Simulated Payment
      ↓
Invoice generated
```
