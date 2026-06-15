from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.sale import Sale, SaleItem, PaymentMethod
from app.models.stock_movement import StockMovement, MovementType


def test_create_user(db):
    user = User(username="admin", password_hash="hashed", role=UserRole.admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.id is not None
    assert user.username == "admin"
    assert user.role == UserRole.admin


def test_username_unique(db):
    db.add(User(username="dup_user", password_hash="h1", role=UserRole.cashier))
    db.commit()
    db.add(User(username="dup_user", password_hash="h2", role=UserRole.cashier))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_create_category_and_product(db):
    cat = Category(nombre="Bebidas")
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = Product(
        nombre="Agua 0.5L",
        precio=Decimal("1.20"),
        stock=50,
        stock_minimo=10,
        category_id=cat.id,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    assert prod.id is not None
    assert prod.category.nombre == "Bebidas"


def test_category_unique(db):
    db.add(Category(nombre="UniqueTest"))
    db.commit()
    db.add(Category(nombre="UniqueTest"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_create_sale_with_items(db):
    user = User(username="cajero1", password_hash="h", role=UserRole.cashier)
    cat = Category(nombre="Alimentacion")
    db.add_all([user, cat])
    db.commit()

    prod = Product(
        nombre="Pan",
        precio=Decimal("0.90"),
        stock=100,
        stock_minimo=5,
        category_id=cat.id,
    )
    db.add(prod)
    db.commit()

    sale = Sale(
        total=Decimal("1.80"),
        metodo_pago=PaymentMethod.efectivo,
        user_id=user.id,
    )
    db.add(sale)
    db.commit()

    item = SaleItem(
        sale_id=sale.id,
        product_id=prod.id,
        cantidad=2,
        precio_unitario=Decimal("0.90"),
    )
    db.add(item)
    db.commit()
    db.refresh(sale)

    assert len(sale.items) == 1
    assert sale.items[0].product.nombre == "Pan"
    assert sale.items[0].cantidad == 2


def test_stock_movement(db):
    prod = Product(nombre="Leche", precio=Decimal("1.10"), stock=20, stock_minimo=5)
    db.add(prod)
    db.commit()

    mov = StockMovement(
        product_id=prod.id,
        cantidad=-5,
        tipo=MovementType.salida,
        motivo="Venta test",
    )
    db.add(mov)
    db.commit()
    db.refresh(prod)

    assert len(prod.stock_movements) == 1
    assert prod.stock_movements[0].tipo == MovementType.salida
    assert prod.stock_movements[0].cantidad == -5


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
