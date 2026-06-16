from decimal import Decimal
import pytest
from app.models.product import Product
from app.models.sale import PaymentMethod


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_product(db, nombre="Prod", precio="10.00", stock=50, stock_minimo=5):
    prod = Product(
        nombre=nombre,
        precio=Decimal(precio),
        stock=stock,
        stock_minimo=stock_minimo,
    )
    db.add(prod)
    db.flush()
    return prod


def _make_sale(db, user_id, metodo_pago, items):
    """items: list of (product, cantidad)"""
    from app.services import sale_service
    return sale_service.create_sale(
        db,
        user_id=user_id,
        metodo_pago=metodo_pago,
        items=[{"product_id": p.id, "cantidad": q} for p, q in items],
    )


# ── daily_close ──────────────────────────────────────────────────────────────

def test_daily_close_no_sales_returns_zeros(db):
    from datetime import date
    from app.services.report_service import daily_close
    result = daily_close(db, date.today())
    assert result.num_tickets == 0
    assert result.total_ventas == Decimal("0")
    assert result.desglose_pago.efectivo == Decimal("0")
    assert result.desglose_pago.tarjeta == Decimal("0")
    assert result.desglose_pago.bizum == Decimal("0")
    assert result.desglose_pago.otro == Decimal("0")


def test_daily_close_counts_todays_sales(db, admin_user):
    from datetime import date
    from app.services.report_service import daily_close
    prod = _make_product(db, precio="10.00", stock=100)
    _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 2)])   # 20.00
    _make_sale(db, admin_user.id, PaymentMethod.tarjeta, [(prod, 1)])    # 10.00
    result = daily_close(db, date.today())
    assert result.num_tickets == 2
    assert result.total_ventas == Decimal("30.00")


def test_daily_close_desglose_por_metodo_pago(db, admin_user):
    from datetime import date
    from app.services.report_service import daily_close
    prod = _make_product(db, precio="5.00", stock=100)
    _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 2)])   # 10.00
    _make_sale(db, admin_user.id, PaymentMethod.tarjeta, [(prod, 3)])    # 15.00
    _make_sale(db, admin_user.id, PaymentMethod.bizum, [(prod, 1)])      # 5.00
    result = daily_close(db, date.today())
    assert result.desglose_pago.efectivo == Decimal("10.00")
    assert result.desglose_pago.tarjeta == Decimal("15.00")
    assert result.desglose_pago.bizum == Decimal("5.00")
    assert result.desglose_pago.otro == Decimal("0")


def test_daily_close_excludes_other_days(db, admin_user):
    from datetime import date, datetime, timedelta, UTC
    from app.services.report_service import daily_close
    prod = _make_product(db, stock=100)
    sale = _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 1)])
    sale.fecha = datetime.now(UTC) - timedelta(days=1)
    db.commit()
    result = daily_close(db, date.today())
    assert result.num_tickets == 0
    assert result.total_ventas == Decimal("0")
