"""
CRUD operations for Category model
"""

from sqlalchemy.orm import Session
from app.models.category   import Category
from app.schemas.category  import CategoryCreate, CategoryUpdate
from typing import Optional, List


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()


def get_all_categories(db: Session, active_only: bool = True) -> List[Category]:
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    return query.order_by(Category.name).all()


def create_category(db: Session, data: CategoryCreate) -> Category:
    cat = Category(name=data.name, description=data.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Optional[Category]:
    cat = get_category_by_id(db, category_id)
    if not cat:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, category_id: int) -> bool:
    cat = get_category_by_id(db, category_id)
    if not cat:
        return False
    cat.is_active = False   # soft delete
    db.commit()
    return True
