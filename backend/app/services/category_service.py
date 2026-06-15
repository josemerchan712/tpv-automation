from sqlalchemy.orm import Session

from app.models.category import Category


def get_all_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.nombre).all()


def get_category(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def create_category(db: Session, nombre: str) -> Category:
    category = Category(nombre=nombre)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, nombre: str) -> Category | None:
    category = get_category(db, category_id)
    if category is None:
        return None
    category.nombre = nombre
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    category = get_category(db, category_id)
    if category is None:
        return False
    if category.products:
        raise ValueError("Category has linked products")
    db.delete(category)
    db.commit()
    return True
