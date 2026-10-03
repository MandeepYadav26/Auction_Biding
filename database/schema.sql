-- ============================================================
-- Auction Bidding Platform — SQL Schema Reference
-- Phase 2: Database Tables
-- ============================================================
-- NOTE: Tables are created automatically by SQLAlchemy (init_db.py)
-- This file is for reference/documentation only.

CREATE DATABASE IF NOT EXISTS auction_platform
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE auction_platform;

-- --------------------------------------------------------
-- 1. USERS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id         INT          NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL,
    password   VARCHAR(255) NOT NULL,        -- bcrypt hashed
    role       ENUM('admin','seller','bidder') NOT NULL,
    is_active  BOOLEAN      DEFAULT TRUE,
    created_at DATETIME     DEFAULT (NOW()),
    PRIMARY KEY (id),
    UNIQUE  KEY ix_users_email (email),
    INDEX   ix_users_id (id)
);

-- --------------------------------------------------------
-- 2. CATEGORIES
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id          INT          NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  DATETIME     DEFAULT (NOW()),
    PRIMARY KEY (id),
    UNIQUE  KEY uq_categories_name (name),
    INDEX   ix_categories_id (id)
);

-- --------------------------------------------------------
-- 3. AUCTIONS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS auctions (
    id                INT             NOT NULL AUTO_INCREMENT,
    seller_id         INT             NOT NULL,
    category_id       INT             NOT NULL,
    title             VARCHAR(200)    NOT NULL,
    description       TEXT,
    `condition`       ENUM('new','like_new','good','fair','poor') NOT NULL,
    image             VARCHAR(500),
    starting_bid      NUMERIC(12, 2)  NOT NULL,
    current_bid       NUMERIC(12, 2),
    minimum_increment NUMERIC(12, 2)  NOT NULL DEFAULT 50.00,
    reserve_price     NUMERIC(12, 2),
    buy_it_now_price  NUMERIC(12, 2),
    start_time        DATETIME        NOT NULL,
    end_time          DATETIME        NOT NULL,
    status            ENUM('draft','pending','active','ended','sold','cancelled') NOT NULL DEFAULT 'draft',
    winner_id         INT,
    total_bids        INT             DEFAULT 0,
    created_at        DATETIME        DEFAULT (NOW()),
    updated_at        DATETIME        ON UPDATE NOW(),
    PRIMARY KEY (id),
    INDEX  ix_auctions_id (id),
    FOREIGN KEY (seller_id)   REFERENCES users (id),
    FOREIGN KEY (category_id) REFERENCES categories (id),
    FOREIGN KEY (winner_id)   REFERENCES users (id)
);

-- --------------------------------------------------------
-- 4. BIDS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS bids (
    id         INT            NOT NULL AUTO_INCREMENT,
    auction_id INT            NOT NULL,
    bidder_id  INT            NOT NULL,
    amount     NUMERIC(12, 2) NOT NULL,
    bid_type   ENUM('manual','proxy') NOT NULL DEFAULT 'manual',
    created_at DATETIME       DEFAULT (NOW()),
    PRIMARY KEY (id),
    INDEX  ix_bids_id (id),
    FOREIGN KEY (auction_id) REFERENCES auctions (id),
    FOREIGN KEY (bidder_id)  REFERENCES users (id)
);

-- --------------------------------------------------------
-- 5. PROXY BIDS (hidden maximum amounts)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS proxy_bids (
    id         INT            NOT NULL AUTO_INCREMENT,
    auction_id INT            NOT NULL,
    bidder_id  INT            NOT NULL,
    max_amount NUMERIC(12, 2) NOT NULL,
    is_active  BOOLEAN        DEFAULT TRUE,
    created_at DATETIME       DEFAULT (NOW()),
    updated_at DATETIME       ON UPDATE NOW(),
    PRIMARY KEY (id),
    INDEX  ix_proxy_bids_id (id),
    FOREIGN KEY (auction_id) REFERENCES auctions (id),
    FOREIGN KEY (bidder_id)  REFERENCES users (id)
);

-- --------------------------------------------------------
-- 6. WATCHLIST
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlist (
    id         INT      NOT NULL AUTO_INCREMENT,
    auction_id INT      NOT NULL,
    bidder_id  INT      NOT NULL,
    created_at DATETIME DEFAULT (NOW()),
    PRIMARY KEY (id),
    UNIQUE KEY uq_watchlist_auction_bidder (auction_id, bidder_id),
    INDEX  ix_watchlist_id (id),
    FOREIGN KEY (auction_id) REFERENCES auctions (id),
    FOREIGN KEY (bidder_id)  REFERENCES users (id)
);

-- --------------------------------------------------------
-- 7. WON AUCTIONS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS won_auctions (
    id               INT            NOT NULL AUTO_INCREMENT,
    auction_id       INT            NOT NULL,
    bidder_id        INT            NOT NULL,
    winning_amount   NUMERIC(12, 2) NOT NULL,
    payment_status   ENUM('pending','paid') DEFAULT 'pending',
    delivery_address VARCHAR(500),
    created_at       DATETIME       DEFAULT (NOW()),
    paid_at          DATETIME,
    PRIMARY KEY (id),
    UNIQUE KEY uq_won_auctions_auction (auction_id),
    INDEX  ix_won_auctions_id (id),
    FOREIGN KEY (auction_id) REFERENCES auctions (id),
    FOREIGN KEY (bidder_id)  REFERENCES users (id)
);

-- --------------------------------------------------------
-- 8. INVOICES
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    id             INT            NOT NULL AUTO_INCREMENT,
    won_auction_id INT            NOT NULL,
    invoice_number VARCHAR(50)    NOT NULL,
    amount         NUMERIC(12, 2) NOT NULL,
    created_at     DATETIME       DEFAULT (NOW()),
    PRIMARY KEY (id),
    UNIQUE KEY uq_invoices_won_auction (won_auction_id),
    UNIQUE KEY uq_invoices_number (invoice_number),
    INDEX  ix_invoices_id (id),
    FOREIGN KEY (won_auction_id) REFERENCES won_auctions (id)
);
