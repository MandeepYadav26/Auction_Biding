"""
Auction Bidding Platform - Main Entry Point
Phase 1: Project Setup
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Auction Bidding Platform",
    description="University Semester Project - Auction Platform with FastAPI + MySQL",
    version="1.0.0"
)

# Allow frontend (HTML/JS) to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Welcome to Auction Bidding Platform 🎯",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "OK"}


# Run with: uvicorn main:app --reload
