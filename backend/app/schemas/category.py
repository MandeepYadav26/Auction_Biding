"""
Pydantic schemas for Category
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CategoryCreate(BaseModel):
    """Admin creates a category"""
    name:        str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    is_active:   Optional[bool] = None


class CategoryResponse(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    is_active:   bool
    created_at:  datetime

    class Config:
        from_attributes = True
