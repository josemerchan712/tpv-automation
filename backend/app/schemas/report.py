from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class PaymentBreakdown(BaseModel):
    efectivo: Decimal = Decimal("0")
    tarjeta: Decimal = Decimal("0")
    bizum: Decimal = Decimal("0")
    otro: Decimal = Decimal("0")


class DailyCloseOut(BaseModel):
    fecha: date
    total_ventas: Decimal
    num_tickets: int
    desglose_pago: PaymentBreakdown


class LowStockProductOut(BaseModel):
    id: int
    nombre: str
    stock: int
    stock_minimo: int

    model_config = {"from_attributes": True}


class TopProductOut(BaseModel):
    product_id: int
    nombre: str
    total_cantidad: int
    total_importe: Decimal
