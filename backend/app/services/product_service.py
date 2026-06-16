from sqlalchemy.orm import Session

from app.models.product import Product


def get_all_products(db: Session, category_id: int | None = None) -> list[Product]:
    q = db.query(Product)
    if category_id is not None:
        q = q.filter(Product.category_id == category_id)
    return q.order_by(Product.nombre).all()


def get_product(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, **kwargs) -> Product:
    product = Product(**kwargs)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: dict) -> Product | None:
    product = get_product(db, product_id)
    if product is None:
        return None
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    product = get_product(db, product_id)
    if product is None:
        return False
    db.delete(product)
    db.commit()
    return True
